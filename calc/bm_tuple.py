# bm_tuple: why are tuples slow?
# Film the screen. Top-left block flips black/white
# after every block of work. Do not touch keys until DONE.
from casioplot import *
try:
  import gc
except ImportError:
  gc=None
SCALE=1
K=(0,0,0)
W=(255,255,255)
H=None

def mark(c):
  for y in range(64):
    for x in range(128):
      set_pixel(x,y,c)
  show_screen()

def free():
  if gc and hasattr(gc,"mem_free"):
    return str(gc.mem_free())
  return "?"

def run(name,B):
  nb=0
  for b in B:
    nb+=b[4]
  clear_screen()
  draw_string(140,4,name,K,"medium")
  draw_string(140,24,"sections "+str(len(B)),K,"small")
  draw_string(140,38,"edges "+str(nb+2),K,"small")
  draw_string(140,52,"scale "+str(SCALE),K,"small")
  draw_string(140,66,"gc "+("yes" if gc else "no")+" free "+free(),K,"small")
  mark(W)
  mark(K)
  c=K
  for b in B:
    n=int(b[2]*SCALE)
    if b[2]==0:
      n=0
    elif n<1:
      n=1
    for k in range(b[4]):
      b[1](n)
      if c==K:
        c=W
      else:
        c=K
      mark(c)
  mark(W)
  draw_string(140,80,"free "+free(),K,"small")
  draw_string(140,100,"DONE",K,"large")
  show_screen()

def t_idle(n):
  pass

def t_t2(n):
  a=1
  for i in range(n):
    c=(a,a);c=(a,a);c=(a,a);c=(a,a);c=(a,a);c=(a,a);c=(a,a);c=(a,a);c=(a,a);c=(a,a)

def t_l2(n):
  a=1
  for i in range(n):
    c=[a,a];c=[a,a];c=[a,a];c=[a,a];c=[a,a];c=[a,a];c=[a,a];c=[a,a];c=[a,a];c=[a,a]

def t_t1(n):
  a=1
  for i in range(n):
    c=(a,);c=(a,);c=(a,);c=(a,);c=(a,);c=(a,);c=(a,);c=(a,);c=(a,);c=(a,)

def t_t8(n):
  a=1
  for i in range(n):
    c=(a,a,a,a,a,a,a,a);c=(a,a,a,a,a,a,a,a);c=(a,a,a,a,a,a,a,a);c=(a,a,a,a,a,a,a,a);c=(a,a,a,a,a,a,a,a);c=(a,a,a,a,a,a,a,a);c=(a,a,a,a,a,a,a,a);c=(a,a,a,a,a,a,a,a);c=(a,a,a,a,a,a,a,a);c=(a,a,a,a,a,a,a,a)

def t_tk(n):
  for i in range(n):
    c=(1,2);c=(1,2);c=(1,2);c=(1,2);c=(1,2);c=(1,2);c=(1,2);c=(1,2);c=(1,2);c=(1,2)

def t_tl(n):
  L=[1,1];t=tuple
  for i in range(n):
    c=t(L);c=t(L);c=t(L);c=t(L);c=t(L);c=t(L);c=t(L);c=t(L);c=t(L);c=t(L)

def t_gc(n):
  if gc:
    gc.collect()
  t_t2(n)

def t_hold(n):
  global H
  H=None
  H=[[i] for i in range(n)]

def t_free(n):
  global H
  H=None

# (name, function, iterations per block, ops per iteration, blocks)
# Every section has an even number of blocks.
B=[
 ("idle0",t_idle,0,1,8),
 ("t2a",t_t2,100,10,50),
 ("l2",t_l2,2000,10,12),
 ("t2b",t_t2,100,10,24),
 ("t1",t_t1,100,10,12),
 ("t8",t_t8,100,10,12),
 ("tk",t_tk,100,10,12),
 ("tl",t_tl,100,10,12),
 ("gc",t_gc,100,10,12),
 ("hold",t_hold,5000,1,2),
 ("t2live",t_t2,100,10,12),
 ("free",t_free,1,1,2),
 ("t2c",t_t2,100,10,24),
 ("idle1",t_idle,0,1,8),
]

run("bm_tuple",B)
