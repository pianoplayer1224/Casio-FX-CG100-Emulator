#!/usr/bin/env python3
"""Per-block timings for calc/bm_tuple.py (or any script with a block table B).

Unlike the bm_* test tables, bm_tuple.py repeats the same block of work many
times and flips the block after each one, to show how the cost of an op
changes as the script runs. Each interval is one block of work plus one block
redraw; the redraw is measured by the idle sections (no work) and subtracted
separately for blocks ending white and black.

    python3 tools/series.py VIDEO --script calc/bm_tuple.py --note "..."

Appends one row per block to results/series.csv.
"""
import argparse
import ast
import csv
import os
import statistics
import sys

import numpy as np

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import analyze  # noqa: E402

SPARK = "_.:-=+*#%@"


def load_blocks(path):
    """Read SCALE and the block table B from the script without running it."""
    tree = ast.parse(open(path).read(), path)
    scale = 1
    sections = None
    for node in tree.body:
        if not (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)):
            continue
        if node.targets[0].id == "SCALE":
            scale = ast.literal_eval(node.value)
        elif node.targets[0].id == "B":
            sections = []
            for elt in node.value.elts:
                name, _, n, unroll, blocks = elt.elts
                n = ast.literal_eval(n)
                # Same rounding as run() on the calculator
                sections.append({
                    "name": ast.literal_eval(name),
                    "n": 0 if n == 0 else max(1, int(n * scale)),
                    "unroll": ast.literal_eval(unroll),
                    "blocks": ast.literal_eval(blocks),
                })
    if sections is None:
        sys.exit("no block table B found in " + path)
    return scale, sections


def edge_count(sections):
    return sum(s["blocks"] for s in sections) + 2


def analyze_blocks(sections, edges):
    """One row per block: interval, work after removing the redraw, us per op.

    Interval i ends on edge i+1; edge 0 goes dark, so even intervals end on
    a white block and odd ones on black."""
    iv = np.diff([e[0] for e in edges])
    idle = {True: [], False: []}
    k = 0
    for s in sections:
        for _ in range(s["blocks"]):
            if s["n"] == 0:
                idle[k % 2 == 0].append(iv[k])
            k += 1
    if not idle[True] or not idle[False]:
        sys.exit("need idle sections (n=0) ending on both colours")
    redraw = {c: statistics.median(v) for c, v in idle.items()}
    rows = []
    k = 0
    done = {}  # ops of each kind of function done so far
    for s in sections:
        for b in range(s["blocks"]):
            white = k % 2 == 0
            work = iv[k] - redraw[white]
            ops = s["n"] * s["unroll"]
            rows.append({
                "section": s["name"], "block": b, "ops": ops,
                "ops_before": done.get(s["name"], 0),
                "interval_s": iv[k], "work_s": work, "white": white,
                "us_per_op": work / ops * 1e6 if ops else float("nan"),
            })
            done[s["name"]] = done.get(s["name"], 0) + ops
            k += 1
    return rows, redraw


def spark(values):
    lo, hi = min(values), max(values)
    span = hi - lo or 1
    return "".join(SPARK[int((v - lo) / span * (len(SPARK) - 1))] for v in values)


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--script", default=os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "calc", "bm_tuple.py"))
    ap.add_argument("--roi", help="manual block region as fractions x,y,w,h of the frame")
    ap.add_argument("--start", type=float, help="ignore video before this many seconds")
    ap.add_argument("--end", type=float, help="ignore video after this many seconds")
    ap.add_argument("--width", type=int, default=64, help="analysis width in pixels")
    ap.add_argument("--out", default="results", help="directory for results")
    ap.add_argument("--note", default="", help="free text saved with results")
    ap.add_argument("--blocks", action="store_true", help="print every block, not just sections")
    a = ap.parse_args()

    scale, sections = load_blocks(a.script)
    count = edge_count(sections)
    frames, times, fps = analyze.read_frames(a.video, a.width, a.start, a.end)
    if a.roi:
        mask = analyze.roi_mask(frames.shape[1:], [float(v) for v in a.roi.split(",")])
    else:
        mask, _ = analyze.find_marker(frames, count)
    edges, _, _ = analyze.find_edges(frames[:, mask].mean(axis=1), times)
    run, warning = analyze.pick_run(edges, count)
    rows, redraw = analyze_blocks(sections, run)

    print("video  %s  %.2f fps" % (a.video, fps))
    if warning:
        print("WARN  ", warning)
    print("redraw  white %.1f ms  black %.1f ms  (from idle blocks)" %
          (redraw[True] * 1e3, redraw[False] * 1e3))
    print("each block is uncertain by ~16 ms (screen refresh tick)\n")
    print("%-7s %6s %6s %9s %9s %9s %9s  %s" %
          ("section", "blocks", "ops", "first", "median", "last", "min-max%", "us/op over blocks"))
    for s in sections:
        rs = [r for r in rows if r["section"] == s["name"]]
        if not s["n"]:
            print("%-7s %6d %6s  idle: %s ms" % (s["name"], len(rs), "-", " ".join(
                "%.0f" % (r["interval_s"] * 1e3) for r in rs)))
            continue
        v = [r["us_per_op"] for r in rs]
        med = statistics.median(v)
        print("%-7s %6d %6d %9.1f %9.1f %9.1f %8.1f%%  %s" %
              (s["name"], len(rs), s["n"] * s["unroll"], v[0], med, v[-1],
               (max(v) - min(v)) / med * 100, spark(v)))
        if a.blocks:
            print("        " + " ".join("%.0f" % x for x in v))

    os.makedirs(a.out, exist_ok=True)
    path = os.path.join(a.out, "series.csv")
    new = not os.path.exists(path)
    name = os.path.splitext(os.path.basename(a.script))[0]
    with open(path, "a", newline="") as f:
        wr = csv.writer(f)
        if new:
            wr.writerow(["script", "video", "note", "scale", "section", "block", "ops",
                         "ops_before", "interval_s", "work_s", "ends_white", "us_per_op"])
        for r in rows:
            wr.writerow([name, os.path.basename(a.video), a.note, scale, r["section"],
                         r["block"], r["ops"], r["ops_before"], "%.5f" % r["interval_s"],
                         "%.5f" % r["work_s"], int(r["white"]), "%.3f" % r["us_per_op"]])
    print("\nappended to", path)


if __name__ == "__main__":
    main()
