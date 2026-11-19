# fx-CG100 Python speed measurements

Timing data from a real fx-CG100, used to tune the speed of a Linux emulator of
its MicroPython + casioplot.

The calculator's Python has no `time` module, so scripts cannot time themselves.
Instead each script flips a black/white block in the top-left of the screen
between timed phases, you film the screen, and `tools/analyze.py` reads the
flips out of the video to sub-frame precision.

## Files

| Path | Purpose |
|---|---|
| `calc/bm_core.py` | loops, integer and big-integer math, local vs global variables |
| `calc/bm_float.py` | float arithmetic, `math` functions |
| `calc/bm_call.py` | function/method calls, attributes, builtins, recursion |
| `calc/bm_data.py` | lists, tuples, dicts, strings, allocation |
| `calc/bm_plot.py` | `set_pixel`, `get_pixel`, `show_screen`, `clear_screen`, `draw_string` |
| `calc/bm_ref.py` | whole programs (sieve, n-queens, mandelbrot...) kept aside to check the emulator |
| `calc/bm_gap.py` | comparisons, closures, `sum()`, swaps, string building: constructs the others miss |
| `calc/bm_print.py` | `print()` to the shell |
| `calc/cginfo.py` | modules, limits, heap size, float format (writes `cginfo.txt` or prints) |
| `calc/cgfont.py` | font charts to photograph, then `getkey()` codes |
| `emu/` | the emulator built from these measurements, see `emu/README.md` |
| `calc/bm_tuple.py` | why building a tuple costs ~1.3–1.9 ms and changes as a script runs |
| `tools/analyze.py` | turns a video into per-op timings, appends to `results/results.csv` |
| `tools/series.py` | per-block timings for `bm_tuple.py`, appends to `results/series.csv` |
| `calc/bm_bigint.py` | big-integer maths, `to_bytes`/`from_bytes`, a 64x64 multiply both ways, then with ~500 KB live |
| `tools/bigint.py` | timings from a `bm_bigint.py` video (two stages), appends to `results/results.csv` |
| `tools/selftest.py` | checks the scripts and analyzer with a synthetic video |

Each test runs at **N** and **2N** iterations; `(time(2N) - time(N)) / N` is the
cost of one iteration with all fixed overhead (block redraw, `show_screen`,
call setup) cancelled out.

Redrawing the block white takes ~15–40 ms longer than black (`w-b` column).
Most scripts run phases in the order N, 2N, 2N, N so each length ends once on
each colour and this cancels exactly. `bm_core` (already recorded) uses N, 2N;
for it the analyzer estimates `w-b` per run and corrects for it. Ops are repeated 10x per loop and the empty `for`
loop cost is subtracted, giving **µs per op**. `for2` repeats the baseline at
the end of each script to catch drift.

## Procedure

1. Copy `calc/*.py` to the calculator over USB (mass storage). Put them in the
   root next to your other scripts.
2. Prop the phone so the whole screen is visible and steady. Lock focus and
   exposure (long-press on the screen in most camera apps). 60 fps is enough;
   120/240 fps slow motion is better. Avoid glare on the block.
3. Restart the Python app, start recording, run one `bm_*.py`. The script
   shows its name and expected edge count, then the block flips. Don't press
   keys until **DONE** appears. Stop recording.
4. Analyze:

   ```bash
   python3 tools/analyze.py VIDEO.mp4 --script calc/bm_core.py --note "OS 2.00, alkaline fresh"
   ```

   If the block is not detected automatically, save a frame and give its
   position as fractions of the frame:

   ```bash
   python3 tools/analyze.py VIDEO.mp4 --snapshot frame.png --at 5
   python3 tools/analyze.py VIDEO.mp4 --script calc/bm_core.py --roi 0.20,0.15,0.30,0.25
   ```

5. Repeat each script 3 times (new video each time). Use the median.

### Getting phase lengths right

The screen only shows a `show_screen()` on its next refresh tick (~16.1 ms,
~62 Hz), so every edge is uncertain by up to ~8 ms no matter how fast the
camera is. Phases need several seconds of work to make that small.

`bm_core.py` is already tuned from real runs. The other scripts still have
guessed counts (too short, probably). For each one:

1. Run it once at the guessed counts and analyze the video (calibration run).
2. Retune it to ~3 s N phases (each test then takes ~18 s over its 4 phases),
   then copy the new file to the calculator:

   ```bash
   python3 tools/summary.py bm_float --retune 3
   ```

3. Move the calibration rows out of `results/results.csv` (e.g. to
   `results/bm_float_calibration.csv`) and do the real runs.

`python3 tools/summary.py bm_core` prints the median and spread across runs.
The analyzer reads the iteration counts from the PC copy of the script, so
keep both copies identical.

### bm_tuple

Building a tuple costs ~1.3–1.9 ms, and the cost per tuple changes from one
phase to the next in a way that repeats exactly between runs. `bm_tuple.py`
flips the block after every block of 1000 tuples (~1.7 s), so the video shows
the cost block by block. Sections compare `(a,a)` over a long run, `(a,)`,
8-item tuples, a constant `(1,2)`, `tuple(list)`, after `gc.collect()`, with
lots of live objects on the heap, and lists `[a,a]` as a control. Idle
sections at both ends measure the block redraw. The screen also shows whether
the `gc` module exists and the free heap at the start and end; note those
numbers with the run. One run takes ~6 minutes.

```bash
python3 tools/series.py VIDEO.mp4 --note "OS 2.00, run 1"
```

### bm_print

`print()` switches the calculator's display from the casioplot screen to
the shell, so `bm_print.py` doesn't use the block. Its marker is the shell
itself: a screenful of `#` lines after every phase, which the next phase's
output scrolls away. Film the shell and analyze only the edges going dark:

```bash
python3 tools/analyze.py VIDEO.mp4 --script calc/bm_print.py --dark-only
```

If the marker isn't found automatically, give `--roi` around the left
half of the shell text.

### Reading the output

- `us/op`: cost of one operation, the number the emulator needs.
- `fixed(ms)` should be close to `block redraw`; a large difference means
  something irregular happened in that test (GC pause, key press).
- `drift`: `for2` vs `for` should be within ~1%.

## Notes

- Existing scripts on the calculator do not affect results; only the running
  script is loaded. Don't keep a file named `casioplot.py`, `math.py` or
  `random.py` on the calculator, since it could shadow the real module.
- Battery type doesn't change CPU speed: the clock comes from a crystal and
  the logic runs from a regulated supply. Avoid nearly flat batteries, and note
  the battery in `--note` so any effect would show up in the data.
- Check the analyzer at any time with `python3 tools/selftest.py`
  (needs `ffmpeg` and `numpy`).
