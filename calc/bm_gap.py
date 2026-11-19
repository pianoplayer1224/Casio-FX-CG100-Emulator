# bm_gap: constructs the other scripts miss
# Film the screen. Top-left block flips black/white
# between timed phases. Do not touch keys until DONE.
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

def t_igt(n):
  a=5;b=7
  for i in range(n):
    c=a>b;c=a>b;c=a>b;c=a>b;c=a>b;c=a>b;c=a>b;c=a>b;c=a>b;c=a>b

def t_ile(n):
  a=5;b=7
  for i in range(n):
    c=a<=b;c=a<=b;c=a<=b;c=a<=b;c=a<=b;c=a<=b;c=a<=b;c=a<=b;c=a<=b;c=a<=b

def t_ieq(n):
  a=5;b=7
  for i in range(n):
    c=a==b;c=a==b;c=a==b;c=a==b;c=a==b;c=a==b;c=a==b;c=a==b;c=a==b;c=a==b

def t_fgt(n):
  a=5.5;b=7.5
  for i in range(n):
    c=a>b;c=a>b;c=a>b;c=a>b;c=a>b;c=a>b;c=a>b;c=a>b;c=a>b;c=a>b

def t_feq(n):
  a=5.5;b=7.5
  for i in range(n):
    c=a==b;c=a==b;c=a==b;c=a==b;c=a==b;c=a==b;c=a==b;c=a==b;c=a==b;c=a==b

def t_neg(n):
  a=5
  for i in range(n):
    c=-a;c=-a;c=-a;c=-a;c=-a;c=-a;c=-a;c=-a;c=-a;c=-a

def t_rng3(n):
  s=1
  for j in range(0,n,s):
    pass

def t_rng(n):
  for i in range(n):
    c=range(10);c=range(10);c=range(10);c=range(10);c=range(10);c=range(10);c=range(10);c=range(10);c=range(10);c=range(10)

def t_sumi(n):
  L=[1]*2000
  for i in range(n):
    c=sum(L)

def t_sumb(n):
  L=[True]*2000
  for i in range(n):
    c=sum(L)

def t_clos(n):
  k=1
  def f(x):
    return k
  for i in range(n):
    c=f(i);c=f(i);c=f(i);c=f(i);c=f(i);c=f(i);c=f(i);c=f(i);c=f(i);c=f(i)

def t_deref(n):
  k=1
  def inner():
    for i in range(n):
      c=k;c=k;c=k;c=k;c=k;c=k;c=k;c=k;c=k;c=k
    return k
  inner()

def t_swap(n):
  l=[1,2,3];j=0
  for i in range(n):
    l[j],l[j+1]=l[j+1],l[j];l[j],l[j+1]=l[j+1],l[j];l[j],l[j+1]=l[j+1],l[j];l[j],l[j+1]=l[j+1],l[j];l[j],l[j+1]=l[j+1],l[j];l[j],l[j+1]=l[j+1],l[j];l[j],l[j+1]=l[j+1],l[j];l[j],l[j+1]=l[j+1],l[j];l[j],l[j+1]=l[j+1],l[j];l[j],l[j+1]=l[j+1],l[j]

def t_lcmp(n):
  l=[1,2,3];j=0
  for i in range(n):
    c=l[j]>l[j+1];c=l[j]>l[j+1];c=l[j]>l[j+1];c=l[j]>l[j+1];c=l[j]>l[j+1];c=l[j]>l[j+1];c=l[j]>l[j+1];c=l[j]>l[j+1];c=l[j]>l[j+1];c=l[j]>l[j+1]

def t_sadd(n):
  for i in range(n):
    s="";s=s+",";s=s+",";s=s+",";s=s+",";s=s+",";s=s+",";s=s+",";s=s+",";s=s+",";s=s+","

def t_sstr(n):
  k=7
  for i in range(n):
    c=str(k);c=str(k);c=str(k);c=str(k);c=str(k);c=str(k);c=str(k);c=str(k);c=str(k);c=str(k)

# (name, function, iterations, ops per iteration, baseline test)
# Counts from the emulator's first cost model: N phases of ~2.5-5 s
T=[
 ("for",t_for,400000,1,None),
 ("igt",t_igt,71000,10,"for"),
 ("ile",t_ile,71000,10,"for"),
 ("ieq",t_ieq,64000,10,"for"),
 ("fgt",t_fgt,29000,10,"for"),
 ("feq",t_feq,26000,10,"for"),
 ("neg",t_neg,98000,10,"for"),
 ("rng3",t_rng3,890000,1,None),
 ("rng",t_rng,6700,10,"for"),
 ("sumi",t_sumi,490,1,"for"),
 ("sumb",t_sumb,170,1,"for"),
 ("clos",t_clos,7100,10,"for"),
 ("deref",t_deref,150000,10,"for"),
 ("swap",t_swap,170,10,"for"),
 ("lcmp",t_lcmp,21000,10,"for"),
 ("sadd",t_sadd,2600,10,"for"),
 ("sstr",t_sstr,1700,10,"for"),
 ("for2",t_for,400000,1,None),
]

run("bm_gap",T)
