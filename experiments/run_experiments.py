"""Classical experiments for the RADAR hybrid feature-selection thesis.

Produces every number needed by Tables 7, 9, 10, 11, 12, 13 and the classical
rows of Table 15 (Chapter 4 of the thesis document), plus the E8 sensitivity
figures.  Deterministic; no number is typed in by hand.

Pipeline (matching Section 4.1 of the thesis):
  dedup on 21 features + label -> split (P1 stratified / P2 group) ->
  balance training only (main arm: random undersampling to the minority size,
  as in [1]) -> Min-Max scaling fitted on the balanced training set ->
  scores (MI, ANOVA F, chi-square, RFE, |Pearson|) on training only ->
  FS-A (voting ratio >= 0.5), FS-B (combined-score sweep),
  FS-C (vote-ranked sweep) -> 5-fold inner CV with everything refitted per
  fold to choose the retained percentage by the one-standard-error rule ->
  train the 7 classical models -> evaluate once on the untouched test set.

Usage:
  python run_experiments.py            # full run (~10-20 min)
  python run_experiments.py --smoke    # tiny run to validate the code
"""
import argparse
import json
import os
import pickle
import platform
import sys
import time
import warnings
from math import floor, sqrt

warnings.filterwarnings("ignore")

import numpy as np
import pandas as pd
from scipy.stats import spearmanr
from sklearn.ensemble import AdaBoostClassifier, RandomForestClassifier
from sklearn.feature_selection import RFE, chi2, f_classif, mutual_info_classif
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (accuracy_score, average_precision_score,
                             f1_score, fbeta_score, precision_score,
                             recall_score, roc_auc_score)
from sklearn.model_selection import (StratifiedGroupKFold, StratifiedKFold,
                                     train_test_split)
from sklearn.naive_bayes import GaussianNB
from sklearn.neighbors import KNeighborsClassifier
from sklearn.preprocessing import MinMaxScaler
from sklearn.tree import DecisionTreeClassifier
from xgboost import XGBClassifier

HERE = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(HERE, "..", "data", "engineered")
OUT_DIR = os.path.join(HERE, "..", "results")

FEATS = ['File_Delete_archived', 'File_created', 'File_creation_time_changed',
         'Pipe_Created', 'Process_Create', 'Registry_value_set',
         'process-related', 'file-related', 'network-related', 'driver-related',
         'registry-related', 'suspicious_path', 'system_executable', 'path_length',
         'directory_depth', 'process_vs_parent_freq_ratio', 'process_name_length',
         'executable_depth_diff', 'parent_is_system_executable',
         'extension_similarity', 'file_name_entropy']
MODELS = ["LR", "KNN", "NB", "DT", "RF", "XGB", "AB"]
MODEL_LABELS = {"LR": "Logistic regression", "KNN": "KNN (k = 5)",
                "NB": "Naive Bayes", "DT": "Decision tree",
                "RF": "Random forest", "XGB": "XGBoost", "AB": "AdaBoost"}
PCTS = list(range(10, 101, 10))
SEEDS = [42, 7, 13, 21, 99]
SEED = 42
N_SPLITS = 5
ARM = "under"               # main balancing arm: random undersampling ([1])
PRIMARY = "dataset-imbalanced-10-engineered.csv"
SECONDARY = "dataset-imbalanced-5-engineered.csv"


def n_for(p, d):
    return max(1, int(floor(d * p / 100.0)))


def load_dedup(path):
    df = pd.read_csv(path)
    df = df.drop_duplicates(subset=FEATS + ["target-class"])
    X = df[FEATS].reset_index(drop=True)
    y = df["target-class"].to_numpy(dtype=int)
    name_col = "target-class-name" if "target-class-name" in df.columns else "target"
    names = df[name_col].astype(str).to_numpy()
    return X, y, names, df


def split_p1(y, seed=SEED, test_size=0.2):
    idx = np.arange(len(y))
    tr, te = train_test_split(idx, test_size=test_size, stratify=y,
                              random_state=seed)
    return tr, te


def split_p2(y, names, seed=SEED, train_frac=0.8):
    """Group split: no ransomware sample on both sides, test ~= 20 % of the
    ransomware rows; goodware (a single stream) is split randomly."""
    rng = np.random.default_rng(seed)
    n = len(y)
    tr_mask = np.zeros(n, dtype=bool)
    r_idx = np.where(y == 1)[0]
    g = names[r_idx]
    uniq, inv, counts = np.unique(g, return_inverse=True, return_counts=True)
    target = (1.0 - train_frac) * counts.sum()
    order = rng.permutation(len(uniq))
    test_names = []
    test_rows = 0
    for i in order:
        c = counts[i]
        if test_rows + c <= target:
            test_names.append(uniq[i])
            test_rows += c
    tr_mask[r_idx] = ~np.isin(g, test_names)
    g_idx = np.where(y == 0)[0]
    g_idx = rng.permutation(g_idx)
    tr_mask[g_idx[:int(round(train_frac * len(g_idx)))]] = True
    tr = np.where(tr_mask)[0]
    te = np.where(~tr_mask)[0]
    return tr, te


def cv_groups(y, names):
    return np.array([names[i] if y[i] == 1 else "gw_%d" % i
                     for i in range(len(y))], dtype=object)


def balance(X, y, arm=ARM, seed=SEED):
    if arm == "none":
        return X, y
    rng = np.random.default_rng(seed)
    idx1 = np.where(y == 1)[0]
    idx0 = np.where(y == 0)[0]
    if arm == "under":
        m = min(len(idx0), len(idx1))
        keep0 = rng.choice(idx0, m, replace=False)
        keep1 = rng.choice(idx1, m, replace=False)
    elif arm == "bidir":
        target = int(round((len(idx0) + len(idx1)) / 2.0))
        keep0 = rng.choice(idx0, target, replace=(len(idx0) < target))
        keep1 = rng.choice(idx1, target, replace=(len(idx1) < target))
    else:
        raise ValueError("unknown arm " + arm)
    keep = np.concatenate([keep0, keep1])
    rng.shuffle(keep)
    return X.iloc[keep].reset_index(drop=True), y[keep]


def compute_scores(Xs, y, seed=SEED, rfe_k=None):
    """Score features on the (already scaled) training data."""
    Xv = Xs.to_numpy(dtype=float)
    d = Xv.shape[1]
    mi = mutual_info_classif(Xv, y, random_state=seed)
    F = np.nan_to_num(f_classif(Xv, y)[0])
    chi = np.nan_to_num(chi2(np.clip(Xv, 0, None), y)[0])
    k = rfe_k if rfe_k else (d + 1) // 2
    rfe = RFE(LogisticRegression(max_iter=5000),
              n_features_to_select=max(1, min(k, d)), step=1).fit(Xv, y)
    corr = np.nan_to_num(np.array([abs(np.corrcoef(Xv[:, j], y)[0, 1])
                                   for j in range(d)]))

    def norm(v):
        lo, hi = float(np.min(v)), float(np.max(v))
        return (v - lo) / (hi - lo) if hi > lo else np.zeros_like(v)

    combined = (norm(mi) + norm(F) + norm(chi)) / 3.0
    votes = ((mi > mi.mean()).astype(int) + (F > F.mean()).astype(int)
             + (rfe.ranking_ == 1).astype(int) + (corr > corr.mean()).astype(int))
    ratio = votes / 4.0
    fsa = np.where(ratio >= 0.5)[0]
    if len(fsa) == 0:
        fsa = np.arange(d)
    order_b = np.argsort(-combined, kind="stable")
    order_c = np.lexsort((-combined, -votes))
    return {"mi": mi, "F": F, "chi": chi, "rfe_rank": rfe.ranking_,
            "corr": corr, "combined": combined, "votes": votes,
            "ratio": ratio, "fsa": fsa, "order_b": order_b, "order_c": order_c}


def make_model(name):
    if name == "LR":
        return LogisticRegression(max_iter=5000, random_state=SEED)
    if name == "KNN":
        return KNeighborsClassifier(n_neighbors=5)
    if name == "NB":
        return GaussianNB()
    if name == "DT":
        return DecisionTreeClassifier(random_state=SEED)
    if name == "RF":
        return RandomForestClassifier(n_estimators=100, random_state=SEED, n_jobs=-1)
    if name == "XGB":
        return XGBClassifier(n_estimators=50, max_depth=3, learning_rate=0.1,
                             reg_lambda=0, gamma=0, eval_metric="logloss",
                             random_state=SEED, n_jobs=-1)
    if name == "AB":
        return AdaBoostClassifier(n_estimators=50, random_state=SEED)
    raise KeyError(name)


def metrics(y_true, pred, proba):
    out = {
        "accuracy": float(accuracy_score(y_true, pred)),
        "precision": float(precision_score(y_true, pred, pos_label=1, zero_division=0)),
        "recall": float(recall_score(y_true, pred, pos_label=1, zero_division=0)),
        "f1": float(f1_score(y_true, pred, pos_label=1, zero_division=0)),
        "f2": float(fbeta_score(y_true, pred, beta=2, pos_label=1, zero_division=0)),
    }
    if proba is not None and len(np.unique(y_true)) > 1:
        out["roc_auc"] = float(roc_auc_score(y_true, proba))
        out["pr_auc"] = float(average_precision_score(y_true, proba))
    else:
        out["roc_auc"] = float("nan")
        out["pr_auc"] = float("nan")
    return out


def evaluate_classical(name, Xtr, ytr, Xte, yte):
    model = make_model(name)
    t0 = time.perf_counter()
    model.fit(Xtr, ytr)
    fit_s = time.perf_counter() - t0
    t0 = time.perf_counter()
    pred = model.predict(Xte)
    for _ in range(2):
        model.predict(Xte)
    pred_ms = (time.perf_counter() - t0) / 3.0 * 1000.0
    proba = model.predict_proba(Xte)[:, 1] if hasattr(model, "predict_proba") else None
    r = metrics(yte, pred, proba)
    r["fit_s"] = fit_s
    r["pred_ms"] = pred_ms
    r["size_kb"] = len(pickle.dumps(model)) / 1024.0
    return r


def compile_stats():
    import sklearn
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "processor": platform.processor(),
        "numpy": np.__version__, "pandas": pd.__version__,
        "sklearn": sklearn.__version__,
        "xgboost": __import__("xgboost").__version__,
        "time": time.strftime("%Y-%m-%d %H:%M:%S"),
    }


def configs_from_scores(art):
    d = len(art["votes"])
    cfg = {"all": np.arange(d), "FS-A": art["fsa"]}
    for p in PCTS:
        cfg["FS-B:%d" % p] = art["order_b"][:n_for(p, d)]
        cfg["FS-C:%d" % p] = art["order_c"][:n_for(p, d)]
    return cfg


def cv_run(Xtr, ytr, groups, protocol, seed, smoke=False):
    """5-fold inner CV; everything (balance, scale, scores, models) refit."""
    Xtr = Xtr.reset_index(drop=True)
    if protocol == "P1":
        splitter = StratifiedKFold(n_splits=N_SPLITS, shuffle=True, random_state=seed)
        folds = list(splitter.split(Xtr, ytr))
    else:
        splitter = StratifiedGroupKFold(n_splits=N_SPLITS, shuffle=True,
                                        random_state=seed)
        folds = list(splitter.split(Xtr, ytr, groups))
    f1 = {}
    subsets = {}
    models = ["LR", "RF"] if smoke else MODELS
    for fold, (ftr, fva) in enumerate(folds):
        Xf, yf = Xtr.iloc[ftr], ytr[ftr]
        Xb, yb = balance(Xf, yf, ARM, seed + fold)
        scaler = MinMaxScaler().fit(Xb)
        Xb_s = pd.DataFrame(scaler.transform(Xb), columns=FEATS)
        Xva_s = pd.DataFrame(scaler.transform(Xtr.iloc[fva]), columns=FEATS)
        yva = ytr[fva]
        art = compute_scores(Xb_s, yb, seed)
        cfg = configs_from_scores(art)
        for cname, idx in cfg.items():
            for m in models:
                r = evaluate_classical(m, Xb_s.iloc[:, idx], yb,
                                       Xva_s.iloc[:, idx], yva)
                f1.setdefault((cname, m), []).append(r["f1"])
        subsets[fold] = {"FS-A": art["fsa"]}
        for p in PCTS:
            subsets[fold]["FS-B:%d" % p] = cfg["FS-B:%d" % p]
            subsets[fold]["FS-C:%d" % p] = cfg["FS-C:%d" % p]
    return f1, subsets


def choose_p(cv_f1, sel):
    """One-standard-error rule on the best validation model per percentage."""
    curve = {}
    for p in PCTS:
        cname = "%s:%d" % (sel, p)
        means = {m: float(np.mean(cv_f1[(cname, m)])) for m in MODELS
                 if (cname, m) in cv_f1}
        bm = max(means, key=means.get)
        vals = np.array(cv_f1[(cname, bm)])
        curve[p] = {"val": means[bm], "model": bm,
                    "se": float(vals.std(ddof=1) / sqrt(len(vals)))}
    best_p = max(curve, key=lambda p: curve[p]["val"])
    thresh = curve[best_p]["val"] - curve[best_p]["se"]
    chosen = min(p for p in PCTS if curve[p]["val"] >= thresh)
    return chosen, curve


def best_model_for(cv_f1, cname):
    means = {m: float(np.mean(cv_f1[(cname, m)])) for m in MODELS
             if (cname, m) in cv_f1}
    return max(means, key=means.get)


def jaccard(a, b):
    a, b = set(np.asarray(a).tolist()), set(np.asarray(b).tolist())
    return len(a & b) / max(1, len(a | b))


def stability_from_subsets(fold_subsets, key):
    sets = [fold_subsets[f][key] for f in sorted(fold_subsets)]
    js = [jaccard(sets[i], sets[j])
          for i in range(len(sets)) for j in range(i + 1, len(sets))]
    return float(np.mean(js)), float(np.min(js))


def run_pipeline(path, protocol, smoke=False):
    X, y, names, _ = load_dedup(path)
    if smoke:
        keep = np.concatenate([np.where(y == 0)[0][:1500], np.where(y == 1)[0][:1500]])
        X, y, names = X.iloc[keep].reset_index(drop=True), y[keep], names[keep]
    tr, te = (split_p1(y) if protocol == "P1" else split_p2(y, names))
    Xtr, ytr = X.iloc[tr].reset_index(drop=True), y[tr]
    Xte, yte = X.iloc[te].reset_index(drop=True), y[te]
    Xb, yb = balance(Xtr, ytr, ARM, SEED)
    scaler = MinMaxScaler().fit(Xb)
    Xb_s = pd.DataFrame(scaler.transform(Xb), columns=FEATS)
    Xte_s = pd.DataFrame(scaler.transform(Xte), columns=FEATS)
    art = compute_scores(Xb_s, yb, SEED)
    cfg = configs_from_scores(art)
    if smoke:
        cfg = {k: v for k, v in cfg.items() if k in ("all", "FS-A", "FS-B:50", "FS-C:50")}

    print("  full-train fits:", len(cfg), "configs x", len(MODELS), "models")
    full = {}
    for cname, idx in cfg.items():
        for m in MODELS:
            full[(cname, m)] = evaluate_classical(
                m, Xb_s.iloc[:, idx], yb, Xte_s.iloc[:, idx], yte)

    groups = cv_groups(ytr, names[tr])
    print("  inner CV ...")
    cv_f1, fold_subsets = cv_run(Xtr, ytr, groups, protocol, SEED, smoke=smoke)

    result = {
        "protocol": protocol, "file": os.path.basename(path), "arm": ARM,
        "n_train": int(len(tr)), "n_test": int(len(te)),
        "n_train_balanced": int(len(yb)),
        "train_pos": int((ytr == 1).sum()), "test_pos": int((yte == 1).sum()),
        "scores": {k: np.asarray(art[k]).tolist() for k in
                   ["mi", "F", "chi", "rfe_rank", "corr", "combined", "votes", "ratio"]},
        "fsa": art["fsa"].tolist(),
        "full": {"%s|%s" % k: v for k, v in full.items()},
        "cv_f1": {"%s|%s" % k: v for k, v in cv_f1.items()},
    }
    for sel in ["FS-B", "FS-C"]:
        chosen, curve = choose_p(cv_f1, sel)
        result[sel] = {"chosen_p": chosen, "curve": {str(k): v for k, v in curve.items()}}
    result["best_model"] = {
        "all": best_model_for(cv_f1, "all"),
        "FS-A": best_model_for(cv_f1, "FS-A"),
    }
    for sel in ["FS-B", "FS-C"]:
        cname = "%s:%d" % (sel, result[sel]["chosen_p"])
        result["best_model"][sel] = best_model_for(cv_f1, cname)
    result["fold_subsets"] = {int(f): {k: v.tolist() for k, v in d.items()}
                              for f, d in fold_subsets.items()}
    return result


def seed_stability(X, y, names, sel_p):
    sets = {"FS-A": [], "FS-B": [], "FS-C": []}
    for seed in SEEDS:
        tr, _ = split_p1(y, seed=seed)
        Xb, yb = balance(X.iloc[tr].reset_index(drop=True), y[tr], ARM, seed)
        scaler = MinMaxScaler().fit(Xb)
        Xs = pd.DataFrame(scaler.transform(Xb), columns=FEATS)
        art = compute_scores(Xs, yb, seed)
        d = len(art["votes"])
        sets["FS-A"].append(art["fsa"])
        sets["FS-B"].append(art["order_b"][:n_for(sel_p["FS-B"], d)])
        sets["FS-C"].append(art["order_c"][:n_for(sel_p["FS-C"], d)])
    out = {}
    for k, ss in sets.items():
        js = [jaccard(ss[i], ss[j]) for i in range(len(ss)) for j in range(i + 1, len(ss))]
        out[k] = float(np.mean(js))
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()
    os.makedirs(OUT_DIR, exist_ok=True)
    t0 = time.time()

    print("== primary file, P1 ==")
    p1 = run_pipeline(os.path.join(DATA_DIR, PRIMARY), "P1", smoke=args.smoke)

    print("== primary file, P2 ==")
    p2 = run_pipeline(os.path.join(DATA_DIR, PRIMARY), "P2", smoke=args.smoke)

    X, y, names, _ = load_dedup(os.path.join(DATA_DIR, PRIMARY))
    print("== seed stability ==")
    sel_p = {"FS-B": p1["FS-B"]["chosen_p"], "FS-C": p1["FS-C"]["chosen_p"]}
    seed_jac = seed_stability(X, y, names, sel_p)

    out = {"env": compile_stats(), "primary_P1": p1, "primary_P2": p2,
           "seed_jaccard": seed_jac,
           "runtime_s": round(time.time() - t0, 1)}
    with open(os.path.join(OUT_DIR, "classical_results.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print("saved classical_results.json in %.1f s" % (time.time() - t0))


if __name__ == "__main__":
    main()
