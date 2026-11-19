#!/usr/bin/env python3
"""Check the calculator scripts and the video analyzer without a calculator.

1. Every calc/bm_*.py fits the editor limits (300 lines, 255 chars per line)
   and runs under CPython with a fake casioplot, flipping the block the
   number of times analyze.py expects.
2. A synthetic video with known timings goes through analyze.py, and the
   recovered per-iteration costs are compared with the truth.
"""
import contextlib
import glob
import io
import os
import random
import subprocess
import sys
import tempfile
import types

import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, "tools"))
import analyze  # noqa: E402
import series  # noqa: E402


def fake_casioplot(log):
    buf = {}
    m = types.ModuleType("casioplot")
    m.set_pixel = lambda x, y, c=(0, 0, 0): buf.__setitem__((x, y), c)
    m.get_pixel = lambda x, y: buf.get((x, y), (255, 255, 255))
    m.clear_screen = buf.clear
    m.draw_string = lambda x, y, s, c=(0, 0, 0), size="medium": None
    m.show_screen = lambda: log.append(buf.get((0, 0), (255, 255, 255)))
    return m


def check_scripts():
    ok = True
    for path in sorted(glob.glob(os.path.join(ROOT, "calc", "bm_*.py"))):
        src = open(path).read()
        lines = src.split("\n")
        name = os.path.basename(path)
        longest = max(len(l) for l in lines)
        if len(lines) > 300 or longest > 255:
            print("FAIL %s: %d lines, longest %d chars" % (name, len(lines), longest))
            ok = False
        if len(os.path.splitext(name)[0]) > 8:
            print("WARN %s: name longer than 8 characters" % name)
        if "\nB=[" in src:
            _, sections = series.load_blocks(path)
            tests, want = sections, series.edge_count(sections)
        else:
            _, tests = analyze.load_script(path)
            want = len(analyze.load_phases(path)) * len(tests) + 2
            if name == "bm_bigint.py":
                want += 8  # its second stage, read by tools/bigint.py
        log = []
        sys.modules["casioplot"] = fake_casioplot(log)
        src = src.replace("SCALE=1\n", "SCALE=0.002\n", 1)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            exec(compile(src, path, "exec"), {"__name__": "__main__"})
        # Only block-colour changes count as edges; extra show_screen calls do not
        flips = sum(1 for a, b in zip(log, log[1:]) if a != b)
        status = "ok  " if flips == want else "FAIL"
        ok &= flips == want
        print("%s %-12s %3d lines, %2d tests, %3d edges (want %d)" %
              (status, name, len(lines), len(tests), flips, want))
    return ok


def synth_video(path, edges, fps=60.0, tau=0.012, w=320, h=240):
    """Render a screen whose block follows `edges` with LCD lag and camera noise."""
    rng = np.random.default_rng(1)
    dur = edges[-1] + 1.5
    n = int(dur * fps)
    proc = subprocess.Popen(
        ["ffmpeg", "-v", "error", "-y", "-f", "rawvideo", "-pix_fmt", "gray",
         "-s", "%dx%d" % (w, h), "-r", str(fps), "-i", "-",
         "-c:v", "libx264", "-crf", "18", "-pix_fmt", "yuv420p", path],
        stdin=subprocess.PIPE)
    level = 1.0
    target_at = lambda t: (sum(1 for e in edges if e <= t) % 2) == 0
    sub = 20
    for i in range(n):
        acc = 0.0
        for k in range(sub):  # integrate over the exposure window
            t = (i + k / sub) / fps
            target = 1.0 if target_at(t) else 0.0
            level += (target - level) * (1 - np.exp(-1 / (fps * sub) / tau))
            acc += level
        v = 30 + 190 * acc / sub
        img = np.full((h, w), 200, np.float32)
        img[40:100, 60:180] = v  # the flipping block
        img[150:200, 60:260] = 120 + 40 * np.sin(i / 7)  # unrelated changing area
        img += rng.normal(0, 3, img.shape)
        proc.stdin.write(np.clip(img, 0, 255).astype(np.uint8).tobytes())
    proc.stdin.close()
    proc.wait()


def check_analyzer(script):
    path = os.path.join(ROOT, "calc", script)
    _, tests = analyze.load_script(path)
    phases = analyze.load_phases(path)
    random.seed(2)
    redraw = 0.35   # white block redraw
    white = 0.025   # white redraw is this much slower than black, as measured
    truth = {}
    t = 2.0
    edges = [t]
    for test in tests:
        per_iter = random.uniform(1.0, 4.0) / test["n"]  # 1-4 s phases
        truth[test["name"]] = per_iter
        for m in phases:
            ends_white = len(edges) % 2 == 1
            t += per_iter * m * test["n"] + 0.004 + redraw - (0 if ends_white else white)
            edges.append(t)
    edges.append(t + redraw)

    with tempfile.TemporaryDirectory() as d:
        video = os.path.join(d, "synth.mp4")
        synth_video(video, edges)
        frames, times, fps = analyze.read_frames(video, 64, None, None)
        mask, _ = analyze.find_marker(frames, len(phases) * len(tests) + 2)
        signal = frames[:, mask].mean(axis=1)
        found, _, _ = analyze.find_edges(signal, times)
        run, warn = analyze.pick_run(found, len(phases) * len(tests) + 2)
        rows, overhead = analyze.analyze(tests, run, phases)

    worst = 0.0
    for name, per_iter in truth.items():
        err = abs(rows[name]["per_iter_us"] / (per_iter * 1e6) - 1)
        worst = max(worst, err)
    edge_err = np.abs(np.array([e[0] for e in run]) - np.array(edges))
    print("%s synthetic 60 fps video: %d edges, worst edge error %.1f ms "
          "(includes LCD lag), worst per-iter error %.3f%%, redraw %.1f ms (true %.0f)" %
          (script, len(run), edge_err.max() * 1e3, worst * 100, overhead * 1e3, redraw * 1e3))
    if warn:
        print("WARN", warn)
    return worst < 0.01


def check_series(script):
    """bm_tuple-style video whose per-op cost drifts and steps between blocks."""
    _, sections = series.load_blocks(os.path.join(ROOT, "calc", script))
    random.seed(3)
    redraw = {True: 0.23, False: 0.205}
    truth = []
    t = 2.0
    edges = [t]
    cost = 1.3e-3
    for s in sections:
        for b in range(s["blocks"]):
            ops = s["n"] * s["unroll"]
            cost = cost * random.uniform(0.97, 1.04) if ops else cost
            truth.append(cost * 1e6 if ops else None)
            t += cost * ops + redraw[len(edges) % 2 == 1]
            edges.append(t)
    edges.append(t + redraw[True])

    with tempfile.TemporaryDirectory() as d:
        video = os.path.join(d, "synth.mp4")
        synth_video(video, edges)
        frames, times, _ = analyze.read_frames(video, 64, None, None)
        count = series.edge_count(sections)
        mask, _ = analyze.find_marker(frames, count)
        found, _, _ = analyze.find_edges(frames[:, mask].mean(axis=1), times)
        run, warn = analyze.pick_run(found, count)
        rows, _ = series.analyze_blocks(sections, run)
    # Blocks with almost no work (free) can't be timed relative to their size
    errs = [abs(r["us_per_op"] / want - 1) for r, want in zip(rows, truth)
            if want and want * r["ops"] > 1e5]
    print("%s synthetic 60 fps video: %d blocks, median per-block error %.2f%%, worst %.2f%%" %
          (script, len(rows), np.median(errs) * 100, max(errs) * 100))
    if warn:
        print("WARN", warn)
    return np.median(errs) < 0.01 and max(errs) < 0.03


if __name__ == "__main__":
    a = check_scripts()
    b = (check_analyzer("bm_core.py") & check_analyzer("bm_float.py")
         & check_series("bm_tuple.py"))
    print("ALL OK" if a and b else "FAILURES")
    sys.exit(0 if a and b else 1)
