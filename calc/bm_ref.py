# bm_ref: whole programs used to check the emulator
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

def sieve(m):
  p=[True]*(m+1)
  p[0]=p[1]=False
  i=2
  while i*i<=m:
    if p[i]:
      for j in range(i*i,m+1,i):
        p[j]=False
    i+=1
  return sum(p)

def queens(m):
  def ok(b,r,c):
    for k in range(r):
      if b[k]==c or abs(b[k]-c)==r-k:
        return False
    return True
  def go(b,r):
    if r==m:
      return 1
    s=0
    for c in range(m):
      if ok(b,r,c):
        b[r]=c
        s+=go(b,r+1)
    return s
  return go([0]*m,0)

def isprime(k):
  if k<2 or k%2==0:
    return k==2
  d=3
  while d*d<=k:
    if k%d==0:
      return False
    d+=2
  return True

def series(e):
  s=0.0;k=1
  while 1/(k*k)>e:
    s+=1/(k*k)
    k+=1
  return s

def bubble(l):
  m=len(l)
  for i in range(m):
    for j in range(m-1-i):
      if l[j]>l[j+1]:
        l[j],l[j+1]=l[j+1],l[j]
  return l

def mandel(x0,y0,w,h):
  for py in range(h):
    for px in range(w):
      cr=-2.0+px*3.0/w;ci=-1.2+py*2.4/h
      zr=0.0;zi=0.0;k=0
      while k<16 and zr*zr+zi*zi<4.0:
        zr,zi=zr*zr-zi*zi+cr,2*zr*zi+ci
        k+=1
      set_pixel(x0+px,y0+py,(k*16,k*8,255-k*16))

def t_for(n):
  for i in range(n):
    pass

def t_sieve(n):
  for i in range(n):
    sieve(2000)

def t_queens(n):
  for i in range(n):
    queens(6)

def t_prime(n):
  for i in range(n):
    isprime(1000003)

def t_series(n):
  for i in range(n):
    series(0.0001)

def t_bubble(n):
  for i in range(n):
    bubble([9,3,7,1,8,2,6,0,5,4,19,13,17,11,18,12,16,10,15,14])

def t_mandel(n):
  for i in range(n):
    mandel(140,90,60,40)

def t_trig(n):
  s=0.0
  for i in range(n):
    s+=sin(i*0.01)*cos(i*0.02)+sqrt(i)

def t_text(n):
  for i in range(n):
    s=""
    for k in range(20):
      s+=str(k)+","

# (name, function, iterations, ops per iteration, baseline test)
T=[
 ("for",t_for,400000,1,None),
 ("sieve",t_sieve,62,1,None),
 ("queens",t_queens,24,1,None),
 ("prime",t_prime,470,1,None),
 ("series",t_series,260,1,None),
 ("bubble",t_bubble,370,1,None),
 ("mandel",t_mandel,1,1,None),
 ("trig",t_trig,7600,1,None),
 ("text",t_text,360,1,None),
 ("for2",t_for,400000,1,None),
]

run("bm_ref",T)
