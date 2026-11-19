# matplotlib.pyplot for the fx-CG100 emulator, on casioplot.
# The calculator's pyplot is a Python module of its firmware. This one has
# exactly its 28 names (calc/cgnames.py, bm_core_videos/12), keeps its state
# the way calc/cginternals.py photographed it (bm_core_videos/14), and draws
# like the photos of calc/cgplot.py and cgplot2.py (bm_core_videos/11, 12).
#
# Photographed state: lines [x0, y0, x1, y1, colour], points [x, y, colour],
# textes [x, y, text]; each list starts as [[]] (plot() and text() replace
# that empty entry, scatter() keeps it). Automatic colours are letters from
# color_auto, one per call (a bar's three lines share one). extrem starts at
# 0..1 and is replaced by the first data, then grows. limits holds pixel
# bounds.
#
# As photographed on screen: the window is 0..1 on both axes until axis()
# sets it (no autoscaling), mapped to x 45..383, y 165..5. Axes on the left
# and bottom only, drawn after the data, with outside ticks from the
# window's minimum in steps of 1, 2.5 or 5 x 10^n (the smallest giving at
# most 6 intervals), labels in the small font and a light grey-blue grid.
# Scatter draws 5 px "+" marks, bars are open at the bottom, arrows are a
# plain black line, text has its top left at the point.
import casioplot as plt

COLOR_DECO_CHAR = ['o', '.', '+', '*', '-']
available_colors = ['b', 'r', 'g', 'k', 'm', 'c', 'y', 'w', 'blue', 'red', 'green',
                    'black', 'magenta', 'cyan', 'yellow', 'white', 'grey', 'orange',
                    'purple', 'brown', 'pink']
color_auto = ['b', 'r', 'g', 'm', 'k', 'c', 'y']
color_count = 0
color_grid = 'grey'
fenetre = [0, 1, 0, 1]
win_scaling = 'init'     # 'init': 0..1, 'fixed': axis([...]), 'auto': the data
extrem = [0, 1, 0, 1]
axis_display = 'on'
grid_display = 'off'
limits = [40, 165, 384, 0]
lines = [[]]
points = [[]]
textes = [[]]

def _plot_core(xs, ys, color, kind):
  # kind "lines": a polyline; "segs": separate segments, coordinates in
  # pairs; "points": marks. color: given, or the next automatic one
  global color_count, extrem, lines
  if color is None:
    color = color_auto[color_count % len(color_auto)]
    color_count += 1
  first = lines == [[]] and points == [[]]
  for v in range(len(xs)):
    if first:
      extrem = [xs[v], xs[v], ys[v], ys[v]]
      first = False
    extrem = [min(extrem[0], xs[v]), max(extrem[1], xs[v]), min(extrem[2], ys[v]), max(extrem[3], ys[v])]
  if kind == "points":
    for v in range(len(xs)):
      points.append([xs[v], ys[v], color])
    return color
  if kind == "segs":
    # consecutive repeats are dropped (hist's empty bins, photographed)
    segs = []
    for v in range(0, len(xs) - 1, 2):
      seg = [xs[v], ys[v], xs[v + 1], ys[v + 1], color]
      if not segs or seg != segs[-1]:
        segs.append(seg)
  elif len(xs) == 1:
    segs = [[xs[0], ys[0], xs[0], ys[0], color]]
  else:
    segs = [[xs[v - 1], ys[v - 1], xs[v], ys[v], color] for v in range(1, len(xs))]
  if lines == [[]]:
    lines = segs
  else:
    lines.extend(segs)
  return color

def axis(*a):
  # returns a tuple (photographed). With no arguments it gives the data's
  # window once something is plotted, though show() still draws 0..1 until
  # axis() sets a window (bm_core_videos/11); whether axis() also switches
  # show() to that window is not known (assumed not)
  global fenetre, win_scaling, axis_display
  def auto():
    # the data's range and 5% each side (photographed: x 0..2 and y 3..9
    # give (-0.1, 2.1, 2.7, 9.300000000000001))
    x0, x1, y0, y1 = extrem
    if x0 == x1:
      x0, x1 = x0 - 1, x1 + 1
    if y0 == y1:
      y0, y1 = y0 - 1, y1 + 1
    return [x0 - 0.05 * (x1 - x0), x1 + 0.05 * (x1 - x0),
            y0 - 0.05 * (y1 - y0), y1 + 0.05 * (y1 - y0)]
  if a:
    v = a[0] if len(a) == 1 else a
    if v in ("on", "off"):
      axis_display = v
    elif v == "auto":
      win_scaling = "auto"
      fenetre = auto()
    else:
      fenetre = list(v)
      win_scaling = "fixed"
  elif win_scaling != "fixed" and (lines != [[]] or points != [[]]):
    w = auto()
    if win_scaling == "auto":
      fenetre = w
    return tuple(w)
  return tuple(fenetre)

def grid(on=None):
  global grid_display
  if on is None:
    grid_display = "off" if grid_display == "on" else "on"
  else:
    grid_display = "on" if on in (True, "on") else "off"

def plot(*a, **kw):
  if len(a) >= 2 and not isinstance(a[1], str):
    x, y = list(a[0]), list(a[1])
    fmt = a[2] if len(a) > 2 else None
  else:
    y = list(a[0])
    x = list(range(len(y)))
    fmt = a[1] if len(a) > 1 else None
  if fmt is not None and not isinstance(fmt, str):
    raise Exception("function plot() : error using arguments")
  if len(x) != len(y):
    raise ValueError("x and y must have same length")
  # photographed (bm_core_videos/15): a name is kept as given, a letter
  # followed by one marker character loses the marker ('ro' -> 'r'),
  # anything else ('r--') is refused
  c = kw.get("color", fmt)
  if c is not None and c not in available_colors:
    if isinstance(c, str) and len(c) == 2 and c[1] in COLOR_DECO_CHAR \
        and c[0] in available_colors:
      c = c[0]
    else:
      raise ValueError("function plot() : unknown color code")
  _plot_core(x, y, c, "lines")

def scatter(x, y):
  # no color= (photographed: TypeError)
  if not isinstance(x, (list, tuple)):
    x, y = [x], [y]
  _plot_core(list(x), list(y), None, "points")

def bar(x, height, width=0.8, **kw):
  # left side, right side, top: no line along the bottom (photographed)
  if not isinstance(x, (list, tuple)):
    x, height = [x], [height]
  color = kw.get("color")
  for i in range(len(x)):
    a = x[i] - width / 2
    b = x[i] + width / 2
    h = height[i]
    color = _plot_core([a, a, b, b, a, b], [0, h, 0, h, h, h], color, "segs")

def hist(x, bins=10, **kw):
  # each bin's left side, top and right side, repeats dropped
  # (photographed)
  lo, hi = min(x), max(x)
  if isinstance(bins, int):
    w = (hi - lo) / bins if hi > lo else 1
    edges = [lo + i * w for i in range(bins + 1)]
  else:
    edges = list(bins)
  counts = [0] * (len(edges) - 1)
  for v in x:
    for i in range(len(counts)):
      if edges[i] <= v < edges[i + 1] or (i == len(counts) - 1 and v == edges[-1]):
        counts[i] += 1
        break
  xs = []
  ys = []
  for i in range(len(counts)):
    a, b, h = edges[i], edges[i + 1], counts[i]
    xs += [a, a, a, b, b, b]
    ys += [0, h, h, h, h, 0]
  _plot_core(xs, ys, kw.get("color"), "segs")
  return counts, edges

def arrow(x, y, dx, dy, head_width=0.003, head_length=None, **kw):
  # black; the head is a triangle from (x+dx, y+dy) on, head_width across
  # and head_length (1.5 x head_width) long, then 59 lines filling it
  # (photographed: the triangle's corners and the line count; the order
  # of the filling lines is a guess). At the default size it is invisible.
  if head_length is None:
    head_length = 1.5 * head_width
  c = kw.get("color", "k")
  _plot_core([x, x + dx], [y, y + dy], c, "lines")
  ex, ey = x + dx, y + dy
  d = (dx * dx + dy * dy) ** 0.5
  if d == 0:
    return
  ux, uy = dx / d, dy / d
  px, py = -uy * head_width / 2, ux * head_width / 2
  tx, ty = ex + ux * head_length, ey + uy * head_length
  xs = [ex + px, ex - px, ex - px, tx, tx, ex + px, ex, tx]
  ys = [ey + py, ey - py, ey - py, ty, ty, ey + py, ey, ty]
  for k in range(1, 30):
    for s in (1, -1):
      xs += [ex + s * px * k / 29, tx]
      ys += [ey + s * py * k / 29, ty]
  _plot_core(xs, ys, c, "segs")

def text(x, y, s):
  global textes
  if textes == [[]]:
    textes = [[x, y, str(s)]]
  else:
    textes.append([x, y, str(s)])

def _show_core():
  rgb = {
    "b": (0, 0, 255), "r": (255, 0, 0), "g": (0, 128, 0), "k": (0, 0, 0),
    "m": (191, 0, 191), "c": (0, 191, 191), "y": (191, 191, 0), "w": (255, 255, 255),
    "blue": (0, 0, 255), "red": (255, 0, 0), "green": (0, 128, 0), "black": (0, 0, 0),
    "magenta": (191, 0, 191), "cyan": (0, 191, 191), "yellow": (191, 191, 0),
    "white": (255, 255, 255), "grey": (176, 192, 216), "orange": (255, 165, 0),
    "purple": (128, 0, 128), "brown": (165, 42, 42), "pink": (255, 192, 203),
  }
  def col(c):
    if isinstance(c, str):
      return rgb.get(c, (0, 0, 0))
    return tuple([int(v * 255) if isinstance(v, float) and v <= 1 else int(v) for v in c])
  x0, x1, y0, y1 = axis() if win_scaling == "auto" else fenetre
  sx = 338 / (x1 - x0)
  sy = 160 / (y1 - y0)
  def px(x, y):
    return int(round(45 + (x - x0) * sx)), int(round(165 - (y - y0) * sy))
  def put(x, y, c):
    if 45 <= x <= 383 and 5 <= y <= 165:
      plt.set_pixel(x, y, c)
  def line(a, b, c, d, colour):
    dx = abs(c - a)
    dy = -abs(d - b)
    s1 = 1 if a < c else -1
    s2 = 1 if b < d else -1
    err = dx + dy
    while True:
      put(a, b, colour)
      if a == c and b == d:
        return
      e2 = 2 * err
      if e2 >= dy:
        err += dy
        a += s1
      if e2 <= dx:
        err += dx
        b += s2
  def ticks(a, b):
    span = b - a
    k = 1.0
    while span / k > 6:
      k *= 10
    while span / k <= 0.6:
      k /= 10
    step = k
    for m in (0.1, 0.25, 0.5, 1):
      if span / (k * m) <= 6:
        step = k * m
        break
    out = []
    i = 0
    while a + i * step <= b + step * 1e-9:
      out.append(a + i * step)
      i += 1
    return out
  def label(v):
    s = "%.4g" % v
    return "0" if s == "-0" else s
  plt.clear_screen()
  if axis_display == "on":
    for t in ticks(x0, x1):
      x, _ = px(t, y0)
      if grid_display == "on" and x > 45:
        line(x, 5, x, 164, col(color_grid))
      for k in range(166, 169):
        plt.set_pixel(x, k, (0, 0, 0))
      s = label(t)
      if x + 7 * len(s) <= 384:
        plt.draw_string(x + 1, 178, s, (0, 0, 0), "small")
    for t in ticks(y0, y1):
      _, y = px(x0, t)
      if grid_display == "on" and y < 165:
        line(46, y, 383, y, col(color_grid))
      for k in range(42, 45):
        plt.set_pixel(k, y, (0, 0, 0))
      plt.draw_string(-1, y, label(t), (0, 0, 0), "small")
  for seg in lines:
    if seg:
      p, q = px(seg[0], seg[1])
      r, s = px(seg[2], seg[3])
      line(p, q, r, s, col(seg[4]))
  for pt in points:
    if pt:
      p, q = px(pt[0], pt[1])
      c = col(pt[2])
      for k in range(-2, 3):
        put(p + k, q, c)
        put(p, q + k, c)
  for tx in textes:
    if tx:
      p, q = px(tx[0], tx[1])
      plt.draw_string(p, q, tx[2], (0, 0, 0), "small")
  # axes last: they stay black where a bar edge lies on them (photo)
  if axis_display == "on":
    line(45, 165, 383, 165, (0, 0, 0))
    line(45, 5, 45, 165, (0, 0, 0))
  plt.show_screen()

def show():
  _show_core()

__file__ = 'matplotlib\\pyplot.py'
