# Open items (2026-10-31)

What still needs a photo, a video or more tuning before the emulator
matches the fx-CG100 (OS 02.10.0202). Details of what is already matched
are in `emu/README.md`.

## Next calculator session (batch 19)

Batch 18 (2026-11-06, bm_core_videos/18) filmed `calc/bm_bigint.py` 3 times (read with
`tools/bigint.py`; `to_bytes` and `from_bytes` exist). It is in `FIT`, and added two costs:
`int_bytes` (per byte converted) and `gc_mark` (per heap block scanned in a collection),
the second set only by `mvb2`, so it has no independent check yet. Batches 16 and 17 (2026-11-03, bm_core_videos/16, 17) filmed `calc/bm_mac.py` and
`calc/bm_bytes.py` 3 times each; both are in `FIT`, with `step`, `bl3` and `bl4` held out. Batch 15 (2026-10-31) did `calc/bm_show2.py` (3 films) and `calc/cgcheck3.py`
(its 10 pages). Still to do:

1. `calc/cgcheck3.py` again, to the end: photograph the plot `show()` draws
   after the last page (and whether it waits for a key), then the shell
   (the `after show:` lines and the traceback of the deliberate error).
2. Typing video: `user_files/calc_missop/missing_op.py`, a few answers,
   then at `>>>`: `for i in range(3):`, `print(i)`, an empty line; then
   a line longer than the screen; Up/Down/AC while typing.
3. Flappy Bird (`flappybird.py` from the games repo), film from start
   without pressing anything: the emulator reaches GAME OVER 3.33 s after
   the first frame (13 frames of 248-280 ms). Snake: press 1, nothing
   else: 18 steps of 83 ms (~1.5 s) to GAME OVER.
4. Small pyplot/turtle follow-ups (a new check script): does `axis()` with
   no arguments switch `show()` to the data's range (plot, `axis()`,
   `show()`)? The order of `arrow`'s 59 head lines (print
   `lines[4:10]` rounded). What `pencolor("orange")` etc. store
   (`turtle_color` after each name).

5. Long lines: where is the "Invalid Data Size" limit? Try opening scripts
   with one line of 255, 256, 300, 512 and 1024 characters, and importing a
   module with a 256-character line from a script that opens. The emulator
   assumes 255 for both (`emu/LIMITATIONS.md`).

## Speed: needs new benchmark scripts, then a video

The timing model is within ~1% on most microbenchmarks and ~2.5% median on
whole programs. The worst errors are listed here. Each needs a targeted
`calc/bm_*.py` (block-flip format, N/2N/2N/N phases), filmed and added to
`FIT` in `emu/fit.py`.

| Item | Emulator vs calculator | What would settle it |
|---|---|---|
| `bm_ref` queens | +8% (too slow) | Split its parts: recursion depth, list `[i]` load/store, `abs()`, nested `for` over `range` |
| `bm_ref` bubble | +18% (too slow) | List subscript load/store and compare, with and without the tuple swap |
| Attribute access | `attr` −10%, `modat` +12% | Instance vs class vs module attributes, read vs write, method lookup |
| Long strings | `c64` −7% | `bm_str` with 128- and 256-character results, to get the per-byte cost |
| Float boxing | `mandel` −6% | Float-only loop that allocates nothing else; does a GC ever happen? |
| Compile time | `lex_char` 12.4 µs per source character, from one point: Bad Apple `bench.py` stage 4 (76 KB of `b"..."` lines, 0.98 s, stopwatch). All five stages match within 5% (emulator 1.62, 4.16, 0.08, 0.98, 7.33 s; calculator 1.58, 4.22, 0.07, 0.98, 7.66) | Import a module of ordinary code (defs, expressions) of known size and time it, to see if code compiles slower per character than data |
| Heap size | emulator fits ~2% more | `cginfo.py`'s fills say 1010 KB, but the GC rhythm says 1029 KB; re-run fills one at a time after a fresh start |

## Look and behaviour: needs photos

- Done 2026-10-30 (bm_core_videos/14): the internal values of turtle and
  pyplot, from `calc/cginternals.py`. The libraries now hold their state
  exactly as photographed.
- Done 2026-10-31 (bm_core_videos/15, `calc/cgcheck3.py`): get_pixel
  read-back and clamping, turtle colour names / pen sizes / speeds,
  pyplot colour checks, `axis()` returns, `hist`, `arrow` heads.
- **turtle:**
  - The 0..1 values behind orange, purple, brown, pink, grey (guessed;
    `pencolor()` returns the name, so print `turtle_color` instead).
  - Whether `circle()` really redraws per chord (fits the film's timing;
    a slow-motion video of `circle(60)` would show it).
- **pyplot:**
  - Whether `axis()` with no arguments makes `show()` draw the data's
    range (assumed not: `show()` drew 0..1 in the cgplot photo).
  - The order of `arrow`'s 59 head-filling lines (guessed).
  - What happens after `show()`: are the stored `lines`/`points` kept
    for the next `show()`? Does `show()` wait for a key?
- **Shell:**
  - A script that raises an error: does the traceback show a
    `File "<stdin>"` line?
  - After a casioplot drawing ends: which key brings the shell back
    (any key, EXE, AC)? The emulator assumes any key.
  - The highlighted line when scrolling up through the shell (seen in two
    photos, not emulated; Up/Down just scroll here).
  - Typing, none of it photographed yet. A short video of
    `user_files/calc_missop/missing_op.py` and of a few lines at `>>>`
    would settle:
    - a prompt longer than 38 characters, then typing after it (the
      emulator cuts the prompt like output and moves the line left while
      typing; findun's save-code prompt is 74 characters);
    - the continuation prompt after `for i in range(3):` (`...` guessed),
      and whether it auto-indents (the emulator doesn't);
    - what Up/Down and AC do while typing;
    - whether the spinner turns while `input()` waits (the emulator keeps
      it turning; it stops at `>>>`).
- **Fonts:**
  - Large `J`, `H`, `I`, `R`: the two photo batches disagree; left as
    decoded.
  - Shell glyphs straightened by hand from one blurred cell: `# W X Y Z ^ _`.
    `y` was moved down a row by judgement.
  - The `cgshell.py` photo is the reference for re-checking these.
- **Screen geometry (±1–2 px):**
  - Status bar is black rows 0–21 and rows 22–23 white; is that the same
    while casioplot runs?
  - The Editor/Shell tab bar outline and rounded corners.
  - The spinner's exact position and dot sizes, from video.

## Needs video

- turtle at `speed(0)`, `speed(1)` and `speed(10)`. Only the default speed
  is calibrated (within ~10%). The others are a guessed table in `goto()`,
  scaled with the default when the LCD transfer wait was added.
- Spinner step rate. It's ~0.37 s per step, read from bm_str; a closer shot
  would pin it down.

## Emulator work (no calculator needed)

- Done 2026-10-30: typing in the window answers `input()` and the `>>>`
  prompt after a script (names kept), Esc = AC stops any loop, waits pause
  the speed clock. Checked with `user_files/` (missing_op, findun's
  save code, Bad Apple runs to the end without MemoryError).
- Done 2026-10-30: the 13 games from github.com/ayush-jha-ai/Casio-CG100-Games
  re-run at calculator speed after the show-cost rework: all start, draw
  and play without errors. Frame rates in the emulator: tetris ~105/s,
  space ~67/s, breakout ~52/s, halloween ~38/s, pacman ~20/s,
  flappybird/football ~4/s (whole-screen redraws from Python).

- The bm_mac refit moved cost between events that nearly always occur together:
  `op_call_function` 1.23 to 0 and `set_pixel` 2.2 to 3.5, `fn_float` 51 to 0 and
  `fn_int` 0 to 55, `op_jump` 0.63 to 0. Fitted scripts still match, but programs with
  other ratios may drift, and `bm_mac` `norm` is −7.2%. Tighter priors on `fn_*` might help.

## Tools

- `tools/emushot.py SCRIPT OUTDIR ["typed lines"]`: emulator screenshots
  without a window, for comparing with photos; the lines are typed at each
  `input()` / `>>>`.
- Photo straightening and glyph decoding scripts from this work are in the
  session scratchpad and may be gone. They work like this:
  - Pick the panel corners (396×224 physical pixels around the 384×216
    picture).
  - Measure the local pixel pitch from the LCD dot pattern.
  - Align each 10×18 cell on its own.
  - Vote across occurrences.
