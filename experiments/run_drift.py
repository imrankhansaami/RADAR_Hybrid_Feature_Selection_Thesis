"""E7: drift robustness on a chronological split of the Drift stream.

The Drift engineered file keeps the stream order (abrupt and gradual drift
phases), but the phase-boundary files are not part of the processed data, so
the split is chronological: the first 80 % of the stream trains, the last 20 %
is the test tail.  Everything else follows the pipeline of run_experiments --
balancing and scaling on the training part only, retained percentages and the
model per configuration chosen by grouped cross-validation inside the training
part (groups = ransomware family, so no family is split across folds).

Writes results/drift_results.json.
"""
import json
import os
import time

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

from run_experiments import (ARM, DATA_DIR, OUT_DIR, SEED, balance, best_model_for,
                             choose_p, compute_scores, configs_from_scores,
                             cv_groups, cv_run, evaluate_classical, load_dedup,
                             n_for)

DRIFT = "dataset-drift-engineered.csv"


def main():
    t0 = time.time()
    X, y, names, _ = load_dedup(os.path.join(DATA_DIR, DRIFT))
    n = len(y)
    cut = int(round(0.8 * n))
    Xtr, ytr = X.iloc[:cut].reset_index(drop=True), y[:cut]
    Xte, yte = X.iloc[cut:].reset_index(drop=True), y[cut:]
    print("chronological split: train %d test %d (test prevalence %.3f)"
          % (len(ytr), len(yte), yte.mean()))

    Xb, yb = balance(Xtr, ytr, ARM, SEED)
    scaler = MinMaxScaler().fit(Xb)
    Xb_s = pd.DataFrame(scaler.transform(Xb), columns=X.columns)
    Xte_s = pd.DataFrame(scaler.transform(Xte), columns=X.columns)
    art = compute_scores(Xb_s, yb, SEED)
    d = len(art["votes"])

    print("  inner grouped CV ...")
    groups = cv_groups(ytr, names[:cut])
    cv_f1, _ = cv_run(Xtr, ytr, groups, "P2", SEED)

    chosen = {}
    cfgs = {"all": np.arange(d), "FS-A": art["fsa"]}
    bm = {"all": best_model_for(cv_f1, "all"), "FS-A": best_model_for(cv_f1, "FS-A")}
    for sel, order in [("FS-B", art["order_b"]), ("FS-C", art["order_c"])]:
        c, curve = choose_p(cv_f1, sel)
        chosen[sel] = {"chosen_p": c, "curve": {str(k): v for k, v in curve.items()}}
        cfgs[sel] = order[:n_for(c, d)]
        bm[sel] = best_model_for(cv_f1, "%s:%d" % (sel, c))

    full = {}
    for cname, idx in cfgs.items():
        full[cname] = evaluate_classical(bm[cname], Xb_s.iloc[:, idx], yb,
                                         Xte_s.iloc[:, idx], yte)

    out = {"file": DRIFT, "n_train": int(len(ytr)), "n_test": int(len(yte)),
           "test_pos": int((yte == 1).sum()),
           "test_prevalence": float(yte.mean()),
           "fsa_size": int(len(art["fsa"])), "chosen": chosen,
           "best_model": bm,
           "f1": {c: full[c]["f1"] for c in cfgs},
           "full": full,
           "subsets": {c: [int(i) for i in idx] for c, idx in cfgs.items()},
           "runtime_s": round(time.time() - t0, 1)}
    with open(os.path.join(OUT_DIR, "drift_results.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print("drift F1:", {c: round(out["f1"][c], 4) for c in cfgs})
    print("chosen p:", {k: v["chosen_p"] for k, v in chosen.items()})
    print("models:", bm)
    print("saved drift_results.json in %.1f s" % (time.time() - t0))


if __name__ == "__main__":
    main()
