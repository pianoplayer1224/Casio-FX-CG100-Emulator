#!/usr/bin/env python3
"""Fit the emulator's per-event costs to the filmed calculator timings.

For each calc/bm_*.py the emulator runs the script itself (unthrottled) and
records every event counter at each show_screen(). The counts between two
block flips are the work of one phase; applying the same N/2N differencing
as tools/analyze.py gives the events per iteration of each test, which must
cost what the calculator measured (results/results.csv):

    measured_us_per_iter[test] = sum(events_per_iter[test, e] * cost[e])

Costs are solved by bounded least squares on relative error, with a weak
pull towards a typical value per event group so events the benchmarks can't
separate (e.g. opcodes that always occur together) get sensible values.
bm_ref is held out and used only to check the result.

    python3 emu/fit.py                 # fit, write emu/costs.txt, report
    python3 emu/fit.py --check         # just report with the current costs
"""
import argparse
import csv
import os
import re
import statistics
import subprocess
import sys
import tempfile

import numpy as np
from scipy.optimize import lsq_linear

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
sys.path.insert(0, os.path.join(ROOT, "tools"))
import analyze  # noqa: E402
import series  # noqa: E402

EMU = os.path.join(HERE, "micropython", "ports", "cg100", "micropython")
COSTS = os.path.join(HERE, "costs.txt")
# Scripts without filmed results yet are skipped automatically
FIT = ["bm_core", "bm_float", "bm_call", "bm_data", "bm_plot", "bm_gap", "bm_str",
       "bm_print", "bm_mac", "bm_bytes", "bm_bigint"]
HOLDOUT = ["bm_ref", "bm_show", "bm_show2"]
# Tests whose cost depends on heap state (tuple building): checked, not fitted.
# bm_mac step is a whole program, kept as an independent check; bm_bytes bl3 and
# bl4 have phases too short to time (the counts assumed len() grew with size)
STATEFUL = {"tnew", "spxt", "gpx", "swap", "step", "bl3", "bl4"}
# bm_tuple sections not fitted: one-op blocks too short to time, and after
# `hold` the calculator's heap layout differs from the emulator's
TUPLE_SKIP = {"hold", "free", "t2live", "t2c"}
# Costs not fitted from per-test edges:
#  getkey() with no key down: ~8.2 ms (Cemetech t=20274, Graph Math+)
#  print() itself: one call per line in every bm_print test, so its cost
#  is folded into print_line
#  compiling source: importing a 76 KB data module (298 lines of b"...")
#  took 0.98 s on the calculator (Bad Apple bench.py stage 4, stopwatch
#  from a screen recording), 0.04 s of it the import's own work: 0.94 s /
#  76021 characters
#  show_screen() with something drawn, and per canvas row drawn on since
#  the last call: calc/bm_show2.py (bm_core_videos/15), fitted to its
#  differences (px2d - px1 etc.), all within 0.5%
EXTERNAL = {"getkey_idle": 8200.0, "getkey_held": 20.0, "fn_print": 0.0,
            "lex_char": 12.365, "show_row": 52.15, "show_any": 38.92}
# Measured cost of scanning one allocation-table byte (4 heap blocks):
# bm_tuple slope 0.1008 us per 2-block tuple = 0.5 table byte
SCAN_US = 0.2016


def prior(name):
    """Typical cost (us) and how loosely to hold it, per event group."""
    if name.startswith("op_"):
        return 2.0, 4.0
    if name.startswith("bin_"):
        cls = name.rsplit("_", 1)[1]
        return {"small": (2.0, 4.0), "float": (20.0, 30.0), "big": (40.0, 80.0),
                "bool": (6.0, 10.0), "other": (5.0, 20.0)}[cls]
    if name == "gc_mark":
        return 0.5, 2.0
    if name.startswith("fn_"):
        return 15.0, 10000.0
    return {"call_closure": (5.0, 20.0), "call_bound": (10.0, 30.0),
            "call_new": (60.0, 200.0), "call_py": (20.0, 40.0), "call_arg": (1.0, 4.0), "call_kw": (3.0, 10.0),
            "call_native": (10.0, 30.0), "call_other": (20.0, 100.0),
            "alloc": (5.0, 20.0), "gc": (15000.0, 10000.0), "qstr_find": (5.0, 20.0), "qstr_scan": (0.1, 0.5),
            "map_probe": (0.2, 0.5), "map_scan": (0.2, 0.5), "iter_list": (2.0, 5.0), "iter_range": (2.0, 5.0), "iter_other": (3.0, 10.0), "big_digits": (2.0, 10.0),
            "pixel_on": (0.5, 5.0), "pixel_off": (0.5, 5.0),
            "char_small": (40.0, 100.0), "char_medium": (90.0, 200.0),
            "char_large": (140.0, 300.0), "print_char": (2.0, 10.0),
            "print_write": (15.0, 50.0), "print_line": (150.0, 300.0), "unary": (3.0, 10.0)}.get(name, (5.0, 20.0))


def script_path(script, counts=None, tmpdir=None):
    """calc/SCRIPT.py, or a copy in tmpdir with the iteration counts the
    filmed runs used (tuple costs depend on how many run between GCs)."""
    path = os.path.join(ROOT, "calc", script + ".py")
    if not counts:
        return path
    src = open(path).read()
    src = re.sub(r'(\("(\w+)",\w+,)\d+(,)',
                 lambda m: m.group(1) + str(counts.get(m.group(2), "")) + m.group(3)
                 if m.group(2) in counts else m.group(0), src)
    out = os.path.join(tmpdir, script + ".py")
    open(out, "w").write(src)
    return out


def run_emulator(script, costs=None, counts=None):
    """Counters at every block flip of one emulated run: (names, array).

    Only show_screen() calls that change the block's colour are edges, as in
    the video (bm_plot's `show` test calls show_screen() 20000 times)."""
    with tempfile.TemporaryDirectory() as d:
        out = os.path.join(d, "counts.csv")
        env = dict(os.environ, CG100_COUNTS=out, CG100_FAST="1")
        env.pop("CG100_SHM", None)
        if costs:
            env["CG100_COSTS"] = costs
        src = script_path(script, counts, d)
        r = subprocess.run([EMU, src], cwd=d, env=env, capture_output=True, text=True)
        if r.returncode:
            sys.exit("emulator failed on %s:\n%s" % (script, r.stderr[-2000:]))
        rows = list(csv.reader(open(out)))
    data = np.array(rows[1:], dtype=np.float64)
    pix = data[:, 0]
    flips = [i for i in range(1, len(pix)) if pix[i] != pix[i - 1]]
    return rows[0][1:], data[flips, 1:]


def per_iter_counts(script, shows, counts=None):
    """Events per iteration of each test, using analyze.py's phase maths."""
    path = os.path.join(ROOT, "calc", script + ".py")
    _, tests = analyze.load_script(path)
    for t in tests:
        t["n"] = (counts or {}).get(t["name"], t["n"])
    phases = analyze.load_phases(path)
    count = len(phases) * len(tests) + 2
    edges = shows[:count]
    iv = np.diff(edges, axis=0)
    p = len(phases)
    out = {}
    for k, t in enumerate(tests):
        ph = iv[p * k:p * k + p]
        if p == 4:
            d = (ph[1] + ph[2]) / 2 - (ph[0] + ph[3]) / 2
        else:
            d = ph[1] - ph[0]
        out[t["name"]] = d / t["n"]
    return out, iv[-1]


def measured(script):
    """Median us/iter per test, and the iteration counts behind it (those of
    the most recent run; runs with other counts are left out)."""
    rows = [r for r in csv.DictReader(open(os.path.join(ROOT, "results", "results.csv")))
            if r["script"] == script]
    counts = {r["test"]: int(r["n"]) for r in rows}   # last row per test wins
    tests = {}
    for r in rows:
        if int(r["n"]) == counts[r["test"]]:
            tests.setdefault(r["test"], []).append(float(r["us_per_iter"]))
    return {k: statistics.median(v) for k, v in tests.items()}, counts


def tuple_blocks():
    """bm_tuple: events per block (work plus block redraw) and the measured
    block interval, for blocks where neither side ran a GC (except l2). The slower
    white redraw is a display delay, not work, so it is taken off."""
    names, shows = run_emulator("bm_tuple")
    path = os.path.join(ROOT, "calc", "bm_tuple.py")
    _, sections = series.load_blocks(path)
    iv = np.diff(shows[:series.edge_count(sections)], axis=0)
    rows = [r for r in csv.DictReader(open(os.path.join(ROOT, "results", "series.csv")))
            if r["script"] == "bm_tuple"]
    gc = names.index("gc")
    # per video: white idle redraw minus black idle redraw
    extra = {}
    for v in {r["video"] for r in rows}:
        idle = [r for r in rows if r["video"] == v and r["section"].startswith("idle")]
        w = statistics.median(float(r["interval_s"]) for r in idle if r["ends_white"] == "1")
        b = statistics.median(float(r["interval_s"]) for r in idle if r["ends_white"] == "0")
        extra[v] = w - b
    eqs = []
    k = 0
    for s in sections:
        for b in range(s["blocks"]):
            iv_s = [float(r["interval_s"]) - (extra[r["video"]] if r["ends_white"] == "1" else 0)
                    for r in rows if r["section"] == s["name"] and int(r["block"]) == b]
            drop = any(float(r["us_per_op"]) < 0.8 * float(p["us_per_op"])
                       for r in rows for p in rows
                       if r["section"] == s["name"] and int(r["block"]) == b
                       and p["video"] == r["video"] and p["section"] == s["name"]
                       and int(p["block"]) == b - 1) if s["n"] and b else False
            # l2 (lists) has GCs on both sides at a steady rate: it pins the GC cost
            nogc = iv[k][gc] == 0 or s["name"] == "l2"
            if iv_s and nogc and not drop and s["name"] not in TUPLE_SKIP:
                eqs.append(("tuple:%s%d" % (s["name"], b), iv[k], statistics.median(iv_s) * 1e6))
            k += 1
    return names, eqs


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="report only, keep costs.txt")
    ap.add_argument("--ridge", type=float, default=0.02, help="pull towards priors")
    a = ap.parse_args()

    names = None
    eqs = []      # (label, counts, measured_us, fitted?)
    redraw = None
    for script in FIT + HOLDOUT:
        meas, counts = measured(script)
        if not meas:
            print("no results yet for", script)
            continue
        names, shows = run_emulator(script, counts=counts)
        model, last = per_iter_counts(script, shows, counts)
        if script == "bm_bigint":
            # Its second stage, as tools/bigint.py reads it: mvb2 from its 2N and last N phases
            iv = np.diff(shows[len(model) * 4 + 2:], axis=0)
            model["mvb2"] = (iv[0] - iv[1]) / counts["mvb2"]
            model["for3"] = ((iv[3] + iv[4]) - (iv[2] + iv[5])) / 2 / counts["for3"]
        for test, c in model.items():
            if test in meas and meas[test] > 0:
                fit = script in FIT and test not in STATEFUL
                eqs.append(("%s:%s" % (script, test), c, meas[test], fit))
        if script == "bm_core":
            redraw = last   # final white redraw: same work as a black one
    # A black block redraw (bm_tuple idle blocks: 201.4-202.3 ms) pins pixel costs
    eqs.append(("redraw:black", redraw, 201.9e3, True))

    tnames, teqs = tuple_blocks()
    assert tnames == names
    for label, c, us in teqs:
        eqs.append((label, c, us, True))

    scan = names.index("alloc_scan")
    A = np.array([e[1] for e in eqs])
    y = np.array([e[2] for e in eqs])
    fitted = np.array([e[3] for e in eqs])
    known = np.zeros(len(names))
    known[scan] = SCAN_US
    for n, c in EXTERNAL.items():
        known[names.index(n)] = c

    if a.check:
        cost = known.copy()
        for line in open(COSTS):
            if line.strip() and not line.startswith("#"):
                n, c = line.split()
                cost[names.index(n)] = float(c)
    else:
        used = np.where((np.abs(A[fitted]).sum(axis=0) > 0) & (known == 0))[0]
        rhs = y[fitted] - A[fitted] @ known
        w = 1 / y[fitted]                        # relative error
        M = A[fitted][:, used] * w[:, None]
        b = rhs * w
        pri = np.array([prior(names[i]) for i in used])
        R = np.diag(a.ridge / pri[:, 1])
        M = np.vstack([M, R])
        b = np.concatenate([b, a.ridge * pri[:, 0] / pri[:, 1]])
        sol = lsq_linear(M, b, bounds=(0, np.inf)).x
        cost = known.copy()
        cost[used] = sol
        # Events only the held-out programs use get their typical value
        seen = np.where((np.abs(A).sum(axis=0) > 0) & (cost == 0)
                        & ~np.isin(np.arange(len(names)), used)
                       & ~np.isin(names, list(EXTERNAL)))[0]
        for i in seen:
            cost[i] = prior(names[i])[0]
        if len(seen):
            print("not covered by fitted tests, using typical cost:",
                  ", ".join(names[i] for i in seen))
        with open(COSTS, "w") as f:
            f.write("# us per event, fitted by emu/fit.py to results/results.csv\n")
            for i in range(len(names)):
                if cost[i]:
                    f.write("%s %.5f\n" % (names[i], cost[i]))
        print("wrote", COSTS, "(%d events)\n" % (np.count_nonzero(cost)))

    pred = A @ cost
    err = pred / y - 1
    for title, sel in (("fitted", fitted),
                       ("held out", ~fitted & np.array(["tuple:" not in e[0] for e in eqs])),
                       ("bm_tuple blocks (no GC)", np.array(["tuple:" in e[0] for e in eqs]))):
        idx = np.where(sel)[0]
        if not len(idx):
            continue
        print("%s: median |error| %.1f%%, worst %.1f%%" %
              (title, np.median(np.abs(err[idx])) * 100, np.max(np.abs(err[idx])) * 100))
        if "tuple" in title:
            continue
        for i in idx:
            flag = "  <--" if abs(err[i]) > 0.05 else ""
            print("  %-22s %12.2f %12.2f %+7.1f%%%s" % (eqs[i][0], y[i], pred[i], err[i] * 100, flag))
        print()


if __name__ == "__main__":
    main()
