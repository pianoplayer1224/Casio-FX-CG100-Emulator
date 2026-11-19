#!/usr/bin/env python3
"""Combine runs in results/results.csv: median and spread per test.

    python3 tools/summary.py bm_core
    python3 tools/summary.py bm_core --retune 5    # rewrite n in calc/bm_core.py

--retune sets each test's iteration count so its N phase does about that many
seconds of work. The screen only updates on a ~16 ms refresh tick, so each
timed edge is uncertain by up to ~8 ms; longer phases shrink that error.
"""
import argparse
import csv
import os
import re
import statistics
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import analyze  # noqa: E402


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("script", help="script name, e.g. bm_core")
    ap.add_argument("--csv", default=os.path.join(ROOT, "results", "results.csv"))
    ap.add_argument("--retune", type=float, metavar="SECONDS",
                    help="rewrite iteration counts in calc/SCRIPT.py for this N-phase length")
    a = ap.parse_args()

    rows = [r for r in csv.DictReader(open(a.csv)) if r["script"] == a.script]
    if not rows:
        sys.exit("no rows for %s in %s" % (a.script, a.csv))
    tests = {}
    for r in rows:
        tests.setdefault(r["test"], []).append(r)

    videos = len({r["video"] for r in rows})
    print("%s: %d runs\n" % (a.script, videos))
    print("%-8s %6s %11s %10s %8s %8s %7s" %
          ("test", "unroll", "us/iter", "us/op", "min", "max", "spread"))
    per_iter = {}
    for name, rs in tests.items():
        ops = [float(r["us_per_op"]) for r in rs]
        it = [float(r["us_per_iter"]) for r in rs]
        med = statistics.median(ops)
        per_iter[name] = statistics.median(it)
        spread = (max(ops) - min(ops)) / med * 100 if med else 0
        print("%-8s %6s %11.3f %10.3f %8.3f %8.3f %6.1f%%" %
              (name, rs[0]["unroll"], per_iter[name], med, min(ops), max(ops), spread))
    redraw = statistics.median(float(r["redraw_ms"]) for r in rows)
    print("\nblock redraw (set_pixel 128x64 + show_screen): %.1f ms" % redraw)

    if a.retune:
        path = os.path.join(ROOT, "calc", a.script + ".py")
        src = open(path).read()
        scale = float(rows[0]["scale"])

        def fix(m):
            name = m.group(2)
            if per_iter.get(name, 0) <= 0:  # unmeasurable: keep, adjust by hand
                print("kept n for %s (no measurable cost)" % name)
                return m.group(0)
            n = a.retune / (per_iter[name] * 1e-6)
            digits = len(str(int(n))) - 2
            n = max(1, int(round(n, -max(digits, 0))))
            return "%s%d%s" % (m.group(1), n, m.group(3))

        new = re.sub(r'(\("(\w+)",\w+,)\d+(,)', fix, src)
        if scale != 1:
            new = re.sub(r"^SCALE=.*$", "SCALE=1", new, count=1, flags=re.M)
        open(path, "w").write(new)
        print("retuned %s for ~%.0f s N phases (est. run %.0f s)" %
              (path, a.retune, len(per_iter) * sum(analyze.load_phases(path)) *
               (a.retune + redraw / 1e3)))


if __name__ == "__main__":
    main()
