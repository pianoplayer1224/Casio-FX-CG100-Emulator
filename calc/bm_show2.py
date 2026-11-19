# bm_show2: show_screen() cost per changed row, with longer runs.
# Film the screen. Top-left block flips black/white
# between timed phases. Do not touch keys until DONE.
#
# The emulator's model (Bad Apple film, bm_show): show_screen()
# costs 62.8 us for each canvas row drawn on since the last show.
# Then pxNd (N pixels in N rows) costs (N-1)*62.8 us more than
# pxNs (N pixels in one row), and col (192 rows) ~12 ms more than
# row (1 row of 384). pxshow2 repeats bm_show's noisy test, 30x
# longer: is a second show with nothing drawn free?
from casioplot import *
SCALE=1
K=(0,0,0)
W=(255,255,255)
R=(255,0,0)

def mark(c):
  for y in range(64):
    for x in range(128):
      set_pixel(x,y,c)
  show_screen()

def run(name,T):
  clear_screen()
  draw_string(140,4,name,K,"medium")
  draw_string(140,24,"tests "+str(len(T)),K,"small")
  draw_string(140,38,"edges "+str(4*len(T)+2),K,"small")
  draw_string(140,52,"scale "+str(SCALE),K,"small")
  mark(W)
  mark(K)
  c=K
  for t in T:
    n=int(t[2]*SCALE)
    if n<1:
      n=1
    for m in (n,2*n,2*n,n):
      t[1](m)
      if c==K:
        c=W
      else:
        c=K
      mark(c)
  mark(W)
  draw_string(140,70,"DONE",K,"large")
  show_screen()

def t_for(n):
  for i in range(n):
    pass

def t_show(n):
  h=show_screen
  for i in range(n):
    h()

def t_px1(n):
  s=set_pixel;h=show_screen;c=R
  for i in range(n):
    s(200,150,c);h()

def t_pxshow2(n):
  s=set_pixel;h=show_screen;c=R
  for i in range(n):
    s(200,150,c);h();h()

def t_px2s(n):
  s=set_pixel;h=show_screen;c=R
  for i in range(n):
    s(200,150,c);s(201,150,c);h()

def t_px2d(n):
  s=set_pixel;h=show_screen;c=R
  for i in range(n):
    s(200,150,c);s(200,151,c);h()

def t_px8s(n):
  s=set_pixel;h=show_screen;c=R
  for i in range(n):
    s(200,150,c);s(201,150,c);s(202,150,c);s(203,150,c)
    s(204,150,c);s(205,150,c);s(206,150,c);s(207,150,c);h()

def t_px8d(n):
  s=set_pixel;h=show_screen;c=R
  for i in range(n):
    s(200,150,c);s(200,151,c);s(200,152,c);s(200,153,c)
    s(200,154,c);s(200,155,c);s(200,156,c);s(200,157,c);h()

# 384 pixels in one row, or 192 rows of 2 pixels, with and
# without a show after each
def t_rowno(n):
  s=set_pixel;c=R
  for i in range(n):
    for x in range(384):
      s(x,150,c)

def t_row(n):
  s=set_pixel;h=show_screen;c=R
  for i in range(n):
    for x in range(384):
      s(x,150,c)
    h()

def t_colno(n):
  s=set_pixel;c=R
  for i in range(n):
    for y in range(192):
      s(200,y,c);s(201,y,c)

def t_col(n):
  s=set_pixel;h=show_screen;c=R
  for i in range(n):
    for y in range(192):
      s(200,y,c);s(201,y,c)
    h()

# (name, function, iterations, ops per iteration, baseline test)
T=[
 ("for",t_for,200000,1,None),
 ("show",t_show,40000,1,"for"),
 ("px1",t_px1,10000,1,"for"),
 ("pxshow2",t_pxshow2,10000,1,"for"),
 ("px2s",t_px2s,8000,1,"for"),
 ("px2d",t_px2d,8000,1,"for"),
 ("px8s",t_px8s,5000,1,"for"),
 ("px8d",t_px8d,3000,1,"for"),
 ("rowno",t_rowno,150,1,"for"),
 ("row",t_row,150,1,"rowno"),
 ("colno",t_colno,150,1,"for"),
 ("col",t_col,100,1,"colno"),
 ("for2",t_for,200000,1,None),
]

run("bm_show2",T)
