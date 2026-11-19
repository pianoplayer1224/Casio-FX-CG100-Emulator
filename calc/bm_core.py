# bm_core: loops, integers, variables
# Film the screen. Top-left block flips black/white
# between timed phases. Do not touch keys until DONE.
from casioplot import *
SCALE=1
K=(0,0,0)
W=(255,255,255)
G=7

def mark(c):
  for y in range(64):
    for x in range(128):
      set_pixel(x,y,c)
  show_screen()

def run(name,T):
  clear_screen()
  draw_string(140,4,name,K,"medium")
  draw_string(140,24,"tests "+str(len(T)),K,"small")
  draw_string(140,38,"edges "+str(2*len(T)+2),K,"small")
  draw_string(140,52,"scale "+str(SCALE),K,"small")
  mark(W)
  mark(K)
  c=K
  for t in T:
    n=int(t[2]*SCALE)
    if n<1:
      n=1
    for m in (n,2*n):
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

def t_while(n):
  i=0
  while i<n:
    i+=1

def t_iadd(n):
  a=12345;b=678
  for i in range(n):
    c=a+b;c=a+b;c=a+b;c=a+b;c=a+b;c=a+b;c=a+b;c=a+b;c=a+b;c=a+b

def t_isub(n):
  a=12345;b=678
  for i in range(n):
    c=a-b;c=a-b;c=a-b;c=a-b;c=a-b;c=a-b;c=a-b;c=a-b;c=a-b;c=a-b

def t_imul(n):
  a=12345;b=678
  for i in range(n):
    c=a*b;c=a*b;c=a*b;c=a*b;c=a*b;c=a*b;c=a*b;c=a*b;c=a*b;c=a*b

def t_idiv(n):
  a=12345;b=678
  for i in range(n):
    c=a//b;c=a//b;c=a//b;c=a//b;c=a//b;c=a//b;c=a//b;c=a//b;c=a//b;c=a//b

def t_imod(n):
  a=12345;b=678
  for i in range(n):
    c=a%b;c=a%b;c=a%b;c=a%b;c=a%b;c=a%b;c=a%b;c=a%b;c=a%b;c=a%b

def t_icmp(n):
  a=12345;b=678
  for i in range(n):
    c=a<b;c=a<b;c=a<b;c=a<b;c=a<b;c=a<b;c=a<b;c=a<b;c=a<b;c=a<b

def t_ibit(n):
  a=12345;b=678
  for i in range(n):
    c=a&b;c=a|b;c=a^b;c=a<<3;c=a>>3;c=a&b;c=a|b;c=a^b;c=a<<3;c=a>>3

def t_iaug(n):
  c=0
  for i in range(n):
    c+=1;c+=1;c+=1;c+=1;c+=1;c+=1;c+=1;c+=1;c+=1;c+=1

def t_badd(n):
  a=2**70+12345;b=2**69+678
  for i in range(n):
    c=a+b;c=a+b;c=a+b;c=a+b;c=a+b;c=a+b;c=a+b;c=a+b;c=a+b;c=a+b

def t_bmul(n):
  a=2**70+12345;b=2**69+678
  for i in range(n):
    c=a*b;c=a*b;c=a*b;c=a*b;c=a*b;c=a*b;c=a*b;c=a*b;c=a*b;c=a*b

def t_bpow(n):
  a=3
  for i in range(n):
    c=a**200

def t_loc(n):
  a=5
  for i in range(n):
    c=a;c=a;c=a;c=a;c=a;c=a;c=a;c=a;c=a;c=a

def t_glob(n):
  for i in range(n):
    c=G;c=G;c=G;c=G;c=G;c=G;c=G;c=G;c=G;c=G

def t_if(n):
  a=1
  for i in range(n):
    if a:
      pass
    if a:
      pass
    if a:
      pass
    if a:
      pass
    if a:
      pass

# (name, function, iterations, ops per iteration, baseline test)
T=[
 ("for",t_for,690000,1,None),
 ("while",t_while,710000,1,None),
 ("iadd",t_iadd,120000,10,"for"),
 ("isub",t_isub,120000,10,"for"),
 ("imul",t_imul,100000,10,"for"),
 ("idiv",t_idiv,110000,10,"for"),
 ("imod",t_imod,110000,10,"for"),
 ("icmp",t_icmp,120000,10,"for"),
 ("ibit",t_ibit,120000,10,"for"),
 ("iaug",t_iaug,120000,10,"for"),
 ("badd",t_badd,7400,10,"for"),
 ("bmul",t_bmul,5400,10,"for"),
 ("bpow",t_bpow,4600,1,"for"),
 ("loc",t_loc,300000,10,"for"),
 ("glob",t_glob,80000,10,"for"),
 ("if",t_if,320000,5,"for"),
 ("for2",t_for,690000,1,None),
]

run("bm_core",T)
