# bm_plot: casioplot drawing costs
# Film the screen. Top-left block flips black/white
# between timed phases. Do not touch keys until DONE.
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

def t_spx(n):
  s=set_pixel;x=200;y=150;c=R
  for i in range(n):
    s(x,y,c);s(x,y,c);s(x,y,c);s(x,y,c);s(x,y,c);s(x,y,c);s(x,y,c);s(x,y,c);s(x,y,c);s(x,y,c)

def t_spxg(n):
  x=200;y=150;c=R
  for i in range(n):
    set_pixel(x,y,c);set_pixel(x,y,c);set_pixel(x,y,c);set_pixel(x,y,c);set_pixel(x,y,c);set_pixel(x,y,c);set_pixel(x,y,c);set_pixel(x,y,c);set_pixel(x,y,c);set_pixel(x,y,c)

def t_spxt(n):
  s=set_pixel;x=200;y=150
  for i in range(n):
    s(x,y,(255,0,0));s(x,y,(255,0,0));s(x,y,(255,0,0));s(x,y,(255,0,0));s(x,y,(255,0,0));s(x,y,(255,0,0));s(x,y,(255,0,0));s(x,y,(255,0,0));s(x,y,(255,0,0));s(x,y,(255,0,0))

def t_spxo(n):
  s=set_pixel;x=500;y=500;c=R
  for i in range(n):
    s(x,y,c);s(x,y,c);s(x,y,c);s(x,y,c);s(x,y,c);s(x,y,c);s(x,y,c);s(x,y,c);s(x,y,c);s(x,y,c)

def t_spxk(n):
  s=set_pixel;x=200;y=150;c=K
  for i in range(n):
    s(x,y,c);s(x,y,c);s(x,y,c);s(x,y,c);s(x,y,c);s(x,y,c);s(x,y,c);s(x,y,c);s(x,y,c);s(x,y,c)

def t_spxw(n):
  s=set_pixel;x=200;y=150;c=W
  for i in range(n):
    s(x,y,c);s(x,y,c);s(x,y,c);s(x,y,c);s(x,y,c);s(x,y,c);s(x,y,c);s(x,y,c);s(x,y,c);s(x,y,c)

def t_gpx(n):
  g=get_pixel;x=200;y=150
  for i in range(n):
    c=g(x,y);c=g(x,y);c=g(x,y);c=g(x,y);c=g(x,y);c=g(x,y);c=g(x,y);c=g(x,y);c=g(x,y);c=g(x,y)

def t_show(n):
  for i in range(n):
    show_screen()

def t_clear(n):
  for i in range(n):
    clear_screen()

def t_ds1(n):
  for i in range(n):
    draw_string(140,100,"A",K,"small")

def t_ds10(n):
  for i in range(n):
    draw_string(140,100,"ABCDEFGHIJ",K,"small")

def t_dm10(n):
  for i in range(n):
    draw_string(140,120,"ABCDEFGHIJ",K,"medium")

def t_dl10(n):
  for i in range(n):
    draw_string(140,140,"ABCDEFGHIJ",K,"large")

def t_dl1(n):
  for i in range(n):
    draw_string(140,140,"A",K,"large")

def t_row(n):
  s=set_pixel;c=R
  for i in range(n):
    for x in range(384):
      s(x,180,c)

def t_fill(n):
  s=set_pixel;c=R
  for i in range(n):
    for y in range(80,192):
      for x in range(384):
        s(x,y,c)

# (name, function, iterations, ops per iteration, baseline test)
T=[
 ("for",t_for,400000,1,None),
 ("spx",t_spx,23000,10,"for"),
 ("spxg",t_spxg,17000,10,"for"),
 ("spxt",t_spxt,160,10,"for"),
 ("spxo",t_spxo,34000,10,"for"),
 ("spxk",t_spxk,23000,10,"for"),
 ("spxw",t_spxw,23000,10,"for"),
 ("gpx",t_gpx,210,10,"for"),
 ("show",t_show,20000,1,"for"),
 ("clear",t_clear,560,1,"for"),
 ("ds1",t_ds1,29000,1,"for"),
 ("ds10",t_ds10,5400,1,"for"),
 ("dm10",t_dm10,2700,1,"for"),
 ("dl10",t_dl10,1900,1,"for"),
 ("dl1",t_dl1,15000,1,"for"),
 ("row",t_row,390,384,None),
 ("fill",t_fill,3,43008,None),
 ("for2",t_for,400000,1,None),
]

run("bm_plot",T)
