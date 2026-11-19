# cginternals: the values inside turtle and matplotlib.pyplot
# Photograph every page (numbered at the bottom), then press
# EXE for the next. Values are listed when imported, then again
# after a few drawing calls, to show what each one holds.
from casioplot import clear_screen, draw_string, show_screen, getkey
import turtle as T
import matplotlib.pyplot as P

COLS = 46
ROWS = 16
out = []

def add(text):
  while len(text) > COLS:
    out.append(text[:COLS])
    text = "  " + text[COLS:]
  out.append(text)

def values(title, mod):
  add("== " + title)
  for name in sorted(dir(mod)):
    v = getattr(mod, name)
    if callable(v) or type(v) == type(T):
      continue
    r = repr(v)
    if len(r) > 700:
      r = r[:700] + "...(" + str(len(r)) + ")"
    add(name + "=" + r)

values("turtle at import", T)
values("pyplot at import", P)

T.pensize(3)
T.pencolor("red")
T.forward(10)
T.left(30)
T.penup()
values("turtle after pensize(3) pencolor(red) fd(10) lt(30) penup()", T)

P.plot([1, 2], [3, 4])
P.scatter([1], [2])
P.bar([3], [2])
P.text(1, 1, "a")
P.axis([0, 5, 0, 5])
P.grid()
values("pyplot after plot scatter bar text axis grid", P)

def key():
  while getkey():
    pass
  while not getkey():
    pass

pages = (len(out) + ROWS - 1) // ROWS
for p in range(pages):
  clear_screen()
  for i in range(ROWS):
    k = p * ROWS + i
    if k < len(out):
      draw_string(0, i * 11, out[k], (0, 0, 0), "small")
  draw_string(0, 178, "page " + str(p + 1) + "/" + str(pages) + "  EXE: next", (0, 0, 255), "small")
  show_screen()
  key()
