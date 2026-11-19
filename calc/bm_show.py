# bm_show: what does show_screen() cost after drawing?
# Film the screen. Top-left block flips black/white
# between timed phases. Do not touch keys until DONE.
#
# The emulator's model (from the Bad Apple film): show_screen()
# returns at once but sends the screen to the LCD for ~6.6 ms;
# drawing before that is done waits. Then pxdK (draw, show, K ms
# of work) costs ~6.6 ms more than dK while K < 6.6, and nothing
# more once K is past it. A fixed cost per show would stay ~6.6 ms.
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
  for i in range(n):
    show_screen()

def t_pxshow(n):
  s=set_pixel;h=show_screen;x=200;y=150;c=R
  for i in range(n):
    s(x,y,c);h()

def t_pxshow2(n):
  s=set_pixel;h=show_screen;x=200;y=150;c=R
  for i in range(n):
    s(x,y,c);h();h()

def t_dsshow(n):
  h=show_screen
  for i in range(n):
    draw_string(200,150,"A",R,"small");h()

# K ms of work: ~7.55 us per empty loop step (bm_plot for)
def t_d2(n):
  for i in range(n):
    for j in range(265):
      pass

def t_d4(n):
  for i in range(n):
    for j in range(530):
      pass

def t_d6(n):
  for i in range(n):
    for j in range(795):
      pass

def t_d8(n):
  for i in range(n):
    for j in range(1060):
      pass

def t_d12(n):
  for i in range(n):
    for j in range(1590):
      pass

def t_pxd2(n):
  s=set_pixel;h=show_screen;x=200;y=150;c=R
  for i in range(n):
    s(x,y,c);h()
    for j in range(265):
      pass

def t_pxd4(n):
  s=set_pixel;h=show_screen;x=200;y=150;c=R
  for i in range(n):
    s(x,y,c);h()
    for j in range(530):
      pass

def t_pxd6(n):
  s=set_pixel;h=show_screen;x=200;y=150;c=R
  for i in range(n):
    s(x,y,c);h()
    for j in range(795):
      pass

def t_pxd8(n):
  s=set_pixel;h=show_screen;x=200;y=150;c=R
  for i in range(n):
    s(x,y,c);h()
    for j in range(1060):
      pass

def t_pxd12(n):
  s=set_pixel;h=show_screen;x=200;y=150;c=R
  for i in range(n):
    s(x,y,c);h()
    for j in range(1590):
      pass

# (name, function, iterations, ops per iteration, baseline test)
T=[
 ("for",t_for,200000,1,None),
 ("show",t_show,20000,1,"for"),
 ("pxshow",t_pxshow,300,1,"for"),
 ("pxshow2",t_pxshow2,300,1,"for"),
 ("dsshow",t_dsshow,300,1,"for"),
 ("d2",t_d2,1000,1,"for"),
 ("pxd2",t_pxd2,300,1,"d2"),
 ("d4",t_d4,500,1,"for"),
 ("pxd4",t_pxd4,300,1,"d4"),
 ("d6",t_d6,330,1,"for"),
 ("pxd6",t_pxd6,300,1,"d6"),
 ("d8",t_d8,250,1,"for"),
 ("pxd8",t_pxd8,250,1,"d8"),
 ("d12",t_d12,170,1,"for"),
 ("pxd12",t_pxd12,170,1,"d12"),
 ("for2",t_for,200000,1,None),
]

run("bm_show",T)
