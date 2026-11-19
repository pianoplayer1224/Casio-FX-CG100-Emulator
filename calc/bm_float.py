# bm_float: floats and math module
# Film the screen. Top-left block flips black/white
# between timed phases. Do not touch keys until DONE.
from casioplot import *
from math import *
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

def t_fadd(n):
  a=1.2345;b=6.789
  for i in range(n):
    c=a+b;c=a+b;c=a+b;c=a+b;c=a+b;c=a+b;c=a+b;c=a+b;c=a+b;c=a+b

def t_fsub(n):
  a=1.2345;b=6.789
  for i in range(n):
    c=a-b;c=a-b;c=a-b;c=a-b;c=a-b;c=a-b;c=a-b;c=a-b;c=a-b;c=a-b

def t_fmul(n):
  a=1.2345;b=6.789
  for i in range(n):
    c=a*b;c=a*b;c=a*b;c=a*b;c=a*b;c=a*b;c=a*b;c=a*b;c=a*b;c=a*b

def t_fdiv(n):
  a=1.2345;b=6.789
  for i in range(n):
    c=a/b;c=a/b;c=a/b;c=a/b;c=a/b;c=a/b;c=a/b;c=a/b;c=a/b;c=a/b

def t_fcmp(n):
  a=1.2345;b=6.789
  for i in range(n):
    c=a<b;c=a<b;c=a<b;c=a<b;c=a<b;c=a<b;c=a<b;c=a<b;c=a<b;c=a<b

def t_mix(n):
  a=12;b=6.789
  for i in range(n):
    c=a*b;c=a*b;c=a*b;c=a*b;c=a*b;c=a*b;c=a*b;c=a*b;c=a*b;c=a*b

def t_idivf(n):
  a=12;b=7
  for i in range(n):
    c=a/b;c=a/b;c=a/b;c=a/b;c=a/b;c=a/b;c=a/b;c=a/b;c=a/b;c=a/b

def t_fpow(n):
  a=1.2345;b=2.5
  for i in range(n):
    c=a**b;c=a**b;c=a**b;c=a**b;c=a**b;c=a**b;c=a**b;c=a**b;c=a**b;c=a**b

def t_conv(n):
  a=12;b=6.789
  for i in range(n):
    c=float(a);c=int(b);c=float(a);c=int(b);c=float(a);c=int(b);c=float(a);c=int(b);c=float(a);c=int(b)

def t_sqrt(n):
  a=6.789
  for i in range(n):
    c=sqrt(a);c=sqrt(a);c=sqrt(a);c=sqrt(a);c=sqrt(a);c=sqrt(a);c=sqrt(a);c=sqrt(a);c=sqrt(a);c=sqrt(a)

def t_sin(n):
  a=0.789
  for i in range(n):
    c=sin(a);c=sin(a);c=sin(a);c=sin(a);c=sin(a);c=sin(a);c=sin(a);c=sin(a);c=sin(a);c=sin(a)

def t_cos(n):
  a=0.789
  for i in range(n):
    c=cos(a);c=cos(a);c=cos(a);c=cos(a);c=cos(a);c=cos(a);c=cos(a);c=cos(a);c=cos(a);c=cos(a)

def t_atan(n):
  a=0.789
  for i in range(n):
    c=atan(a);c=atan(a);c=atan(a);c=atan(a);c=atan(a);c=atan(a);c=atan(a);c=atan(a);c=atan(a);c=atan(a)

def t_exp(n):
  a=0.789
  for i in range(n):
    c=exp(a);c=exp(a);c=exp(a);c=exp(a);c=exp(a);c=exp(a);c=exp(a);c=exp(a);c=exp(a);c=exp(a)

def t_log(n):
  a=6.789
  for i in range(n):
    c=log(a);c=log(a);c=log(a);c=log(a);c=log(a);c=log(a);c=log(a);c=log(a);c=log(a);c=log(a)

def t_floor(n):
  a=6.789
  for i in range(n):
    c=floor(a);c=floor(a);c=floor(a);c=floor(a);c=floor(a);c=floor(a);c=floor(a);c=floor(a);c=floor(a);c=floor(a)

# (name, function, iterations, ops per iteration, baseline test)
T=[
 ("for",t_for,400000,1,None),
 ("fadd",t_fadd,9400,10,"for"),
 ("fsub",t_fsub,9400,10,"for"),
 ("fmul",t_fmul,9300,10,"for"),
 ("fdiv",t_fdiv,8500,10,"for"),
 ("fcmp",t_fcmp,29000,10,"for"),
 ("mix",t_mix,9400,10,"for"),
 ("idivf",t_idivf,9400,10,"for"),
 ("fpow",t_fpow,1800,10,"for"),
 ("conv",t_conv,6600,10,"for"),
 ("sqrt",t_sqrt,4700,10,"for"),
 ("sin",t_sin,3500,10,"for"),
 ("cos",t_cos,3400,10,"for"),
 ("atan",t_atan,2400,10,"for"),
 ("exp",t_exp,2600,10,"for"),
 ("log",t_log,3200,10,"for"),
 ("floor",t_floor,12000,10,"for"),
 ("for2",t_for,400000,1,None),
]

run("bm_float",T)
