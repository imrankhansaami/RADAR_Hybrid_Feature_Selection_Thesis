"""Spot-check key numbers before they go into the thesis."""
import json
import os

import numpy as np
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

from run_experiments import (ARM, DATA_DIR, FEATS, PRIMARY, SEED, balance,
                             compute_scores, evaluate_classical, load_dedup,
                             split_p1)

OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "results")

res = json.load(open(os.path.join(OUT, "classical_results.json")))
p1, p2 = res["primary_P1"], res["primary_P2"]
print("P1 positives: train %d test %d" % (p1["train_pos"], p1["test_pos"]))
print("P2 positives: train %d test %d" % (p2["train_pos"], p2["test_pos"]))
print("P2 view of the world: test prevalence %.3f"
      % (p2["test_pos"] / p2["n_test"]))

X, y, names, _ = load_dedup(os.path.join(DATA_DIR, PRIMARY))
tr, te = split_p1(y)
Xtr, ytr = X.iloc[tr].reset_index(drop=True), y[tr]
Xte, yte = X.iloc[te].reset_index(drop=True), y[te]
Xb, yb = balance(Xtr, ytr, ARM, SEED)
scaler = MinMaxScaler().fit(Xb)
Xb_s = pd.DataFrame(scaler.transform(Xb), columns=FEATS)
Xte_s = pd.DataFrame(scaler.transform(Xte), columns=FEATS)

r = evaluate_classical("XGB", Xb_s, yb, Xte_s, yte)
print("spot-check XGB all-features F1 = %.4f (stored %.4f)"
      % (r["f1"], p1["full"]["all|XGB"]["f1"]))

art = compute_scores(Xb_s, yb, SEED)
sens = json.load(open(os.path.join(OUT, "sensitivity.json")))
print("FS-A subset:      ", sorted(int(i) for i in art["fsa"]))
print("RFE k=10 subset:  ", sorted(sens["rfe10"]["subset"]))
print("theta=0.75 subset:", sorted(sens["theta75"]["subset"]))
