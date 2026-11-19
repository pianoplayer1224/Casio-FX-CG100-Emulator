#!/usr/bin/env python3
"""Timings from a video of calc/bm_bigint.py, which analyze.py can't read: it has two test tables.

Stage 1 is the usual run() (62 edges). Stage 2 times mvb2 with ~500 KB held live, then for3; the
first mvb2 phase ends on white with the block already white, so only phases 3 and 4 of mvb2 show,
and their white-minus-black difference is taken from for3.

    python3 tools/bigint.py VIDEO --note "OS 02.10.0202, batch 18"
"""
import argparse
import ast
import csv
import os
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(__file__))
import analyze as A

SCRIPT = os.path.join(os.path.dirname(__file__), "..", "calc", "bm_bigint.py")


def tables():
    out = []
    for node in ast.parse(open(SCRIPT).read()).body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", None) == "T":
            out.append([{"name": ast.literal_eval(e.elts[0]), "n": ast.literal_eval(e.elts[2]),
                         "unroll": ast.literal_eval(e.elts[3]), "base": ast.literal_eval(e.elts[4])}
                        for e in node.value.elts])
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("video")
    ap.add_argument("--note", default="")
    ap.add_argument("--roi")
    ap.add_argument("--out", default="results")
    a = ap.parse_args()
    t1, t2 = tables()
    count = 4 * len(t1) + 2 + 8
    frames, times, fps = A.read_frames(a.video, 64, None, None)
    if a.roi:
        mask = A.roi_mask(frames.shape[1:], [float(v) for v in a.roi.split(",")])
    else:
        mask, _ = A.find_marker(frames, count)
    edges, lo, hi = A.find_edges(frames[:, mask].mean(axis=1), times)
    run, warning = A.pick_run(edges, count)
    if warning:
        print("WARN ", warning)
    rows, overhead = A.analyze(t1, run[:4 * len(t1) + 2], (1, 2, 2, 1))
    # Stage 2: e[0] ends mvb2's 2N phase, e[1] and e[2] its other 2N and last N, then for3 and the final white
    e = [x[0] for x in run[4 * len(t1) + 2:]]
    iv = np.diff(e)
    f = t2[1]
    p = iv[2:6]
    i1, i2, delta = (p[0] + p[3]) / 2, (p[1] + p[2]) / 2, p[0] - p[3]
    rows["for3"] = dict(f, i1=i1, i2=i2, delta=delta, fixed_s=2 * i1 - i2 + delta / 2,
                        per_iter_us=(i2 - i1) / f["n"] * 1e6)
    m = t2[0]
    i2, i1 = iv[0], iv[1]
    rows["mvb2"] = dict(m, i1=i1, i2=i2, delta=delta, fixed_s=2 * i1 - i2 + delta,
                        per_iter_us=(i2 - i1 - delta) / m["n"] * 1e6)
    for k in ("for3", "mvb2"):
        r = rows[k]
        base = rows[r["base"]] if r["base"] else None
        r["per_op_us"] = (r["per_iter_us"] - (base["per_iter_us"] if base else 0)) / r["unroll"]
    print("video %s  %.2f fps  levels %.0f..%.0f  white redraw %.1f ms" % (a.video, fps, lo, hi, overhead * 1e3))
    print("%-8s %7s %8s %8s %11s %10s %9s" % ("test", "n", "N(s)", "2N(s)", "us/iter", "us/op", "fixed(ms)"))
    for r in rows.values():
        print("%-8s %7d %8.3f %8.3f %11.3f %10.3f %9.1f" % (r["name"], r["n"], r["i1"], r["i2"], r["per_iter_us"],
                                                          r["per_op_us"], r["fixed_s"] * 1e3))
    print("drift for2 vs for %+.2f%%, for3 vs for %+.2f%%" % (
        100 * (rows["for2"]["per_iter_us"] / rows["for"]["per_iter_us"] - 1),
        100 * (rows["for3"]["per_iter_us"] / rows["for"]["per_iter_us"] - 1)))
    os.makedirs(a.out, exist_ok=True)
    path = os.path.join(a.out, "results.csv")
    with open(path, "a", newline="") as fh:
        wr = csv.writer(fh)
        for r in rows.values():
            wr.writerow(["bm_bigint", os.path.basename(a.video), a.note, 1, r["name"], r["n"], r["unroll"],
                         r["base"] or "", "%.5f" % r["i1"], "%.5f" % r["i2"], "%.4f" % r["per_iter_us"],
                         "%.4f" % r["per_op_us"], "%.2f" % (r["fixed_s"] * 1e3), "%.2f" % (overhead * 1e3),
                         "%.3f" % fps, "%.2f" % (r["delta"] * 1e3), "1-2-2-1"])
    print("appended to", path)


if __name__ == "__main__":
    main()
