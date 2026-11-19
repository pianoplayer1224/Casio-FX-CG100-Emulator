# Research brief: Casio fx-CG100 MicroPython internals

## Goal

Find public information (docs, forum posts, reverse-engineering notes, source
code, firmware analyses) that explains how Casio's MicroPython on the
**fx-CG100 / fx-1AU Graph / Graph Math+** differs from stock MicroPython
v1.9.4. The findings feed a Linux emulator that already runs stock
MicroPython 1.9.4 (32-bit) with a timing model fitted to filmed benchmarks
of a real fx-CG100. Clues that explain *why* the measurements look the way
they do are worth more than general overviews.

Report sources with URLs, quote the exact relevant sentence or code (short
quotes), and say how confident you are and whether a claim is about the
fx-CG100 itself or a related model (fx-CG50, Graph 90+E, fx-9750GIII,
Graph Math+). Do not guess; mark inference as inference.

## Already known (measured on a real fx-CG100, don't re-research)

- Shell banner: "MicroPython v1.9.4 / CASIO COMPUTER CO., LTD."
- Importable modules: builtins, math, random, casioplot, turtle, matplotlib.
  Not available: cmath, sys, gc, time, os, array, collections, struct,
  micropython, ujson/json, re, io.
- `type(x).__name__` raises AttributeError (MICROPY_CPYTHON_COMPAT off?).
- Strings are bytes: `len('é') == 2`, `chr(9608)` raises ValueError.
- Recursion fails at depth ~97 with "pystack exhausted" (MICROPY_ENABLE_PYSTACK).
- Doubles (not single-precision floats). `random.seed(1)` gives the same
  sequence as stock MicroPython's urandom (yasmarang).
- Heap ~1 MB: ~942 strings of 1000 chars, ~27,100 two-item tuples or
  ~27,100 one-item lists fit before MemoryError.
- Building a tuple costs 20–45 µs plus ~0.1 µs per tuple created since the
  last garbage collection, resetting at each collection (about every 31,000
  tuples). 8-item tuples grow 2× as fast. Lists, `tuple(list)` and strings
  don't show this. Best explanation so far: tuples occupy 2 GC blocks
  (stock 1.9.4: 1 block) and gc_alloc's free-block search restarts from a
  hint that multi-block allocations never advance.
- `l[j],l[j+1]=l[j+1],l[j]` builds a tuple (1.7 ms) while `a,b=b,a` with
  plain names doesn't: Casio's compiler limits the double-tuple-assign
  optimisation to name targets (stock 1.9.4 doesn't).
- CPU: SH4-family (SH7305-like) at ~118 MHz, no FPU (unconfirmed for CG100).
- casioplot: 384×192, RGB565, show_screen() appears on a ~16 ms (~62 Hz)
  refresh; getkey() exists. Shell truncates long lines.

## Questions, most important first

1. **Object sizes / GC block layout.** Why would tuples take 2 GC blocks?
   Look for: Casio's MicroPython build configuration, MICROPY_OBJ_REPR,
   MICROPY_BYTES_PER_GC_BLOCK, object header changes, a modified
   mp_obj_tuple_t, or anything about memory layout on Casio calculators.
   Do other objects (instances, closures, dicts, sets, floats) also grow?
2. **Float representation.** Are floats boxed heap objects (REPR_A) or
   packed (REPR_C/REPR_D) on Casio calculators? Any software-float library
   used (SH4 without FPU)?
3. **Casio's MicroPython source or config.** Has Casio published its port
   source (GPL/MIT obligations, an "open source" page on support.casio.com
   or edu.casio.com), a license notice listing MicroPython commits, or
   mpconfigport-style settings? Has anyone extracted it from firmware
   (OS update files, .g3a/.bin dumps)?
4. **Compiler/runtime modifications** beyond stock 1.9.4: tuple-assign
   change, removed features, added features, backported patches.
5. **Heap and GC details:** exact heap size, gc.threshold settings, whether
   the C stack is scanned conservatively, pystack size.
6. **Full builtin lists:** dir() of builtins, math, random, casioplot,
   turtle, matplotlib on the fx-CG100 (or Graph Math+ / fx-CG50 3.x, which
   may share the port). Exact getkey() key codes and semantics (held key
   vs press, AC behaviour). draw_string font sizes/metrics.
7. **Shell behaviour:** print()/input() speed, scrolling, line truncation,
   whether printing switches away from the casioplot screen.
8. **Hardware of the fx-CG100:** exact CPU/SoC, clock, RAM, LCD controller
   and refresh. Teardowns, FCC filings, datasheets.
9. **Existing emulators or benchmarks** for the fx-CG100 / Graph Math+ /
   fx-CG50 Python (performance comparisons, speed tests, timing tables).

## Where to look

- Planète Casio (planet-casio.com): forums, "Python" topics, reverse
  engineering (they decompile Casio OSes; search for CG100, Graph Math+,
  "fx-1AU", MicroPython, casioplot, getkey).
- TI-Planet (tiplanet.org): Python comparisons across calculators, often
  with heap sizes, recursion limits, module lists, benchmarks.
- Cemetech forums, Casio-related GitHub repos (search "casioplot",
  "fx-CG100", "Graph Math+", "gint", "fxlib", "SH4 emulator").
- Casio official: edu.casio.com, support.casio.com manuals (Python
  chapters), open-source/licence notices.
- MicroPython GitHub history: commits after v1.9.4 touching
  compile.c tuple assignment, objtuple.c, gc.c alloc hint, pystack.
- Wikipedia / WikiChip / teardown sites for the hardware.

## Output

A markdown report:
1. Answers per question (numbered as above) with sources and confidence.
2. Anything that contradicts the "already known" list.
3. Leads worth following up that you couldn't resolve.
4. A short list of the most useful URLs.
