"""Re-run the P2 protocol (fixed group split) and patch classical_results.json."""
import json
import os
import sys

BASE = (r"C:\Users\imran\Documents\thesis research\Hybrid Voting and "
        r"Percentage-Sweep Feature Selection for Ransomware Detection from Sysmon Events")
sys.path.insert(0, os.path.join(BASE, "experiments"))

import run_experiments as rx

p2 = rx.run_pipeline(os.path.join(rx.DATA_DIR, rx.PRIMARY), "P2")
js = os.path.join(rx.OUT_DIR, "classical_results.json")
res = json.load(open(js))
res["primary_P2"] = p2
with open(js, "w", encoding="utf-8") as fh:
    json.dump(res, fh, indent=1)
print("patched primary_P2: train_pos", p2["train_pos"], "test_pos", p2["test_pos"])
