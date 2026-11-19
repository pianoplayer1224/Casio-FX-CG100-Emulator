# fx-CG100 emulator: limitations

As of 2026-11-19, against an fx-CG100 running OS 02.10.0202. Percentages are
emulator time against the filmed calculator: + means the emulator is too
slow, so the script runs faster on the calculator; − means the emulator is
too fast. What to film or photograph next is in `../TODO.md`.

For anything where exact timing or memory matters, do a final run on the
calculator.

## Scope

- It runs the Python screen only: no menus, file browser or other apps.
- It runs on Linux only.
- Scripts are started from the command line (`emu/cg100 SCRIPT.py`).

## Long lines

The emulator refuses a file with a line over 255 characters, as the calculator
does with "Invalid Data Size". Not all of this rule has been measured:

- **Confirmed:** the calculator (OS 02.10) refused to open a script with a line
  of 1,743 characters. After that line was wrapped, the same script opened and
  ran. Its lines are up to 239 characters and its imported modules' up to 244.
- **Inferred:** the limit of 255. Nothing between 256 and 1,743 has been tried.
  The evidence is that the Bad Apple modules stop at exactly 255 and import
  and run on the calculator, and that Casio's manual gives 255 characters for
  shell input lines.
- **Assumed:**
  - An imported module is refused too, with `ImportError`. The refusal was only
    seen when opening the main script, so the calculator may treat imports
    differently. What it reports for a module is also unknown.
  - The count leaves out the line ending, and counts bytes rather than
    characters. Neither has been checked.
- **Not limited:** the number of lines in a file, and lines typed at the `>>>`
  prompt or passed to `exec()`.

## Speed

Typical code is close: benchmarks never used for fitting have a median error
of about 1%. The known outliers are:

| Area | Benchmark | Error | What it means |
|---|---|---|---|
| Heavy list code | `bm_ref` bubble | +17.7% | May run faster on the calculator |
| Recursion and lists | `bm_ref` queens | +8.1% | May run faster on the calculator |
| Attribute access | `attr` / `modat` | −10.2% / +11.7% | Class-heavy code can be off in either direction |
| Float-heavy loops | `bm_ref` mandel | −6.2% | Leave some margin |
| Long strings | `c64` | −6.6% | Small unless many are built |
| List-heavy sieve | `bm_ref` sieve | −4.5% | Leave some margin |
| Large big ints | `bm_bigint` add256 / mul256 | −16.5% / −12.7% | Arithmetic on ~256-digit ints may be slower on the calculator; 64-digit is +5–7% |
| Bad Apple decode loop | `bench.py` stage 5 | +0.8% (7.72 s vs 7.66 s, stopwatch) | Now close |
| Bad Apple overall | Film, 2994 frames | +0.2% (217.45 s vs 217.07 s, from event counts) | Long programs can still drift by seconds |

- **Name lookups:** only the slots walked in hash tables are charged, at one fitted cost.
  Searching the fixed builtin table isn't charged separately (`map_scan` fits to 0).
- **Compile time:** the 12.4 µs per source character comes from one file, a
  76 KB module of `b"..."` data lines. Importing ordinary code may take longer
  on the calculator.
- **turtle speed:** only the default speed 5 is filmed, and it is within about
  9%. Speeds 0, 1 and 10 are scaled from it and may be well off.
- **turtle `circle()`:** redrawing at each chord fits the film's timing, but
  has not been seen directly.
- **Games:** all 13 GitHub games run without errors, but their speed has not
  been compared with the calculator. Only Bad Apple has been timed as a whole
  program.

- **Garbage collection with a full heap:** the cost per heap block scanned
  (`gc_mark`) comes from one phase of one film (`bm_bigint` `mvb2`, ~500 KB
  live), which has only a few collections, so it is uncertain by about 10%.
  Programs that keep most of the heap full and collect often, such as the
  big-int GPT models, depend on it heavily.

## Memory

- The emulator fits about 2% more data than the calculator. Test on the
  calculator if a script is close to the memory limit.
- `cginfo.py`'s fills suggest a 1010 KB heap, while the garbage collection
  rhythm suggests 1029 KB, which is what the emulator uses.

## Typing and the shell

- **Not tested in the real window:** typing letters has only been tested by
  feeding characters straight to the emulator, because simulated key presses
  don't produce SDL text input.
- **Not filmed, so guessed:**
  - how long lines and prompts over 38 characters are shown
  - the `...` continuation prompt, and that there is no auto-indent
  - what Up, Down and AC do while typing
  - whether the spinner turns while `input()` waits
- **Tracebacks:** they show the script's file path, and the calculator's
  wording may differ, for example with a `File "<stdin>"` line.
- **After a drawing ends:** the emulator returns to the shell on any key; which
  key the calculator needs is not known.
- **Scrolling:** the highlighted line seen in two photos when scrolling up is
  not emulated.

## turtle

- The values behind orange, purple, brown, pink and grey are guessed, so those
  colours may look slightly different.
- Shapes other than the default arrow have not been compared on screen.

## pyplot

- Whether `show()` waits for a key is not photographed, nor whether it keeps
  the plotted data for the next `show()`.
- Whether `axis()` with no arguments makes `show()` use the data's range is not
  known. The emulator assumes not, because `show()` drew 0–1 in the `cgplot`
  photo.
- The order of `arrow`'s 59 head-filling lines is a guess. Their stored numbers
  also differ from the calculator's in the last digits.
- Automatic colours after the second, and how `axis("auto")` and `hist` look on
  screen, are not photographed.

## Screen and fonts

- Large-font `J`, `H`, `I` and `R`: two photo batches disagree, and they are
  left as decoded.
- Shell-font `# W X Y Z ^ _` were straightened by hand from one blurred cell,
  and `y` was moved down a row by judgement.
- These positions may be off by 1–2 pixels:
  - the status bar rows while casioplot runs
  - the Editor/Shell tab outline and rounded corners
  - the spinner's position and dot sizes
- The spinner's step rate (about 0.37 s) is read from one film and is
  approximate.
