"""A2G-PTH deep evaluator runs (E5, Table 14) + the deep row of Table 15.

Implements the adversarial autoencoder + graph classifier of [2] as adapted in
the thesis plan:
  - architecture variants: the faithful configuration as written (512/256/128
    encoder with attention, 64-d latent) and a compact variant with smaller
    widths (the number of input features here is at most 21);
  - graph variants: the as-written equations (W applied to the latent vector
    only, adjacency unused -> "faithful graph") and the message-passing variant
    H' = ReLU(A_hat H W) with the normalised adjacency;
  - a reconstruction-error anomaly detector (trained on goodware only) with its
    threshold chosen on validation data (the 0.1 value of [2] is also recorded).

Everything refits on the same P1 split / balancing / scaling as the classical
runs (imported from run_experiments), so the subsets match Table 11/13.

Usage:
  python run_a2g.py            # full run
  python run_a2g.py --smoke    # tiny run to validate the code
"""
import argparse
import json
import os
import time

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"

import numpy as np
import pandas as pd
import tensorflow as tf
from sklearn.metrics import (accuracy_score, f1_score, precision_score,
                             recall_score, roc_auc_score)
from sklearn.model_selection import train_test_split

from run_experiments import (ARM, DATA_DIR, FEATS, OUT_DIR, PRIMARY, SEED,
                             balance, load_dedup, n_for, split_p1)

tf.keras.utils.set_random_seed(SEED)
rng = np.random.default_rng(SEED)

CFG = {
    "faithful": {"enc": [512, 256, 128], "latent": 64, "dec": [128, 256, 512],
                 "disc": [256, 128, 64], "cls": [128, 128], "head": 64},
    "compact": {"enc": [64, 32, 16], "latent": 8, "dec": [16, 32, 64],
                "disc": [64, 32, 16], "cls": [64, 64], "head": 32},
}
ENC_DROP = [0.3, 0.3, 0.2]
DEC_DROP = [0.2, 0.3, 0.3]
DISC_DROP = [0.4, 0.4, 0.3]
BATCH = 256
EPOCHS = 40
PATIENCE = 8
ADV_W = 0.1


def normalize_adj(a):
    a = a + tf.eye(tf.shape(a)[0])
    d = tf.reduce_sum(a, axis=-1, keepdims=True)
    dinv = tf.math.rsqrt(tf.maximum(d, 1e-6))
    return a * dinv * tf.transpose(dinv)


def batch_adj(z, thresh=0.7):
    zn = tf.math.l2_normalize(z, axis=1)
    sim = tf.matmul(zn, zn, transpose_b=True)
    return normalize_adj(tf.cast(sim > thresh, tf.float32))


class GraphDense(tf.keras.layers.Layer):
    def __init__(self, units, message_passing):
        super().__init__()
        self.dense = tf.keras.layers.Dense(units)
        self.message_passing = message_passing

    def call(self, h, adj):
        h = self.dense(h)
        if self.message_passing:
            h = tf.matmul(adj, h)
        return tf.nn.relu(h)


def build_encoder(d, cfg):
    x = tf.keras.Input(shape=(d,))
    h = x
    for u, p in zip(cfg["enc"], ENC_DROP):
        h = tf.keras.layers.Dense(u)(h)
        h = tf.keras.layers.BatchNormalization()(h)
        h = tf.keras.layers.ReLU()(h)
        h = tf.keras.layers.Dropout(p)(h)
    a = tf.keras.layers.Softmax()(tf.keras.layers.Dense(h.shape[-1], activation="tanh")(h))
    h = tf.keras.layers.Multiply()([h, a])
    z = tf.keras.layers.Dense(cfg["latent"], activation="relu")(h)
    return tf.keras.Model(x, z, name="encoder")


def build_decoder(d, cfg):
    z = tf.keras.Input(shape=(cfg["latent"],))
    h = z
    for u, p in zip(cfg["dec"], DEC_DROP):
        h = tf.keras.layers.Dense(u, activation="relu")(h)
        h = tf.keras.layers.Dropout(p)(h)
    out = tf.keras.layers.Dense(d, activation="sigmoid")(h)
    return tf.keras.Model(z, out, name="decoder")


def build_discriminator(cfg):
    z = tf.keras.Input(shape=(cfg["latent"],))
    h = z
    for u, p in zip(cfg["disc"], DISC_DROP):
        h = tf.keras.layers.Dense(u, activation="relu")(h)
        h = tf.keras.layers.Dropout(p)(h)
    out = tf.keras.layers.Dense(1, activation="sigmoid")(h)
    return tf.keras.Model(z, out, name="discriminator")


def build_classifier(cfg, message_passing):
    class GraphClassifier(tf.keras.Model):
        def __init__(self):
            super().__init__()
            self.drop1 = tf.keras.layers.Dropout(0.3)
            self.g1 = GraphDense(cfg["cls"][0], message_passing)
            self.drop2 = tf.keras.layers.Dropout(0.3)
            self.g2 = GraphDense(cfg["cls"][1], message_passing)
            self.drop3 = tf.keras.layers.Dropout(0.2)
            self.head = tf.keras.layers.Dense(cfg["head"], activation="relu")
            self.out = tf.keras.layers.Dense(2, activation="softmax")

        def call(self, inputs, training=False):
            z, adj = inputs
            h = self.drop1(z, training=training)
            h = self.g1(h, adj)
            h = self.drop2(h, training=training)
            h = self.g2(h, adj)
            h = self.drop3(h, training=training)
            h = self.head(h)
            return self.out(h)

    return GraphClassifier()


class A2G:
    def __init__(self, d, variant, message_passing):
        cfg = CFG[variant]
        self.d = d
        self.cfg = cfg
        self.variant = variant
        self.message_passing = message_passing
        self.encoder = build_encoder(d, cfg)
        self.decoder = build_decoder(d, cfg)
        self.discriminator = build_discriminator(cfg)
        self.classifier = build_classifier(cfg, message_passing)
        self.opt_ae = tf.keras.optimizers.Adam(1e-3)
        self.opt_disc = tf.keras.optimizers.Adam(1e-3)
        self.opt_clf = tf.keras.optimizers.Adam(1e-3)

    # --- training ---------------------------------------------------------
    @tf.function
    def _step_ae(self, x):
        with tf.GradientTape(persistent=True) as tape:
            z = self.encoder(x, training=True)
            rec = self.decoder(z, training=True)
            rec_loss = tf.reduce_mean(tf.square(x - rec))
            real = tf.stop_gradient(z)
            fake = tf.random.normal(tf.shape(real))
            d_real = self.discriminator(real, training=True)
            d_fake = self.discriminator(fake, training=True)
            d_loss = tf.reduce_mean(
                tf.keras.losses.binary_crossentropy(tf.ones_like(d_real), d_real)
                + tf.keras.losses.binary_crossentropy(tf.zeros_like(d_fake), d_fake))
            g_loss = tf.reduce_mean(tf.keras.losses.binary_crossentropy(
                tf.ones_like(d_real), self.discriminator(z, training=True)))
            ae_loss = rec_loss + ADV_W * g_loss
        ae_vars = self.encoder.trainable_variables + self.decoder.trainable_variables
        self.opt_ae.apply_gradients(
            zip(tape.gradient(ae_loss, ae_vars), ae_vars))
        d_vars = self.discriminator.trainable_variables
        self.opt_disc.apply_gradients(
            zip(tape.gradient(d_loss, d_vars), d_vars))
        del tape
        return rec_loss

    @tf.function
    def _step_clf(self, x, y):
        with tf.GradientTape() as tape:
            z = self.encoder(x, training=True)
            adj = batch_adj(z)
            logits = self.classifier([z, adj], training=True)
            loss = tf.reduce_mean(
                tf.keras.losses.sparse_categorical_crossentropy(y, logits))
        # the classifier loss also refines the encoder: the source paper trains
        # the pipeline jointly; this is our documented choice on validation data
        vars_ = self.classifier.trainable_variables + self.encoder.trainable_variables
        self.opt_clf.apply_gradients(zip(tape.gradient(loss, vars_), vars_))
        return loss

    def _batches(self, X, y, shuffle):
        idx = np.arange(len(X))
        if shuffle:
            rng.shuffle(idx)
        n = (len(idx) // BATCH) * BATCH
        for i in range(0, n, BATCH):
            b = idx[i:i + BATCH]
            yield tf.constant(X[b], dtype=tf.float32), tf.constant(y[b], dtype=tf.int32)

    def _recon(self, X):
        out = []
        for i in range(0, len(X), 1024):
            xb = tf.constant(X[i:i + 1024], dtype=tf.float32)
            z = self.encoder(xb, training=False)
            rec = self.decoder(z, training=False)
            out.append(tf.reduce_mean(tf.square(xb - rec), axis=1).numpy())
        return np.concatenate(out)

    def _proba(self, X):
        out = []
        for i in range(0, len(X), 1024):
            xb = tf.constant(X[i:i + 1024], dtype=tf.float32)
            z = self.encoder(xb, training=False)
            adj = batch_adj(z)
            p = self.classifier([z, adj], training=False).numpy()[:, 1]
            out.append(p)
        return np.concatenate(out)

    def _snapshot(self, models):
        return [[w.numpy().copy() for w in m.weights] for m in models]

    def _restore(self, models, snap):
        for m, ws in zip(models, snap):
            for w, v in zip(m.weights, ws):
                w.assign(v)

    def fit(self, Xtr, ytr, Xval, yval, epochs=EPOCHS, patience=PATIENCE,
            verbose=False):
        best = {"rec": np.inf, "snap": None}
        for ep in range(epochs):
            for xb, _ in self._batches(Xtr, ytr, shuffle=True):
                self._step_ae(xb)
            rec_val = float(np.mean(self._recon(Xval)))
            if rec_val < best["rec"] - 1e-5:
                best = {"rec": rec_val,
                        "snap": self._snapshot([self.encoder, self.decoder])}
                stall = 0
            else:
                stall += 1
            if verbose:
                print(f"    AE ep {ep + 1}: val rec {rec_val:.5f}")
            if stall >= patience:
                break
        self._restore([self.encoder, self.decoder], best["snap"])

        best = {"f1": -1.0, "snap": None}
        for ep in range(epochs):
            for xb, yb in self._batches(Xtr, ytr, shuffle=True):
                self._step_clf(xb, yb)
            f1v = f1_score(yval, (self._proba(Xval) >= 0.5).astype(int),
                           pos_label=1, zero_division=0)
            if f1v > best["f1"] + 1e-5:
                best = {"f1": f1v,
                        "snap": self._snapshot([self.encoder, self.classifier])}
                stall = 0
            else:
                stall += 1
            if verbose:
                print(f"    CLF ep {ep + 1}: val F1 {f1v:.4f}")
            if stall >= patience:
                break
        self._restore([self.encoder, self.classifier], best["snap"])
        return best["f1"]

    def param_kb(self):
        total = 0
        for m in (self.encoder, self.decoder, self.discriminator, self.classifier):
            for w in m.weights:
                total += int(np.prod(w.shape)) * 4
        return total / 1024.0


class AnomalyAE:
    """Compact autoencoder trained on goodware only."""

    def __init__(self, d):
        cfg = CFG["compact"]
        self.encoder = build_encoder(d, cfg)
        self.decoder = build_decoder(d, cfg)
        self.opt = tf.keras.optimizers.Adam(1e-3)

    @tf.function
    def _step(self, x):
        with tf.GradientTape() as tape:
            rec = self.decoder(self.encoder(x, training=True), training=True)
            loss = tf.reduce_mean(tf.square(x - rec))
        vars_ = self.encoder.trainable_variables + self.decoder.trainable_variables
        self.opt.apply_gradients(zip(tape.gradient(loss, vars_), vars_))
        return loss

    def recon(self, X):
        out = []
        for i in range(0, len(X), 1024):
            xb = tf.constant(X[i:i + 1024], dtype=tf.float32)
            rec = self.decoder(self.encoder(xb, training=False), training=False)
            out.append(tf.reduce_mean(tf.square(xb - rec), axis=1).numpy())
        return np.concatenate(out)

    def fit(self, X, epochs=30, patience=8):
        best = {"rec": np.inf, "snap": None}
        for ep in range(epochs):
            for i in range(0, (len(X) // BATCH) * BATCH, BATCH):
                self._step(tf.constant(X[i:i + BATCH], dtype=tf.float32))
            rec = float(np.mean(self.recon(X)))
            if rec < best["rec"] - 1e-5:
                best = {"rec": rec,
                        "snap": [[w.numpy().copy() for w in m.weights]
                                 for m in (self.encoder, self.decoder)]}
                stall = 0
            else:
                stall += 1
            if stall >= patience:
                break
        for m, ws in zip((self.encoder, self.decoder), best["snap"]):
            for w, v in zip(m.weights, ws):
                w.assign(v)


def eval_metrics(yte, proba):
    pred = (proba >= 0.5).astype(int)
    return {
        "accuracy": float(accuracy_score(yte, pred)),
        "precision": float(precision_score(yte, pred, pos_label=1, zero_division=0)),
        "recall": float(recall_score(yte, pred, pos_label=1, zero_division=0)),
        "f1": float(f1_score(yte, pred, pos_label=1, zero_division=0)),
        "roc_auc": float(roc_auc_score(yte, proba)) if len(np.unique(yte)) > 1 else float("nan"),
    }


def threshold_f1(y, err, threshold):
    return f1_score(y, (err > threshold).astype(int), pos_label=1, zero_division=0)


def best_threshold(y, err):
    cands = np.unique(np.quantile(err, np.linspace(0.01, 0.99, 99)))
    scores = [(threshold_f1(y, err, t), float(t)) for t in cands]
    return max(scores)[1] if scores else 0.1


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    args = ap.parse_args()

    X, y, names, _ = load_dedup(os.path.join(DATA_DIR, PRIMARY))
    tr, te = split_p1(y)
    Xtr_raw, ytr = X.iloc[tr].reset_index(drop=True), y[tr]
    Xte_raw, yte = X.iloc[te].reset_index(drop=True), y[te]
    if args.smoke:
        keep = np.concatenate([np.where(ytr == 0)[0][:400], np.where(ytr == 1)[0][:400]])
        Xtr_raw, ytr = Xtr_raw.iloc[keep].reset_index(drop=True), ytr[keep]
        kt = np.concatenate([np.where(yte == 0)[0][:200], np.where(yte == 1)[0][:200]])
        Xte_raw, yte = Xte_raw.iloc[kt].reset_index(drop=True), yte[kt]

    res = json.load(open(os.path.join(OUT_DIR, "classical_results.json")))
    p1 = res["primary_P1"]
    fsa_idx = np.array(p1["fsa"])
    sc = p1["scores"]
    order_c = np.lexsort((-np.array(sc["combined"]), -np.array(sc["votes"])))
    p_fsc = p1["FS-C"]["chosen_p"]
    fsc_idx = order_c[:n_for(p_fsc, len(FEATS))]

    subsets = {"All 21": np.arange(len(FEATS)),
               "FS-A": fsa_idx,
               "FS-C best": fsc_idx}

    from sklearn.preprocessing import MinMaxScaler
    Xb, yb = balance(Xtr_raw, ytr, ARM, SEED)
    scaler = MinMaxScaler().fit(Xb)
    Xb_s = scaler.transform(Xb)
    Xte_s = scaler.transform(Xte_raw)

    itr, iva = train_test_split(np.arange(len(Xb_s)), test_size=0.2, stratify=yb,
                                random_state=SEED)
    Xa, ya = Xb_s[itr], yb[itr]
    Xv, yv = Xb_s[iva], yb[iva]

    variants = ["compact"] if args.smoke else ["faithful", "compact"]
    modes = ["faithful", "message"] if not args.smoke else ["message"]
    subset_names = list(subsets) if not args.smoke else ["All 21"]
    epochs = 3 if args.smoke else EPOCHS

    out = {"configs": {}, "selection": {}, "cost": {}, "subset_sizes": {}}
    for sname in subset_names:
        idx = subsets[sname]
        d = len(idx)
        out["subset_sizes"][sname] = int(d)
        for variant in variants:
            for mode in modes:
                key = f"{sname}|{variant}|{mode}"
                print(f"== {key} (d={d}) ==", flush=True)
                t0 = time.time()
                model = A2G(d, variant, mode == "message")
                val_f1 = model.fit(Xa[:, idx], ya, Xv[:, idx], yv,
                                   epochs=epochs, patience=PATIENCE)
                train_s = time.time() - t0
                t0 = time.time()
                proba = model._proba(Xte_s[:, idx])
                pred_ms = (time.time() - t0) * 1000.0
                m = eval_metrics(yte, proba)
                m.update({"train_s": train_s, "pred_ms": pred_ms,
                          "size_kb": model.param_kb(), "val_f1": float(val_f1)})
                out["configs"][key] = m
                print(f"   F1={m['f1']:.4f} acc={m['accuracy']:.4f} "
                      f"train={train_s:.1f}s size={m['size_kb']:.0f}KB", flush=True)
                if variant == "compact" and sname in ("All 21", "FS-C best"):
                    out["cost"][f"{sname}|{mode}"] = {
                        "train_s": train_s, "pred_ms": pred_ms,
                        "size_kb": m["size_kb"]}

    # --- anomaly detector per input subset (goodware-only AE) ---------------
    for sname in subset_names:
        idx = subsets[sname]
        print(f"== anomaly detector: {sname} ==", flush=True)
        gw = ya == 0
        t0 = time.time()
        ae = AnomalyAE(len(idx))
        ae.fit(Xa[gw][:, idx], epochs=3 if args.smoke else 30)
        err_tr = ae.recon(Xa[gw][:, idx])
        err_val = ae.recon(Xv[:, idx])
        err_te = ae.recon(Xte_s[:, idx])
        thr = best_threshold(yv, err_val)
        f1_01 = float(threshold_f1(yte, err_te, 0.1))
        f1_val = float(threshold_f1(yte, err_te, thr))
        out["configs"][f"anomaly|{sname}"] = {
            "threshold": float(thr), "f1_at_chosen": f1_val,
            "f1_at_0.1": f1_01, "train_s": time.time() - t0,
            "mean_err_goodware": float(np.mean(err_tr))}
        print(f"   thr={thr:.4f} F1(chosen)={f1_val:.4f} F1(0.1)={f1_01:.4f}",
              flush=True)

    with open(os.path.join(OUT_DIR, "a2g_results.json"), "w", encoding="utf-8") as fh:
        json.dump(out, fh, indent=1)
    print("saved a2g_results.json", flush=True)


if __name__ == "__main__":
    main()
