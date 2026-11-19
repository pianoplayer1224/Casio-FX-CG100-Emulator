# fx-CG100 emulator

Measured on an fx-CG100 running OS 02.10.0202.

Runs calculator Python scripts on Linux with the fx-CG100's MicroPython,
`casioplot` screen and speed. It is the real MicroPython v1.9.4 (the
calculator's version) built as a 32-bit program, with a timing model fitted
to the filmed benchmarks in `../results/`.

```bash
emu/port.sh restore                # fresh clone only: fetch MicroPython v1.9.4, apply our changes
emu/build.sh                       # once (needs gcc -m32 and SDL2)
emu/cg100 calc/bm_ref.py           # window + calculator speed
emu/cg100 --fast SCRIPT.py         # as fast as the PC can (signals SIGRTMIN / SIGRTMIN+1
                                   # switch fast mode on / off while it runs)
emu/cg100 --headless SCRIPT.py     # no window
```

Compatibility: all 13 games in github.com/ayush-jha-ai/Casio-CG100-Games
start and run without errors.

The window shows the whole 384×216 screen: status bar, then the shell or
casioplot's canvas. `print()` output goes to the shell (and the terminal).
Type at the PC keyboard to answer `input()`, and after the script at the
shell's `>>>` prompt, which keeps the script's names (the calculator runs
a script as `from NAME import *`). A line typed in the terminal works too.
A drawing stays on screen after the script ends until a key is pressed,
then the shell shows. Esc is [AC]: it stops the script. Close the window
to quit.

Git: `micropython/` is upstream MicroPython with its own `.git`, so the
project repo ignores it. Our changes are tracked as a copy of the port in
`port/cg100/` and the core diff in `patches/py-cg100.patch`. Keep editing in
`micropython/` as before, then run `emu/port.sh save` before committing
(`emu/port.sh check` says whether the copy is behind).

A script with a line over 255 characters is refused before it runs:
"Invalid Data Size" and the line's number and length appear in the window and
the terminal, and the exit status is 1. An imported module with such a line
raises `ImportError`. The 1,743-character refusal is confirmed on the
calculator; the limit of 255, imports and how characters are counted are not
(see [LIMITATIONS.md](LIMITATIONS.md)).

## How it works

| Part | File |
|---|---|
| MicroPython 1.9.4, 32-bit, 1029 KB heap, pystack (recursion depth 97), byte strings, no `type.__name__`; modules `builtins`, `math`, `random`, `casioplot` built in, `turtle` and `matplotlib.pyplot` as Python files in `lib/`; the calculator's missing builtins and math functions left out (`MICROPY_CG_NAMES`) | `micropython/` (v1.9.4 tag), `micropython/ports/cg100/` |
| Changes to MicroPython's core (counters, tuple size) | `patches/py-cg100.patch` (already applied) |
| `casioplot`: 384×192 RGB565 canvas, `draw_string`, `getkey` | `micropython/ports/cg100/modcasioplot.c` |
| Screen: status bar, shell, canvas hand-over | `micropython/ports/cg100/cgscreen.c` |
| `turtle`, `matplotlib.pyplot` (unverified, see below) | `lib/` |
| Timing model | `micropython/ports/cg100/cgtime.c`, `costs.txt` |
| Screen window (separate 64-bit SDL2 program) | `viewer.c` |
| Cost fitting | `fit.py` |

**Timing.** The interpreter counts events: each bytecode, each binary op by
number type (small int, float, big int, bool, other), calls by kind, each
builtin and `math`/`casioplot` function, attribute and subscript access by
object type, loop steps by iterable, heap allocations, allocation-table
scanning, garbage collections and the heap blocks each one scans
(`gc_mark`), bytes converted by `int.to_bytes`/`int.from_bytes` on big
ints (`int_bytes`), pixels, characters drawn and printed.
Virtual time = Σ count × cost, and the interpreter sleeps to keep it in
step with the clock. Costs (µs) are in `costs.txt`. Two costs are measured
directly rather than fitted:

- Compiling source: 12.4 µs per character (`lex_char`), from importing a
  76 KB data module in 0.98 s (Bad Apple `bench.py`, stopwatch).
- `show_screen()` sends only the canvas rows drawn on since the last
  call: 38.9 µs if anything was drawn (`show_any`) plus 52.2 µs per row
  (`show_row`), on top of the ~27 µs call. Measured by `calc/bm_show2.py`
  (bm_core_videos/15, 3 films agreeing within 1%): one pixel then show
  140 µs, 2 rows 205 µs, 8 rows 591 µs, all 192 rows 10.1 ms more than
  drawing alone; all within 0.5% here. A second show with nothing drawn
  costs only the call; how much of a row was drawn on doesn't matter,
  nor whether the rows are next to each other (Bad Apple's film tracks
  best without that). `draw_string()` marks each character's whole cell
  (10 rows for small), which makes `bm_show`'s small "A" then show 692 µs
  (filmed 702). A wait for an LCD transfer (tried first) is ruled out:
  draw, show, then 2–12 ms of work costs the same extra ~0.1 ms each time.
- `get_pixel()` reads RGB565 back with the bits shifted up (red →
  248, 0, 0; (250, 250, 250) → (248, 248, 248)), except that 0xFFFF reads
  (255, 255, 255): white, (248, 252, 248) and (255, 255, 254) all read
  back as 255s. Colour values over 255 count as 255 (`calc/cgcheck3.py`,
  all photographed).

**Memory.** The calculator's tuples take more heap than stock MicroPython's
(bm_tuple: 1–3 items use 2 heap blocks, 8 items use 4), so tuples are padded
by 12 bytes (`MICROPY_CG_TUPLE_PAD`). MicroPython's allocator only moves its
"next free block" hint on single-block allocations, so each tuple scans past
every tuple made since the last garbage collection. The model charges
0.2016 µs per allocation-table byte scanned, from the measured slope. This
reproduces the calculator's tuple cost ramp and its reset at each collection
without special-casing tuples.

The calculator's largest single allocation is 733,153 bytes
(`calc/cgcheck2.py`), so something sits inside its heap; the emulator pins
a 16-byte block 738,400 bytes into its heap (`CG_HEAP_PIN_AT` in `main.c`,
or `CG100_HEAP_PIN=0` to turn it off), which reproduces that figure.

**Strings.** A str result (`+`, `str()`, `join`, ...) is first looked up
among the interned strings, so that an existing constant is reused. A miss
scans every interned string: ~73 µs on the calculator (bm_str: `"q"+"z"`
126 µs, the same on bytes 53 µs; `"abcd"+"efgh"`, whose result is a
literal elsewhere in the script, 42 µs). The emulator counts the strings
compared (`qstr_scan`, 0.1 µs each).

**Shell.** On the calculator the shell is not redrawn while a script runs;
all output appears when it ends, while casioplot drawing stays visible.
print() costs 150 µs per line, 13 µs per separate write (each argument,
separator and line end) and 1.5 µs per character (bm_print).

**Compiler.** `a,b = c,d` is compiled as a stack swap only when the targets
are plain names; `l[j],l[j+1] = ...` builds a tuple, as the calculator does
(bm_gap `swap`: 1.73 ms, predicted within 1% without fitting).

**Font.** `draw_string` uses the calculator's own glyphs and advance
widths, read back on the calculator by `calc/cgglyph.py` (get_pixel, shown
magnified, plus printed advance tables) and decoded from photos by
`tools/glyphdecode.py` into `cgfont_calc.json`; `mkfont.py` builds
`cgfont.h`. Cells: small 7×10, medium 14×17, large 17×23 px, ink starting
1 px right of and level with the draw point; transparent background. Small
and medium are proportional (small 4–8 px, medium 4–15 px), large is fixed
at 18 px. Characters outside ASCII 32–126 draw as `?`. Rendering
`calc/cgfont.py` reproduces the photos of the calculator, including where
lines are clipped at the screen edge.

**Screen.** The emulator keeps the whole 384×216 panel in a shared-memory
file that `viewer` displays. The calculator shows frames on a ~16.1 ms
refresh tick; the viewer polls every 16 ms. Layout, from photos of the
shell and of running scripts (panel 396×224 physical pixels around the
384×216 picture):

- Status bar, rows 0–21: black, battery at the left. While a script runs
  the viewer adds the busy spinner at the right (8 dots, the bright end
  stepping clockwise about every 0.37 s, filmed in bm_str). Rows 22–23
  white; casioplot's canvas is rows 24–215.
- Shell: 9 lines of 38 characters, 10×18 cells from row 24, long lines cut
  off (not wrapped), a scroll bar at x 378–379 once there are more than 9
  lines, the Editor/Shell tabs in rows 190–215. Running a script shows the
  banner (`MicroPython v1.9.4`, `|CASIO COMPUTER CO., LTD.` in slate blue),
  `>>>from NAME import *`, the output, then `>>>` and the cursor.
- The shell is not redrawn while the script runs (as on the calculator):
  output appears when it ends, or when `input()` waits. Once
  `show_screen()` has been called the drawing stays after the script ends
  until a key is pressed.
- Typing (not photographed): the text appears after the prompt with the
  2 px cursor; Backspace/Delete delete, Left/Right move the cursor, Up/Down
  scroll the shell. A line longer than the screen moves left to keep the
  cursor in view; once entered it is cut like any other line. At `>>>`,
  `if`/`for`/`def` and open brackets continue on a `...` line (no
  auto-indent); an empty line runs the block. Esc cancels the line.
- Time spent waiting for typing or for a key is not the script's time: the
  clock that keeps the emulator at the calculator's speed is paused.
- Shell font (`cgfont_shell`, in `cgfont_calc.json` as size `shell`):
  monospaced 10×18, 2 px strokes, every character read from four photos
  of the shell (one of them `calc/cgshell.py`, the whole set); each
  occurrence aligned to the others and voted. A few single, blurred cells
  were straightened by hand (listed in the json). Rendering
  `calc/cgshell.py` reproduces its photo. The Editor/Shell tab labels are
  casioplot's medium font, which matches them in size and position; the
  arrows and battery are bitmaps taken from the photos.

**Files.** On the calculator `open(name, "w")` (or `"a"`, `"+"`) returns
None (`calc/cgshell.py`), so `.write()` raises AttributeError. The
emulator does the same and creates nothing on the PC.

**turtle and matplotlib.** The calculator has both as Python modules in
its firmware, built on casioplot. `lib/turtle.py` and
`lib/matplotlib/pyplot.py` have exactly the calculator's names
(`calc/cgnames.py`: turtle 71, pyplot 28, matplotlib only `__name__` and
`__path__`, so it is a package without `__init__.py`) and are matched to
a film of `calc/cgturtle.py` and photos of `calc/cgplot.py` and
`cgplot2.py` (bm_core_videos 11, 12). How they work inside is not known:
the internal names (`_draw_turtle`, `turtle_buffer`, `fenetre`,
`color_count`, ...) are the calculator's, their meanings guessed. They
run as Python on casioplot, so their speed comes from the timing model.

- turtle: same geometry as Python's (origin at the canvas centre, y up);
  default pen black, 1 px, speed 5. Its state is as photographed
  (`calc/cginternals.py`, bm_core_videos/14; `calc/cgcheck3.py`, 15):
  colours kept as 0–1 (`pencolor("red")` stores (1, 0, 0),
  `pencolor(1, 0, 0)` the list [1, 0, 0], a tuple as given), and
  `pencolor()` gives the name back when there is one. The 13 names are
  black, white, red, green, blue, yellow, cyan, magenta, orange, purple,
  brown, pink, grey; anything else (`"gray"`, `"Red"`, 0–255 values) is a
  ValueError. `speed()` takes 0–10 (11 and −1 → 0, 2.5 → 2) or the
  standard names; `pensize()` stops at 5. `turtleshapes` holds pixel lists for
  "classic" (the arrowhead) and "turtle", `turtle_data` the current one;
  each pixel is turned to the heading and rounded, repeats dropped (this
  reproduces the photographed `turtle_buffer` exactly). The turtle stays
  drawn at rest, `turtle_buffer` keeping `[x, y, colour]` of what it
  covers; `frame_count` counts pixels moved; `pen_pixels` grows in rings as
  photographed: + at 2, the 3×3 square at 3, ±2 tips at 4, the (2, 1)
  knight's moves at 5. While moving it is shown every 6 px at
  speed 5 and at the end of each `circle()` chord, which reproduces the
  film: star 1.34 s (filmed 1.37), pen-up move 0.38 s (0.35), circle 1.27 s
  (1.24); other speeds are scaled, unfilmed. `write()` uses the small
  font, starting at the turtle, just below it. No `color()`, `dot()`,
  `colormode()` or `done()`. `from turtle import *` also brings `sin`,
  `cos`, `sqrt`, `atan2`, `pi` and `casioplot`, as on the calculator.
- pyplot state as photographed: `lines` `[x0, y0, x1, y1, colour]`,
  `points` `[x, y, colour]`, `textes` `[x, y, text]`, each starting as
  `[[]]` (`plot()`/`text()` replace the empty entry, `scatter()` keeps
  it); automatic colours are letters from `color_auto` (b r g m k c y),
  one per call, a bar's three lines sharing one; `extrem` starts 0–1 and
  is replaced by the first data; `available_colors` and
  `COLOR_DECO_CHAR` (`o . + * -`) are lists; `limits` is the list
  `[40, 165, 384, 0]`; `color_grid` is `'grey'`.
- pyplot calls as photographed (`calc/cgcheck3.py`): a colour is a name or
  letter from `available_colors`, kept as given; a letter plus one marker
  (`"ro"`) keeps the letter; anything else (`"r--"`) is a ValueError, and
  a non-string third argument an Exception. `scatter(x, y)` and
  `text(x, y, s)` take nothing more. `axis()` returns a tuple; with no
  arguments, once something is plotted, it gives the data's range plus
  5% each side, which `axis("auto")` also stores in `fenetre`. `hist`
  returns `(counts, edges)` and draws each bin's left side, top and right
  side, repeats dropped. `arrow` adds a head: a triangle `head_width`
  (default 0.003) across and `head_length` (1.5×) long, and 59 lines
  filling it (their order is a guess).
- pyplot drawing: the window is 0–1 on both axes until `axis()` sets it (no
  autoscaling even though `axis()` reports the data's range), mapped to x
  45–383, y 165–5. Axes on the left and bottom only, drawn after the
  data; outside ticks from the window's minimum in steps of 1, 2.5 or
  5×10ⁿ, the smallest giving at most 6 intervals (0–1: 0.25; −3…3: 1;
  −1…9: 2.5, as photographed); labels in the small font, grid light
  grey-blue. Calls without a colour take the next automatic colour. `scatter` draws 5 px `+` marks,
  bars are open at the bottom, `arrow` is black (its head is too small to
  see at the default size), `text` has
  its top left at the point. No `clf()`/`close()`.

## Outside measurements

Costs not filmed here come from others' measurements (`EXTERNAL` in
`fit.py`): `getkey()` with no key down costs ~8.2 ms per call, ~20 µs with
a key held (Cemetech t=20274). Other published figures
to check the emulator against, once their scripts are found: Critor's
seuil(0.008) 3.57 s and primality test 1.53 s on the Math+, full-screen
set_pixel fill ~2 s (90+E), CalcLoverHK's factorisation of 96835724136209
in 114 s and Monte-Carlo π in 148 s. Hardware: SH4 (SH7305-like) at
~118 MHz, no FPU (software doubles), 8 MiB SDRAM.

## Fitting the costs

```bash
python3 emu/fit.py           # refit costs.txt from results/*.csv and report
python3 emu/fit.py --check   # report with the current costs.txt
```

`fit.py` runs each benchmark script in the emulator, records every counter
at each block flip, applies the same N/2N differencing as
`tools/analyze.py`, and solves for costs (bounded least squares on relative
error, with a weak pull towards a typical value per event group). `bm_ref`
(whole programs) is held out to measure accuracy on code the fit never saw.
Scripts without filmed results are skipped; a new script needs adding to
`FIT` before filming it changes anything.

### Accuracy (2026-11-06, refitted with `bm_bigint`, batch 18)

| | median error | worst |
|---|---|---|
| Fitted microbenchmarks (core, float, call, data, plot, gap, str, print, mac, bytes, bigint) | 0.7% | 16.5% (`bm_bigint` `add256`) |
| `bm_bigint` big-int sizes | | 16-digit within 2%, 64-digit +5–7%, 256-digit −13% to −17% |
| bm_tuple blocks | 1.4% | 13% (blocks near a GC) |
| Never fitted: `tnew`, `spxt`, `gpx`, `swap` (all tuple-heavy) | | within ~6% |
| `bm_mac` `step` (held out, one token of a small GPT) | | −2.4% |
| Held-out programs (`bm_ref`) | 1.5% | 18% |
| All held out (`bm_ref`, `bm_show`, `bm_show2`) | 1.1% | 22% |
| `bm_show2` (held out) | 0.4% | 2.2% |
| `bm_show` (held out) | 1.2% | 22% (`pxshow2`, a short noisy phase; `bm_show2` measures it at 168.9 µs, 168.4 here) |
| Bad Apple (calc_v1, 2994 frames, filmed) | 217.45 s vs 217.07 s (+0.2%, from event counts) | drift along the video rms 0.13 s after scaling |

Bad Apple was within 0.02% with the old show cost (62.8 µs per row, fitted
to this film), but that hid an error elsewhere: `bm_show2` measures the
show cost directly. Counting name lookups (below) then brought Bad Apple's
`bench.py` decode stage from 7.33 s to 7.72 s (calculator 7.66 s).

**Name lookups.** A builtin's name is searched for in the script's globals
first, and MicroPython's tables fill up completely before growing, so a miss
can walk most of the table. `len` costs 17 µs with 2 slots walked per lookup
(`bm_bytes`) and 44 µs with 118 (`bm_mac`). The emulator counts the slots
(`map_probe`, 0.236 µs each); its name hashes reproduce the calculator's
walks. `bytes[i]` and `len(bytes)` don't depend on size (`bm_bytes`).

**Big ints (batch 18).** `bm_bigint` showed the calculator has
`to_bytes`/`from_bytes`, and a 64×64 matrix-vector multiply with big ints
takes 20.4 ms against 77.2 ms the plain way. With ~500 KB live it takes
28.4 ms, because each collection scans more of the heap; that phase (`mvb2`)
is the only one setting `gc_mark` (1.03 µs per block), so the cost has no
independent check yet. The cost per digit doesn't scale like the
calculator's: 256-digit adds and multiplies run 13–17% fast here.

Held-out details: series, prime, trig, text within ~2%; sieve −4.4%;
mandel −6%; queens +8%, bubble +18%. Fitted outliers: attribute access
(`attr` −10%, `modat` +12%) and long strings (`c64` −7%: the calculator
charges more per byte than the model).

## Keys and builtins

- `getkey()` codes: row×10+column, confirmed by `cgfont.py` page 3 (the
  calculator reports 12–16, 21–26, 31–36, 41–46, 51–56, 61–64, 71–75,
  81–85, 91–95; AC stops the script). Window keys: arrows, Space = OK,
  Enter = EXE, Backspace = back, 0–9, `.`, Delete = DEL, `* / + -`,
  Esc = AC (DEL, operators and point placed from the keypad layout).
  `getkey()` returns None with no key down. AC stops a script anywhere,
  not only in `getkey()` (KeyboardInterrupt). Typed letters reach
  `input()` and `>>>`, not `getkey()`.
- Builtins and math match the calculator's (`calc/cgcheck.py`,
  `cgcheck2.py`: 84 builtins, 25 math names). Missing there and here:
  enumerate, filter, frozenset, reversed, bytearray, help, UnicodeError,
  NotImplemented, StopAsyncIteration, compile, memoryview, property;
  math's isfinite, isinf, isnan, trunc, copysign, degrees, radians, expm1,
  log2, acosh, asinh, atanh, erf, erfc, gamma, lgamma, hypot.

## Not done yet

- turtle shapes other than the default arrow, the values behind turtle's
  colour names other than black, white and the primaries, the order of
  `arrow`'s head lines, whether `axis()` also switches `show()` to the
  data's range, and the automatic colours after the second are not
  photographed.
- How the calculator shows typing is not photographed (long lines, the
  continuation prompt, auto-indent, Up/Down, whether the spinner turns
  while `input()` waits).
- Compile time is one measured point: 12.4 µs per source character, from
  importing a 76 KB module of `b"..."` lines (Bad Apple's `bench.py`
  stage 4, 0.98 s). Ordinary code may cost more per character to compile.
- Tracebacks name the script file directly (`File "x.py"`); the
  calculator, which imports the script, may also show a `<stdin>` line.
- Heap size: `cginfo.py` on the calculator fills memory at 942 KB strings /
  27,097 two-item tuples / 27,138 one-item lists, which a 1010 KB heap
  matches; but the calculator's garbage-collection rhythm in bm_tuple
  matches 1029 KB, and Critor measures 1.029 MB usable on the Graph Math+.
  The emulator uses 1029 KB and fits ~2% more before MemoryError.
- Float boxing: whether the calculator allocates a heap object per float
  (as this build does) is not known; mandel (−6%) hints it may not.
- Timing outliers: queens +15%, bubble +17%, attribute access (−10% /
  +12%), long strings (`c64` −7%).
