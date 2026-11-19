# bm_call: functions, methods, attributes, builtins
# Film the screen. Top-left block flips black/white
# between timed phases. Do not touch keys until DONE.
from casioplot import *
import math
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

def f0():
  pass

def f1(a):
  pass

def f3(a,b,c):
  pass

def fd(a,b=2):
  pass

def fr():
  return 1

def fib(k):
  if k<2:
    return k
  return fib(k-1)+fib(k-2)

class P:
  def __init__(self):
    self.x=1
  def m(self):
    pass

def t_for(n):
  for i in range(n):
    pass

def t_call0(n):
  f=f0
  for i in range(n):
    f();f();f();f();f();f();f();f();f();f()

def t_call1(n):
  f=f1;a=1
  for i in range(n):
    f(a);f(a);f(a);f(a);f(a);f(a);f(a);f(a);f(a);f(a)

def t_call3(n):
  f=f3;a=1
  for i in range(n):
    f(a,a,a);f(a,a,a);f(a,a,a);f(a,a,a);f(a,a,a);f(a,a,a);f(a,a,a);f(a,a,a);f(a,a,a);f(a,a,a)

def t_calld(n):
  f=fd;a=1
  for i in range(n):
    f(a);f(a);f(a);f(a);f(a);f(a);f(a);f(a);f(a);f(a)

def t_callkw(n):
  f=fd;a=1
  for i in range(n):
    f(a,b=a);f(a,b=a);f(a,b=a);f(a,b=a);f(a,b=a);f(a,b=a);f(a,b=a);f(a,b=a);f(a,b=a);f(a,b=a)

def t_callg(n):
  for i in range(n):
    f0();f0();f0();f0();f0();f0();f0();f0();f0();f0()

def t_ret(n):
  f=fr
  for i in range(n):
    c=f();c=f();c=f();c=f();c=f();c=f();c=f();c=f();c=f();c=f()

def t_meth(n):
  o=P()
  for i in range(n):
    o.m();o.m();o.m();o.m();o.m();o.m();o.m();o.m();o.m();o.m()

def t_attr(n):
  o=P()
  for i in range(n):
    c=o.x;c=o.x;c=o.x;c=o.x;c=o.x;c=o.x;c=o.x;c=o.x;c=o.x;c=o.x

def t_attrw(n):
  o=P()
  for i in range(n):
    o.x=i;o.x=i;o.x=i;o.x=i;o.x=i;o.x=i;o.x=i;o.x=i;o.x=i;o.x=i

def t_modat(n):
  for i in range(n):
    c=math.pi;c=math.pi;c=math.pi;c=math.pi;c=math.pi;c=math.pi;c=math.pi;c=math.pi;c=math.pi;c=math.pi

def t_new(n):
  for i in range(n):
    c=P()

def t_abs(n):
  a=-5
  for i in range(n):
    c=abs(a);c=abs(a);c=abs(a);c=abs(a);c=abs(a);c=abs(a);c=abs(a);c=abs(a);c=abs(a);c=abs(a)

def t_len(n):
  l=[1,2,3]
  for i in range(n):
    c=len(l);c=len(l);c=len(l);c=len(l);c=len(l);c=len(l);c=len(l);c=len(l);c=len(l);c=len(l)

def t_lam(n):
  f=lambda x:x
  for i in range(n):
    c=f(i);c=f(i);c=f(i);c=f(i);c=f(i);c=f(i);c=f(i);c=f(i);c=f(i);c=f(i)

def t_fib(n):
  for i in range(n):
    fib(12)

# (name, function, iterations, ops per iteration, baseline test)
T=[
 ("for",t_for,390000,1,None),
 ("call0",t_call0,8300,10,"for"),
 ("call1",t_call1,8100,10,"for"),
 ("call3",t_call3,7500,10,"for"),
 ("calld",t_calld,7800,10,"for"),
 ("callkw",t_callkw,7600,10,"for"),
 ("callg",t_callg,7400,10,"for"),
 ("ret",t_ret,8200,10,"for"),
 ("meth",t_meth,4300,10,"for"),
 ("attr",t_attr,30000,10,"for"),
 ("attrw",t_attrw,36000,10,"for"),
 ("modat",t_modat,25000,10,"for"),
 ("new",t_new,24000,1,"for"),
 ("abs",t_abs,14000,10,"for"),
 ("len",t_len,14000,10,"for"),
 ("lam",t_lam,8000,10,"for"),
 ("fib12",t_fib,120,1,"for"),
 ("for2",t_for,390000,1,None),
]

run("bm_call",T)
