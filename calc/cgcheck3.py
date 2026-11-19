# cgcheck3: get_pixel read-back, turtle colours, pen sizes and
# speeds, pyplot details. Run it fresh (just after opening Python).
# 1. Photograph each page (numbered at the bottom), EXE for the next.
# 2. After the last page a plot is drawn with show(). Photograph it.
#    If it stays, press EXE (and photograph what comes next).
# 3. The script ends with a deliberate error: photograph the shell.
from casioplot import clear_screen, draw_string, show_screen, getkey
from casioplot import set_pixel, get_pixel
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

def show(label, f):
  try:
    r = repr(f())
  except Exception as e:
    r = "ERR " + repr(e)
  if len(r) > 300:
    r = r[:300] + "...(" + str(len(r)) + ")"
  add(label + " " + r)

# get_pixel after set_pixel: what does each colour read back as?
add("== get_pixel")
clear_screen()
show("fresh (0,0)", lambda: get_pixel(0, 0))
for c in ((255, 0, 0), (255, 255, 255), (248, 252, 248),
          (250, 250, 250), (0, 0, 0), (0, 255, 0), (0, 0, 255),
          (7, 3, 7), (8, 4, 8), (128, 128, 128), (255, 255, 254)):
  set_pixel(0, 0, c)
  show(str(c), lambda: get_pixel(0, 0))
show("(-1,0)", lambda: get_pixel(-1, 0))
show("(0,191)", lambda: get_pixel(0, 191))
show("(0,192)", lambda: get_pixel(0, 192))
show("(384,0)", lambda: get_pixel(384, 0))
show("set (300,0,0)", lambda: set_pixel(1, 1, (300, 0, 0)))
show(" reads", lambda: get_pixel(1, 1))
clear_screen()

# turtle: what each colour name stores
add("== turtle pencolor(name) -> pencolor()")
for n in ("black", "white", "red", "green", "blue", "yellow",
          "cyan", "magenta", "orange", "purple", "brown", "pink",
          "grey", "gray", "lightblue", "darkgreen", "Red"):
  def f():
    T.pencolor(n)
    return T.pencolor()
  show(n, f)
for c in ((255, 0, 0), (0.5, 0.5, 0.5), (128, 0, 0), (1, 1, 1)):
  def f():
    T.pencolor(c)
    return T.pencolor()
  show(str(c), f)
show("pencolor(1,0,0)", lambda: (T.pencolor(1, 0, 0), T.pencolor())[1])
show("turtle_color", lambda: T.turtle_color)
add("== turtle pensize(k) -> pensize(), pen_pixels")
for k in (1, 2, 4, 5, 6, 10, 0):
  def f():
    T.pensize(k)
    return (T.pensize(), T.pen_size, T.pen_pixels)
  show(str(k), f)
show("2.5", lambda: (T.pensize(2.5), T.pen_size)[1])
add("== turtle speed(k) -> speed(), turtle_speed")
for k in (0, 1, 3, 10, 11, -1, 2.5, "fast", "slowest"):
  def f():
    T.speed(k)
    return (T.speed(), T.turtle_speed)
  show(repr(k), f)
show("color", lambda: T.color)
show("colormode", lambda: T.colormode)
T.hideturtle()

# pyplot
add("== pyplot")
show("axis()", lambda: P.axis())
show("plot red", lambda: (P.plot([1, 2], [3, 4], "red"), P.lines[-1])[1])
show("plot color=", lambda: (P.plot([1, 2], [3, 5], color="green"), P.lines[-1])[1])
show("plot r--", lambda: (P.plot([1, 2], [3, 6], "r--"), P.lines[-1])[1])
show("plot ro", lambda: (P.plot([1, 2], [3, 7], "ro"), P.lines[-1])[1])
show("plot (1,0,0)", lambda: (P.plot([1, 2], [3, 8], (1, 0, 0)), P.lines[-1])[1])
show("plot orange", lambda: (P.plot([1, 2], [3, 9], "orange"), P.lines[-1])[1])
show("plot 1 list", lambda: (P.plot([5, 6, 7]), P.lines[-2:])[1])
show("scatter red", lambda: (P.scatter([1], [2], color="red"), P.points[-1])[1])
show("text colour", lambda: (P.text(0, 0, "t", "red"), P.textes[-1])[1])
show("axis() now", lambda: P.axis())
show("extrem", lambda: P.extrem)
show("axis('auto')", lambda: P.axis("auto"))
show("axis() after", lambda: P.axis())
show("win_scaling", lambda: P.win_scaling)
show("fenetre", lambda: P.fenetre)
show("axis([0,9,0,9])", lambda: P.axis([0, 9, 0, 9]))
show("axis('off')", lambda: P.axis("off"))
show("axis_display", lambda: P.axis_display)
show("axis('on')", lambda: P.axis("on"))
n = len(P.lines)
show("arrow", lambda: (P.arrow(0, 0, 1, 1), P.lines[n:])[1])
n = len(P.lines)
show("arrow head", lambda: (P.arrow(0, 0, 2, 1, head_width=0.5, head_length=0.5), P.lines[n:])[1])
n = len(P.lines)
show("hist", lambda: P.hist([1, 2, 2, 3, 3, 3]))
show(" lines", lambda: P.lines[n:])
n = len(P.lines)
show("hist bins=2", lambda: P.hist([1, 2, 2, 3, 3, 3], 2))
show(" lines", lambda: P.lines[n:])
show("len lines/points/textes", lambda: (len(P.lines), len(P.points), len(P.textes)))

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

# Does show() keep the stored data, and does it wait for a key?
P.axis([0, 10, 0, 10])
P.show()
print("after show:", len(P.lines), len(P.points), len(P.textes))
print("axis", P.axis())
raise ValueError("cgcheck3 end")
