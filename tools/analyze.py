#!/usr/bin/env python3
"""Measure fx-CG100 benchmark timings from a phone video of the screen.

Each calc/bm_*.py script flips a black/white block in the top-left of the
screen between timed phases. This tool finds those flips in the video,
times them to sub-frame precision, and turns the intervals into per-op costs.

    python3 tools/analyze.py VIDEO --script calc/bm_core.py
    python3 tools/analyze.py VIDEO --snapshot frame.png --at 5

Needs ffmpeg/ffprobe on PATH and numpy.
"""
import argparse
import ast
import csv
import json
import os
import subprocess
import sys
import tempfile

import numpy as np


def load_script(path):
    """Read SCALE and the test table T from a bm_*.py file without running it."""
    tree = ast.parse(open(path).read(), path)
    scale = 1
    tests = None
    for node in tree.body:
        if not isinstance(node, ast.Assign) or len(node.targets) != 1:
            continue
        target = node.targets[0]
        if not isinstance(target, ast.Name):
            continue
        if target.id == "SCALE":
            scale = ast.literal_eval(node.value)
        elif target.id == "T" and tests is None:
            # The first table: bm_bigint has a second stage, read by tools/bigint.py
            tests = []
            for elt in node.value.elts:
                name, _, n, unroll, base = elt.elts
                tests.append({
                    "name": ast.literal_eval(name),
                    "n": ast.literal_eval(n),
                    "unroll": ast.literal_eval(unroll),
                    "base": ast.literal_eval(base),
                })
    if tests is None:
        sys.exit("no test table T found in " + path)
    for t in tests:
        # Same rounding as run() on the calculator
        t["n"] = max(1, int(t["n"] * scale))
    return scale, tests


def load_phases(path):
    """Phase multipliers from run()'s `for m in (n,2*n,...)`: [1, 2] or [1, 2, 2, 1]."""
    for node in ast.walk(ast.parse(open(path).read(), path)):
        if (isinstance(node, ast.For) and isinstance(node.target, ast.Name)
                and node.target.id == "m" and isinstance(node.iter, ast.Tuple)):
            return [e.left.value if isinstance(e, ast.BinOp) else 1 for e in node.iter.elts]
    sys.exit("no `for m in (...)` phase loop found in " + path)


def probe(video):
    out = subprocess.run(
        ["ffprobe", "-v", "error", "-select_streams", "v:0",
         "-show_entries", "stream=width,height,avg_frame_rate",
         "-of", "json", video],
        check=True, capture_output=True, text=True).stdout
    s = json.loads(out)["streams"][0]
    num, den = s["avg_frame_rate"].split("/")
    return s["width"], s["height"], float(num) / float(den)


def read_frames(video, width, start, end):
    """Decode to small grayscale frames plus their presentation timestamps."""
    w, h, fps = probe(video)
    height = max(2, int(round(h * width / w / 2)) * 2)
    trim = []
    if start:
        trim += ["-ss", str(start)]
    if end:
        trim += ["-to", str(end)]
    with tempfile.NamedTemporaryFile("w+", suffix=".log") as log:
        proc = subprocess.Popen(
            ["ffmpeg", "-v", "info", "-nostats", "-copyts"] + trim +
            ["-i", video, "-an", "-fps_mode", "passthrough",
             "-vf", "scale=%d:%d,format=gray,showinfo" % (width, height),
             "-f", "rawvideo", "-"],
            stdout=subprocess.PIPE, stderr=log)
        raw = proc.stdout.read()
        proc.wait()
        if proc.returncode:
            sys.exit("ffmpeg failed decoding " + video)
        log.seek(0)
        times = [float(line.split("pts_time:")[1].split()[0])
                 for line in log if "pts_time:" in line]
    frames = np.frombuffer(raw, np.uint8).reshape(-1, height, width)
    if len(times) != len(frames):
        sys.exit("timestamp count %d != frame count %d" % (len(times), len(frames)))
    return frames, np.array(times), fps


def find_marker(frames, expected=None, chunk=4096):
    """The flipping block: high-contrast pixels that sit at one of two levels
    (not fading or flickering in between) and switch between them most often.
    Other screen areas (test drawing, glare) change brightness too, but only
    a few times or without two clean levels. If the expected number of
    edges is known, pixels flipping a very different number of times (e.g.
    flicker from repeated show_screen()) are ruled out."""
    lo = frames.min(axis=0).astype(np.float32)
    hi = frames.max(axis=0).astype(np.float32)
    s = np.zeros(frames.shape[1:])
    s2 = np.zeros(frames.shape[1:])
    for i in range(0, len(frames), chunk):
        f = frames[i:i + chunk].astype(np.float32)
        s += f.sum(axis=0)
        s2 += (f * f).sum(axis=0)
    mean = s / len(frames)
    std = np.sqrt(np.maximum(s2 / len(frames) - mean * mean, 0))
    mid = (lo + hi) / 2
    half = np.maximum((hi - lo) / 2, 1)
    flips = np.zeros(frames.shape[1:], np.int64)
    extreme = np.zeros(frames.shape[1:])  # mean distance from mid, 1 = always at an end
    bright = np.zeros(frames.shape[1:])   # fraction of time above mid
    prev = frames[0] > mid
    for i in range(0, len(frames), chunk):
        f = frames[i:i + chunk]
        b = f > mid
        flips += (b[0] != prev) + (b[1:] != b[:-1]).sum(axis=0)
        prev = b[-1]
        extreme += (np.abs(f.astype(np.float32) - mid) / half).sum(axis=0)
        bright += b.sum(axis=0)
    extreme /= len(frames)
    bright /= len(frames)
    candidate = ((std >= 0.3 * std.max()) & (extreme >= 0.75)
                 & (bright > 0.15) & (bright < 0.85))
    if expected:
        candidate &= np.abs(flips - expected) <= 0.25 * expected + 2
    if not candidate.any():
        sys.exit("no two-level flipping area found; pass --roi")
    flips[~candidate] = 0
    mask = flips >= 0.7 * flips.max()
    ys, xs = np.nonzero(mask)
    return mask, (xs.min(), ys.min(), xs.max() + 1, ys.max() + 1)


def roi_mask(shape, roi):
    h, w = shape
    x, y, rw, rh = roi
    mask = np.zeros(shape, bool)
    mask[int(y * h):int((y + rh) * h), int(x * w):int((x + rw) * w)] = True
    return mask


def find_edges(signal, times):
    """Sub-frame times where the block crosses 50% brightness, with hysteresis."""
    lo, hi = np.percentile(signal, 2), np.percentile(signal, 98)
    if hi - lo < 10:
        sys.exit("block barely changes brightness (%.1f..%.1f): wrong ROI?" % (lo, hi))
    s = (signal - lo) / (hi - lo)
    edges = []
    state = s[0] > 0.5
    for i in range(1, len(s)):
        if state and s[i] < 0.35 or not state and s[i] > 0.65:
            # Walk back to the frame pair straddling 50% and interpolate
            j = i
            while j > 0 and (s[j - 1] > 0.5) != state:
                j -= 1
            j = max(j, 1)
            a, b = s[j - 1], s[j]
            frac = (0.5 - a) / (b - a) if b != a else 0.5
            t = times[j - 1] + frac * (times[j] - times[j - 1])
            state = not state
            edges.append((t, "dark" if not state else "light"))
    return edges, lo, hi


def pick_run(edges, count):
    """Choose `count` consecutive edges forming one run (first edge goes dark,
    last interval is the short marker-only one)."""
    if len(edges) == count and edges[0][1] == "dark":
        return edges, None
    best = None
    for i in range(len(edges) - count + 1):
        win = edges[i:i + count]
        if win[0][1] != "dark":
            continue
        iv = np.diff([e[0] for e in win])
        score = iv[-1] / np.median(iv)
        if best is None or score < best[0]:
            best = (score, win)
    if best is None:
        sys.exit("found %d edges, need %d for this script" % (len(edges), count))
    return best[1], "found %d edges, expected %d; picked the most plausible run" % (len(edges), count)


def analyze(tests, edges, phases=(1, 2)):
    """Per-iteration cost of each test.

    Phases ending on a white block take `delta` longer than ones ending on
    black (the white redraw is slower). With phases N,2N,2N,N each length ends
    once on each colour, so delta cancels. With N,2N it is estimated per run
    from the average fixed cost of all tests minus the final white redraw.
    """
    times = [e[0] for e in edges]
    iv = np.diff(times)
    overhead = iv[-1]  # final white redraw, no work
    p = len(phases)
    rows = {}
    for k, t in enumerate(tests):
        ph = iv[p * k:p * k + p]
        if p == 4:
            i1, i2 = (ph[0] + ph[3]) / 2, (ph[1] + ph[2]) / 2
            delta = ph[0] - ph[3]
        else:
            i1, i2 = ph
            delta = None
        fixed = 2 * i1 - i2 + (delta / 2 if p == 4 else 0)  # white-ending redraw
        rows[t["name"]] = dict(t, i1=i1, i2=i2, delta=delta, fixed_s=fixed)
    if p == 2:
        delta = np.mean([r["fixed_s"] for r in rows.values()]) - overhead
        for r in rows.values():
            r["delta"] = delta
            r["fixed_s"] -= delta  # now comparable with the white redraw
    for r in rows.values():
        work = r["i2"] - r["i1"] + (r["delta"] if p == 2 else 0)
        r["per_iter_us"] = work / r["n"] * 1e6
    for r in rows.values():
        base = rows.get(r["base"])
        net = r["per_iter_us"] - (base["per_iter_us"] if base else 0)
        r["per_op_us"] = net / r["unroll"]
    return rows, overhead


def main():
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("video")
    ap.add_argument("--script", help="calc/bm_*.py that was run in this video")
    ap.add_argument("--roi", help="manual block region as fractions x,y,w,h of the frame")
    ap.add_argument("--start", type=float, help="ignore video before this many seconds")
    ap.add_argument("--end", type=float, help="ignore video after this many seconds")
    ap.add_argument("--width", type=int, default=64, help="analysis width in pixels")
    ap.add_argument("--out", default="results", help="directory for results")
    ap.add_argument("--note", default="", help="free text saved with results (battery, OS...)")
    ap.add_argument("--snapshot", help="just save one frame as PNG (use with --at)")
    ap.add_argument("--at", type=float, default=1.0, help="snapshot time in seconds")
    ap.add_argument("--dump-signal", help="write per-frame time,brightness CSV here")
    a = ap.parse_args()

    if a.snapshot:
        subprocess.run(["ffmpeg", "-v", "error", "-y", "-ss", str(a.at), "-i", a.video,
                        "-frames:v", "1", a.snapshot], check=True)
        print("wrote", a.snapshot)
        return
    if not a.script:
        ap.error("--script is required")

    scale, tests = load_script(a.script)
    phases = load_phases(a.script)
    frames, times, fps = read_frames(a.video, a.width, a.start, a.end)
    if a.roi:
        mask = roi_mask(frames.shape[1:], [float(v) for v in a.roi.split(",")])
        box = None
    else:
        flips = len(phases) * len(tests) + 2
        mask, box = find_marker(frames, flips)
    signal = frames[:, mask].mean(axis=1)
    if a.dump_signal:
        np.savetxt(a.dump_signal, np.column_stack([times, signal]),
                   delimiter=",", header="time_s,brightness", comments="")

    edges, lo, hi = find_edges(signal, times)
    run, warning = pick_run(edges, len(phases) * len(tests) + 2)
    rows, overhead = analyze(tests, run, phases)

    h, w = frames.shape[1:]
    print("video  %s  %.2f fps, %d frames" % (a.video, fps, len(frames)))
    if box:
        print("block  x %.2f-%.2f  y %.2f-%.2f of frame (auto)" %
              (box[0] / w, box[2] / w, box[1] / h, box[3] / h))
    print("levels dark %.0f  light %.0f" % (lo, hi))
    if warning:
        print("WARN  ", warning)
    print("script %s  SCALE=%s  phases %s  run %.3f s  white redraw %.1f ms\n" %
          (a.script, scale, ",".join("%dN" % m for m in phases),
           run[-1][0] - run[0][0], overhead * 1e3))
    print("%-8s %8s %9s %9s %11s %10s %9s %9s" %
          ("test", "n", "N(s)", "2N(s)", "us/iter", "us/op", "fixed(ms)", "w-b(ms)"))
    for r in rows.values():
        flag = ""
        work = r["i2"] - r["i1"]
        if work < 3.0:
            # Screen refresh (~16 ms) snaps both edges of the difference
            flag = "  <- short phase, ~%.1f%% error" % (100 * 0.016 / max(work, 1e-3))
        elif abs(r["fixed_s"] - overhead) > 0.05 * r["i1"] + 0.02:
            flag = "  <- fixed cost far from block redraw"
        print("%-8s %8d %9.3f %9.3f %11.3f %10.3f %9.1f %9.1f%s" %
              (r["name"], r["n"], r["i1"], r["i2"], r["per_iter_us"],
               r["per_op_us"], r["fixed_s"] * 1e3, r["delta"] * 1e3, flag))
    if len(phases) == 2:
        print("\n(w-b: white redraw minus black redraw, estimated for the whole run\n"
              " and added back to each 2N-N difference)")
    if "for" in rows and "for2" in rows:
        d = rows["for2"]["per_iter_us"] / rows["for"]["per_iter_us"] - 1
        print("\ndrift  for2 vs for: %+.2f%%" % (d * 100))

    os.makedirs(a.out, exist_ok=True)
    name = os.path.splitext(os.path.basename(a.script))[0]
    path = os.path.join(a.out, "results.csv")
    new = not os.path.exists(path)
    with open(path, "a", newline="") as f:
        wr = csv.writer(f)
        if new:
            wr.writerow(["script", "video", "note", "scale", "test", "n", "unroll", "base",
                         "phase_n_s", "phase_2n_s", "us_per_iter", "us_per_op",
                         "fixed_ms", "redraw_ms", "fps", "white_minus_black_ms", "phases"])
        for r in rows.values():
            wr.writerow([name, os.path.basename(a.video), a.note, scale, r["name"], r["n"],
                         r["unroll"], r["base"] or "", "%.5f" % r["i1"], "%.5f" % r["i2"],
                         "%.4f" % r["per_iter_us"], "%.4f" % r["per_op_us"],
                         "%.2f" % (r["fixed_s"] * 1e3), "%.2f" % (overhead * 1e3),
                         "%.3f" % fps, "%.2f" % (r["delta"] * 1e3),
                         "-".join(str(m) for m in phases)])
    print("\nappended to", path)


if __name__ == "__main__":
    main()
