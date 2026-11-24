"""E7 companion: compact A2G-PTH on the chronological Drift split.

Runs after run_drift.py (the subsets and the split are taken from
results/drift_results.json).  Two inputs (all features, best FS-B subset) and
both graph variants, compact architecture only, because the faithful
architecture variant is already reported for the primary file and the tail
carries only ~45 positive rows.  A stratified 20 % slice of the balanced
training part is the validation set, exactly as in run_a2g.py.

Writes results/drift_a2g_results.json.
"""
import json
import os
import time

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import MinMaxScaler

from run_experiments import ARM, DATA_DIR, OUT_DIR, SEED, balance, load_dedup

from run_a2g import A2G, AnomalyAE, EPOCHS, PATIENCE, best_threshold, eval_metrics, threshold_f1

DRIFT = "dataset-drift-engineered.csv"


def main():
    t0 = time.time()
    dr = json.load(open(os.path.join(OUT_DIR, "drift_results.json"), encoding="utf-8"))

    X, y, names, _ = load_dedup(os.path.join(DATA_DIR, DRIFT))
    n = len(y)
    cut = int(round(0.8 * n))
    Xtr, ytr = X.iloc[:cut].reset_index(drop=True), y[:cut]
    Xte, yte = X.iloc[cut:].reset_index(drop=True), y[cut:]

    Xb, yb = balance(Xtr, ytr, ARM, SEED)
    scaler = MinMaxScaler().fit(Xb)
    Xb_s = scaler.transform(Xb)
    Xte_s = scaler.transform(Xte)

    itr, iva = train_test_split(np.arange(len(Xb_s)), test_size=0.2, stratify=yb,
                                random_state=SEED)
    Xa, ya = Xb_s[itr], yb[itr]
    Xv, yv = Xb_s[iva], yb[iva]

    subsets = {"All 21": np.array(dr["subsets"]["all"]),
               "FS-A": np.array(dr["subsets"]["FS-A"])}

    out = {"configs": {}, "anomaly": {}, "subset_sizes": {}, "runtime_s": None}
    for sname, idx in subsets.items():
        d = len(idx)
        out["subset_sizes"][sname] = int(d)
        for mode in ["faithful", "message"]:
            key = "%s|compact|%s" % (sname, mode)
            print("== %s (d=%d) ==" % (key, d), flush=True)
            t1 = time.time()
            model = A2G(d, "compact", mode == "message")
            val_f1 = model.fit(Xa[:, idx], ya, Xv[:, idx], yv,
                               epochs=EPOCHS, patience=PATIENCE)
            train_s = time.time() - t1
            t1 = time.time()
            proba = model._proba(Xte_s[:, idx])
            pred_ms = (time.time() - t1) * 1000.0
            m = eval_metrics(yte, proba)
            m.update({"train_s": train_s, "pred_ms": pred_ms,
                      "size_kb": model.param_kb(), "val_f1": float(val_f1)})
            out["configs"][key] = m
            print("   F1=%.4f val=%.4f train=%.1fs" % (m["f1"], m["val_f1"], train_s),
                  flush=True)

    for sname, idx in subsets.items():
        print("== anomaly detector: %s ==" % sname, flush=True)
        gw = ya == 0
        t1 = time.time()
        ae = AnomalyAE(len(idx))
        ae.fit(Xa[gw][:, idx], epochs=30)
        err_tr = ae.recon(Xa[gw][:, idx])
        err_val = ae.recon(Xv[:, idx])
        err_te = ae.recon(Xte_s[:, idx])
        thr = best_threshold(yv, err_val)
        out["anomaly"][sname] = {
            "threshold": float(thr),
            "f1_at_chosen": float(threshold_f1(yte, err_te, thr)),
            "f1_at_0.1": float(threshold_f1(yte, err_te, 0.1)),
            "train_s": time.time() - t1,
            "mean_err_goodware": float(np.mean(err_tr))}
        print("   thr=%.4f F1(chosen)=%.4f" % (thr, out["anomaly"][sname]["f1_at_chosen"]),
              flush=True)

    out["runtime_s"] = round(time.time() - t0, 1)
    with open(os.path.join(OUT_DIR, "drift_a2g_results.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print("saved drift_a2g_results.json in %.1f s" % (time.time() - t0))


if __name__ == "__main__":
    main()
