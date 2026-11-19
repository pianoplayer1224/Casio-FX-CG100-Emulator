# turtle for the fx-CG100 emulator, on casioplot.
# The calculator's turtle is a Python module of its firmware. This one has
# exactly its 71 names (calc/cgnames.py, bm_core_videos/12) - including
# sin, cos, sqrt, atan2, pi and casioplot, which `from turtle import *`
# hands to the script - and draws like the film of calc/cgturtle.py
# (bm_core_videos/11). How it works inside is not known; the helpers and
# state variables carry the calculator's names; their values at import and
# after a few calls are photographed (calc/cginternals.py, bm_core_videos/14;
# calc/cgcheck3.py, bm_core_videos/15): colours 0..1, shapes as pixel lists, the turtle left drawn at rest with the
# pixels under it kept in turtle_buffer.
# Canvas 384x192, origin at its centre, y up, angles in degrees.
import casioplot
from math import sin, cos, sqrt, atan2, pi

turtle_pos = [0, 0]
turtle_angle = 0
turtle_color = (0, 0, 0)
turtle_speed = 5
turtle_visible = True
turtle_name = "classic"
# pixel offsets (forward, left) from the turtle's position
turtleshapes = {
  "turtle": [[-3, 3], [2, 3], [-2, 2], [-1, 2], [0, 2], [1, 2], [-2, 1], [-1, 1],
             [1, 1], [0, 1], [2, 1], [3, 1], [-2, 0], [-1, 0], [0, 0], [1, 0],
             [-1, -1], [-2, -1], [0, -1], [1, -1], [2, 0], [3, 0], [-3, -2], [2, -2]],
  "classic": [[-9, 5], [-9, 4], [-8, 4], [-8, 3], [-8, 2], [-8, -2], [-8, -3],
              [-8, -4], [-9, -4], [-9, -5], [-7, 4], [-7, 1], [-7, 0], [-7, -1],
              [-7, -4], [-6, 3], [-6, -3], [-5, 3], [-5, -3], [-4, 2], [-4, -2],
              [-3, 2], [-3, -2], [-2, 1], [-2, -1], [-1, 1], [-1, -1], [0, 0]],
}
turtle_data = turtleshapes["classic"]
turtle_buffer = []       # [x, y, colour] under the drawn turtle
writing = True           # pen down
pen_size = 1
pen_pixels = [[0, 0]]
frame_count = 0          # pixels moved

def _conv_angle(a):
  # the calculator's math has no radians()
  return a * pi / 180

def _draw_turtle():
  # each shape pixel turned to the heading and rounded, repeats dropped
  # (matches the photographed turtle_buffer at 30 degrees exactly)
  global turtle_buffer
  turtle_buffer = []
  if not turtle_visible:
    return
  a = _conv_angle(turtle_angle)
  ca = cos(a)
  sa = sin(a)
  x0 = turtle_pos[0] + 192
  y0 = 96 - turtle_pos[1]
  c = _rgb(turtle_color)
  done = []
  for f, l in turtle_data:
    x = int(round(x0 + f * ca - l * sa))
    y = int(round(y0 - (f * sa + l * ca)))
    if [x, y] in done:
      continue
    done.append([x, y])
    turtle_buffer.append([x, y, casioplot.get_pixel(x, y)])
  for x, y, old in turtle_buffer:
    casioplot.set_pixel(x, y, c)

def _erase_turtle():
  global turtle_buffer
  for x, y, old in turtle_buffer:
    if old is not None:
      casioplot.set_pixel(x, y, old)
  turtle_buffer = []

def _refresh_turtle():
  _erase_turtle()
  _draw_turtle()
  casioplot.show_screen()

def _rgb(c):
  return (int(c[0] * 255), int(c[1] * 255), int(c[2] * 255))

def _pen_brush(x, y, c):
  for dx, dy in pen_pixels:
    casioplot.set_pixel(x + dx, y + dy, c)

def goto(x, y=None, show=True):
  # Bresenham from the turtle to (x, y), one pixel at a time (frame_count
  # counts them). Above speed 0 the turtle is shown on the way every few
  # pixels: every 6 at the default speed 5, which reproduces the film of
  # calc/cgturtle.py within ~9% (star 1.34 s, filmed 1.37; pen-up move
  # 0.38 s, 0.35; circle 1.27 s, 1.24, shown at each chord end). Other
  # speeds are scaled from that, unfilmed.
  global frame_count
  if y is None:
    x, y = x
  x0 = int(round(turtle_pos[0] + 192))
  y0 = int(round(96 - turtle_pos[1]))
  x1 = int(round(x + 192))
  y1 = int(round(96 - y))
  every = turtle_speed * 1.2
  c = _rgb(turtle_color)
  _erase_turtle()
  dx = abs(x1 - x0)
  dy = -abs(y1 - y0)
  sx = 1 if x0 < x1 else -1
  sy = 1 if y0 < y1 else -1
  err = dx + dy
  while True:
    if writing:
      _pen_brush(x0, y0, c)
    if x0 == x1 and y0 == y1:
      break
    e2 = 2 * err
    if e2 >= dy:
      err += dy
      x0 += sx
    if e2 <= dx:
      err += dx
      y0 += sy
    frame_count += 1
    if every and int(frame_count / every) != int((frame_count - 1) / every):
      turtle_pos[0] = x0 - 192
      turtle_pos[1] = 96 - y0
      _refresh_turtle()
      _erase_turtle()
  turtle_pos[0] = float(x)
  turtle_pos[1] = float(y)
  if show:
    _refresh_turtle()

def forward(d):
  a = _conv_angle(turtle_angle)
  goto(turtle_pos[0] + d * cos(a), turtle_pos[1] + d * sin(a))

def backward(d):
  forward(-d)

def right(a):
  global turtle_angle
  turtle_angle = (turtle_angle - a) % 360
  _refresh_turtle()

def left(a):
  right(-a)

def setx(x):
  goto(x, turtle_pos[1])

def sety(y):
  goto(turtle_pos[0], y)

def setheading(a):
  global turtle_angle
  turtle_angle = a % 360
  _refresh_turtle()

def home():
  goto(0, 0)
  setheading(0)

def circle(radius, extent=None):
  # short chords, the turtle shown at the end of each (the film's circle
  # costs more per pixel than its star)
  global turtle_angle
  if extent is None:
    extent = 360
  n = max(4, min(72, int(abs(radius) * abs(extent) / 360 / 2) + 4))
  step = extent / n
  length = 2 * abs(radius) * sin(_conv_angle(abs(step)) / 2)
  if radius < 0:
    step = -step
  for i in range(n):
    turtle_angle = (turtle_angle + step / 2) % 360
    a = _conv_angle(turtle_angle)
    goto(turtle_pos[0] + length * cos(a), turtle_pos[1] + length * sin(a))
    turtle_angle = (turtle_angle + step / 2) % 360
  _refresh_turtle()

def write(text):
  # small font, starting at the turtle, just below it (filmed)
  x = int(round(turtle_pos[0] + 192))
  y = int(round(96 - turtle_pos[1]))
  _erase_turtle()
  casioplot.draw_string(x - 1, y + 1, str(text), _rgb(turtle_color), "small")
  _refresh_turtle()

def position():
  return (turtle_pos[0], turtle_pos[1])

def xcor():
  return turtle_pos[0]

def ycor():
  return turtle_pos[1]

def heading():
  return turtle_angle

def distance(x, y=None):
  if y is None:
    x, y = x
  return sqrt((x - turtle_pos[0]) ** 2 + (y - turtle_pos[1]) ** 2)

def towards(x, y=None):
  if y is None:
    x, y = x
  return atan2(y - turtle_pos[1], x - turtle_pos[0]) * 180 / pi % 360

def pendown():
  global writing
  writing = True

def penup():
  global writing
  writing = False

def isdown():
  return writing

def pensize(w=None):
  # photographed (bm_core_videos/15): sizes above 5 become 5, 0 and 2.5 are
  # kept; the brush grows in rings: + at 2, 3x3 at 3, +-2 tips at 4, the
  # (2, 1) knight moves at 5
  global pen_size, pen_pixels
  if w is None:
    return pen_size
  pen_size = min(w, 5)
  pts = [[0, 0]]
  if pen_size >= 2:
    pts += [[1, 0], [0, 1], [-1, 0], [0, -1]]
  if pen_size >= 3:
    pts += [[1, 1], [1, -1], [-1, 1], [-1, -1]]
  if pen_size >= 4:
    pts += [[2, 0], [0, 2], [-2, 0], [0, -2]]
  if pen_size >= 5:
    pts += [[2, 1], [1, 2], [-2, 1], [-1, 2], [2, -1], [1, -2], [-2, -1], [-1, -2]]
  pen_pixels = pts

# the 13 names pencolor() takes; the values other than black, white and
# the primaries are not photographed
_colors = {
  "black": (0, 0, 0), "white": (1, 1, 1), "red": (1, 0, 0),
  "green": (0, 1, 0), "blue": (0, 0, 1), "yellow": (1, 1, 0),
  "cyan": (0, 1, 1), "magenta": (1, 0, 1), "orange": (1, 0.65, 0),
  "purple": (0.63, 0.13, 0.94), "brown": (0.65, 0.16, 0.16),
  "pink": (1, 0.75, 0.8), "grey": (0.75, 0.75, 0.75),
}

def pencolor(*c):
  # photographed: a name is stored as its 0..1 tuple, three numbers as a
  # list, one tuple as given; pencolor() gives the name back when there is
  # one ('white' for (1, 1, 1))
  global turtle_color
  if not c:
    for n in _colors:
      if tuple(turtle_color) == _colors[n]:
        return n
    return turtle_color
  if len(c) == 1 and isinstance(c[0], str) and c[0] in _colors:
    turtle_color = _colors[c[0]]
  else:
    v = c[0] if len(c) == 1 else list(c)
    ok = isinstance(v, (list, tuple)) and len(v) == 3
    if ok:
      for x in v:
        if not isinstance(x, (int, float)) or x < 0 or x > 1:
          ok = False
    if not ok:
      raise ValueError("error using pencolor : enter a color text or 3 floats between 0 and 1")
    turtle_color = v
  _refresh_turtle()

def speed(s=None):
  # photographed: 11 and -1 give 0, 2.5 gives 2, 'fast' 10, 'slowest' 1
  global turtle_speed
  if s is None:
    return turtle_speed
  if isinstance(s, str):
    s = {"fastest": 0, "fast": 10, "normal": 6, "slow": 3, "slowest": 1}[s]
  turtle_speed = int(round(s)) if 0.5 < s < 10.5 else 0

def shape(name=None):
  global turtle_name
  if name is None:
    return turtle_name
  global turtle_data
  if name not in turtleshapes:
    raise ValueError("bad shape")
  turtle_name = name
  turtle_data = turtleshapes[name]
  _refresh_turtle()

def showturtle():
  global turtle_visible
  turtle_visible = True
  _refresh_turtle()

def hideturtle():
  global turtle_visible
  turtle_visible = False
  _refresh_turtle()

def isvisible():
  return turtle_visible

def clear():
  global turtle_buffer
  turtle_buffer = []
  casioplot.clear_screen()
  _refresh_turtle()

def reset():
  global turtle_angle, writing, turtle_color, turtle_visible, turtle_speed
  turtle_pos[0] = turtle_pos[1] = 0
  turtle_angle = 0
  writing = True
  turtle_color = (0, 0, 0)
  turtle_visible = True
  turtle_speed = 5
  pensize(1)
  clear()

fd = forward
bk = back = backward
rt = right
lt = left
setpos = setposition = goto
seth = setheading
pos = position
pd = down = pendown
pu = up = penup
width = pensize
st = showturtle
ht = hideturtle

# The calculator shows the canvas with the turtle when turtle is imported
_refresh_turtle()
__file__ = "turtle.py"
