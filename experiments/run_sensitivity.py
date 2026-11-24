"""E8 sensitivity runs: Imbalanced-5, stricter vote threshold, RFE ablation,
and the alternative balancing arms.

Writes results/sensitivity.json.
"""
import json
import os
import time

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import f1_score
from sklearn.preprocessing import MinMaxScaler
from xgboost import XGBClassifier

from run_experiments import (ARM, DATA_DIR, MODELS, OUT_DIR, PRIMARY, SEED,
                             balance, compute_scores, load_dedup, make_model,
                             n_for, run_pipeline, split_p1)

SECONDARY = "dataset-imbalanced-5-engineered.csv"


def eval_subset(Xb_s, yb, Xte_s, yte, idx, model_name, seed=SEED,
                class_weight=None, scale_pos=None):
    model = make_model(model_name)
    if class_weight is not None:
        model.set_params(class_weight=class_weight)
    if scale_pos is not None and model_name == "XGB":
        model.set_params(scale_pos_weight=scale_pos)
    model.fit(Xb_s.iloc[:, idx], yb)
    pred = model.predict(Xte_s.iloc[:, idx])
    return float(f1_score(yte, pred, pos_label=1, zero_division=0))


def main(smoke=False):
    t0 = time.time()
    out = {}
    X, y, names, _ = load_dedup(os.path.join(DATA_DIR, PRIMARY))
    if smoke:
        keep = np.concatenate([np.where(y == 0)[0][:1000], np.where(y == 1)[0][:1000]])
        X, y = X.iloc[keep].reset_index(drop=True), y[keep]

    tr, te = split_p1(y)
    Xtr, ytr = X.iloc[tr].reset_index(drop=True), y[tr]
    Xte, yte = X.iloc[te].reset_index(drop=True), y[te]
    Xb, yb = balance(Xtr, ytr, "under", SEED)
    scaler = MinMaxScaler().fit(Xb)
    Xb_s = pd.DataFrame(scaler.transform(Xb), columns=X.columns)
    Xte_s = pd.DataFrame(scaler.transform(Xte), columns=X.columns)
    d = Xb_s.shape[1]

    # --- theta = 0.75 -------------------------------------------------------
    art = compute_scores(Xb_s, yb, SEED)
    fsa50 = art["fsa"]
    fsa75 = np.where(art["ratio"] >= 0.75)[0]
    if len(fsa75) == 0:
        fsa75 = np.arange(d)
    out["theta75"] = {"subset_size": int(len(fsa75)),
                      "subset": [int(i) for i in fsa75],
                      "f1": {m: eval_subset(Xb_s, yb, Xte_s, yte, fsa75, m)
                             for m in MODELS}}

    # --- RFE ablation (k = 10 instead of 11) --------------------------------
    art10 = compute_scores(Xb_s, yb, SEED, rfe_k=10)
    fsa10 = art10["fsa"]
    out["rfe10"] = {"subset_size": int(len(fsa10)),
                    "subset": [int(i) for i in fsa10],
                    "f1": {m: eval_subset(Xb_s, yb, Xte_s, yte, fsa10, m)
                           for m in MODELS}}

    # --- balancing arms on the FS-C best subset -----------------------------
    res = json.load(open(os.path.join(OUT_DIR, "classical_results.json")))
    cc = res["primary_P1"]["FS-C"]["chosen_p"]
    idx_c = art["order_c"][:n_for(cc, d)]
    n_pos = int((ytr == 1).sum())
    n_neg = int((ytr == 0).sum())
    spw = n_neg / max(1, n_pos)
    arms = {}
    for m in ["RF", "XGB"]:
        arms[m] = {}
        # class weights, no resampling (training set stays imbalanced)
        arms[m]["class_weights"] = eval_subset(
            pd.DataFrame(scaler.transform(Xtr), columns=X.columns), ytr,
            Xte_s, yte, idx_c, m, class_weight="balanced", scale_pos=spw)
        # undersampling (the main arm)
        arms[m]["undersampling"] = eval_subset(Xb_s, yb, Xte_s, yte, idx_c, m)
        # bidirectional resampling towards the median class size
        Xbi, ybi = balance(Xtr, ytr, "bidir", SEED)
        Xbi_s = pd.DataFrame(scaler.transform(Xbi), columns=X.columns)
        arms[m]["bidirectional"] = eval_subset(Xbi_s, ybi, Xte_s, yte, idx_c, m)
    out["balancing_arms"] = arms
    out["balancing_arms_note"] = "class weights use class_weight='balanced' " \
        "(RF) / scale_pos_weight (XGB) without resampling"

    # --- Imbalanced-5 -------------------------------------------------------
    if not smoke:
        p5 = run_pipeline(os.path.join(DATA_DIR, SECONDARY), "P1")
        full = p5["full"]
        bm = p5["best_model"]
        cb5, cc5 = p5["FS-B"]["chosen_p"], p5["FS-C"]["chosen_p"]
        out["imbalanced5"] = {
            "n_train": p5["n_train"], "n_test": p5["n_test"],
            "fsa_size": len(p5["fsa"]),
            "chosen_p_FSB": cb5, "chosen_p_FSC": cc5,
            "best_model_all": bm["all"],
            "f1_all": full["all|%s" % bm["all"]]["f1"],
            "f1_fsa": full["FS-A|%s" % bm["FS-A"]]["f1"],
            "f1_fsb": full["FS-B:%d|%s" % (cb5, bm["FS-B"])]["f1"],
            "f1_fsc": full["FS-C:%d|%s" % (cc5, bm["FS-C"])]["f1"]}

    out["runtime_s"] = round(time.time() - t0, 1)
    with open(os.path.join(OUT_DIR, "sensitivity.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print("saved sensitivity.json in %.1f s" % (time.time() - t0))


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()
    main(smoke=args.smoke)
