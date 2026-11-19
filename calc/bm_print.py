# bm_print: print() to the shell
# Film the screen. Top-left block flips black/white
# between timed phases. Do not touch keys until DONE.
# The shell is not redrawn while a script runs, so
# the block shows the phases. If the shell appears
# instead of the block, note it and let it finish.
from casioplot import *
SCALE=1
K=(0,0,0)
W=(255,255,255)

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

# Line lengths 1, 40, 0 and ~4 separate the cost of a
# line from the cost of a character
def t_pshort(n):
  for i in range(n):
    print("x")

def t_plong(n):
  for i in range(n):
    print("........................................")

def t_pempty(n):
  for i in range(n):
    print()

def t_pint(n):
  for i in range(n):
    print(i)

def t_pmulti(n):
  for i in range(n):
    print(i,i,i)

# (name, function, iterations, ops per iteration, baseline test)
# One run measured 216 us per line: N phases of ~3 s
T=[
 ("for",t_for,400000,1,None),
 ("pshort",t_pshort,13000,1,"for"),
 ("plong",t_plong,13000,1,"for"),
 ("pempty",t_pempty,13000,1,"for"),
 ("pint",t_pint,13000,1,"for"),
 ("pmulti",t_pmulti,9000,1,"for"),
 ("pshort2",t_pshort,13000,1,"for"),
 ("for2",t_for,400000,1,None),
]

run("bm_print",T)
