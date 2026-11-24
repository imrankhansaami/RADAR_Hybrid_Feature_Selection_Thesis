"""Seed repeats and pairwise significance for the key configurations.

Produces results/statistics.json:
  - mean and standard deviation of the test F1 over seeds [42, 7, 13, 21, 99]
    for the four key configurations (all, FS-A, FS-B best, FS-C best) x 7 models
    (the thesis text promises "repeated over seeds with mean and standard
    deviation recorded");
  - McNemar exact tests and paired-bootstrap 95% CIs for the F1 difference
    between the subsets under one fixed model family (XGBoost), so the
    comparison isolates the subset effect.
"""
import json
import os
import time

import numpy as np
import pandas as pd
from scipy.stats import binomtest
from sklearn.ensemble import AdaBoostClassifier, RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import f1_score
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import MinMaxScaler
from sklearn.tree import DecisionTreeClassifier
from xgboost import XGBClassifier

from run_experiments import (ARM, DATA_DIR, MODELS, OUT_DIR, PRIMARY, SEED,
                             balance, compute_scores, load_dedup, n_for,
                             split_p1)

SEEDS = [42, 7, 13, 21, 99]


def make_model(name, seed):
    if name == "LR":
        return LogisticRegression(max_iter=5000)
    if name == "KNN":
        return KNeighborsClassifier(n_neighbors=5)
    if name == "NB":
        return GaussianNB()
    if name == "DT":
        return DecisionTreeClassifier(random_state=seed)
    if name == "RF":
        return RandomForestClassifier(n_estimators=100, random_state=seed, n_jobs=-1)
    if name == "XGB":
        return XGBClassifier(n_estimators=50, max_depth=3, learning_rate=0.1,
                             reg_lambda=0, gamma=0, eval_metric="logloss",
                             random_state=seed, n_jobs=-1)
    if name == "AB":
        return AdaBoostClassifier(n_estimators=50, random_state=seed)
    raise KeyError(name)


def main():
    t0 = time.time()
    res = json.load(open(os.path.join(OUT_DIR, "classical_results.json")))
    p1 = res["primary_P1"]
    cb, cc = p1["FS-B"]["chosen_p"], p1["FS-C"]["chosen_p"]

    X, y, names, _ = load_dedup(os.path.join(DATA_DIR, PRIMARY))
    rows = []
    preds = {}  # (seed, cfg) -> (pred, yte) for the significance tests
    for seed in SEEDS:
        tr, te = split_p1(y, seed=seed)
        Xtr, ytr = X.iloc[tr].reset_index(drop=True), y[tr]
        Xte, yte = X.iloc[te].reset_index(drop=True), y[te]
        Xb, yb = balance(Xtr, ytr, ARM, seed)
        scaler = MinMaxScaler().fit(Xb)
        Xb_s = pd.DataFrame(scaler.transform(Xb), columns=X.columns)
        Xte_s = pd.DataFrame(scaler.transform(Xte), columns=X.columns)
        art = compute_scores(Xb_s, yb, seed)
        d = len(art["votes"])
        cfgs = {"all": np.arange(d), "FS-A": art["fsa"],
                "FS-B:%d" % cb: art["order_b"][:n_for(cb, d)],
                "FS-C:%d" % cc: art["order_c"][:n_for(cc, d)]}
        for cfg, idx in cfgs.items():
            for m in MODELS:
                model = make_model(m, seed)
                model.fit(Xb_s.iloc[:, idx], yb)
                pred = model.predict(Xte_s.iloc[:, idx])
                f1 = float(f1_score(yte, pred, pos_label=1, zero_division=0))
                rows.append({"seed": seed, "config": cfg, "model": m, "f1": f1})
                if m == "XGB":
                    preds[(seed, cfg)] = (pred, yte)
        print("seed", seed, "done", flush=True)

    df = pd.DataFrame(rows)
    summary = {}
    for cfg in df["config"].unique():
        for m in MODELS:
            vals = df[(df["config"] == cfg) & (df["model"] == m)]["f1"]
            summary["%s|%s" % (cfg, m)] = {
                "mean": float(vals.mean()), "std": float(vals.std(ddof=1)),
                "n": int(len(vals))}

    # --- significance between subsets under the fixed XGBoost family -------
    names_map = {"all": "All 21", "FS-A": "FS-A",
                 "FS-B:%d" % cb: "FS-B best", "FS-C:%d" % cc: "FS-C best"}
    keys = list(names_map)
    sig = {}
    rng = np.random.default_rng(SEED)
    for i, a in enumerate(keys):
        for b in keys[i + 1:]:
            pa, ya = preds[(SEED, a)]
            pb, yb_ = preds[(SEED, b)]
            both_wrong = int(((pa != ya) & (pb != yb_)).sum())
            a_right_b_wrong = int(((pa == ya) & (pb != yb_)).sum())
            b_right_a_wrong = int(((pb == yb_) & (pa != ya)).sum())
            n = a_right_b_wrong + b_right_a_wrong
            pval = float(binomtest(a_right_b_wrong, n, 0.5).pvalue) if n else float("nan")
            # paired bootstrap of the F1 difference
            diffs = []
            for _ in range(2000):
                idx = rng.integers(0, len(ya), len(ya))
                f1a = f1_score(ya[idx], pa[idx], pos_label=1, zero_division=0)
                f1b = f1_score(ya[idx], pb[idx], pos_label=1, zero_division=0)
                diffs.append(f1a - f1b)
            lo, hi = np.percentile(diffs, [2.5, 97.5])
            sig["%s vs %s" % (names_map[a], names_map[b])] = {
                "mcnemar_p": pval,
                "delta_f1": float(f1_score(ya, pa, pos_label=1, zero_division=0)
                                  - f1_score(ya, pb, pos_label=1, zero_division=0)),
                "ci95": [float(lo), float(hi)],
                "discordant": n}

    out = {"seeds": SEEDS, "summary": summary, "significance_xgb": sig,
           "runtime_s": round(time.time() - t0, 1)}
    with open(os.path.join(OUT_DIR, "statistics.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print("saved statistics.json in %.1f s" % (time.time() - t0))


if __name__ == "__main__":
    main()
