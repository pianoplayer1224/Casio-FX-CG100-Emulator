# bm_mac: integer neural-net loops (CalcAI)
# Film the screen. Top-left block flips black/white
# between timed phases. Do not touch keys until DONE.
from casioplot import *
from math import exp
from random import seed,random
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

# Model sizes for t_step: width, heads, feed-forward, context, vocab
DM=16
HM=2
FM=32
CM=8
VM=32
DH=DM//HM
PE=VM*DM
NW=PE+3*DM*DM+HM*CM+DM*DM+DM*FM+FM*DM
# Weights as bytes holding w+128, activations as small ints
WB=bytes([(i*37+(i>>3))%256 for i in range(NW)])
X64=[(i*11)%255-127 for i in range(64)]
Y64=[(i*7)%255-127 for i in range(64)]
Y4=[0]*4
EXPT=[int(exp((i-128)/16)*16)+1 for i in range(256)]
KC=[(i*5)%128-64 for i in range(CM*DM)]
VC=[(i*3)%128-64 for i in range(CM*DM)]
QQ=[0]*DM
KK=[0]*DM
VV=[0]*DM
AA=[0]*DM
OO=[0]*DM
XX=[0]*DM
FH=[0]*FM
SC=[0]*CM
LG=[0]*VM

def t_for(n):
  for i in range(n):
    pass

# One operation, 10 per loop
def t_bsub(n):
  b=WB;j=5
  for i in range(n):
    c=b[j];c=b[j];c=b[j];c=b[j];c=b[j];c=b[j];c=b[j];c=b[j];c=b[j];c=b[j]

def t_lsub(n):
  l=X64;j=5
  for i in range(n):
    c=l[j];c=l[j];c=l[j];c=l[j];c=l[j];c=l[j];c=l[j];c=l[j];c=l[j];c=l[j]

def t_lset(n):
  l=[0]*8;j=5;v=9
  for i in range(n):
    l[j]=v;l[j]=v;l[j]=v;l[j]=v;l[j]=v;l[j]=v;l[j]=v;l[j]=v;l[j]=v;l[j]=v

def t_blen(n):
  b=WB
  for i in range(n):
    c=len(b);c=len(b);c=len(b);c=len(b);c=len(b);c=len(b);c=len(b);c=len(b);c=len(b);c=len(b)

def t_bmul(n):
  b=WB;j=5;v=-93
  for i in range(n):
    c=b[j]*v;c=b[j]*v;c=b[j]*v;c=b[j]*v;c=b[j]*v;c=b[j]*v;c=b[j]*v;c=b[j]*v;c=b[j]*v;c=b[j]*v

# 64 steps per loop, cost per step
def t_lit(n):
  x=X64
  for i in range(n):
    for v in x:
      pass

def t_mac(n):
  w=WB;x=X64
  for i in range(n):
    s=0;p=0
    for v in x:
      s+=w[p]*v
      p+=1

def t_lmac(n):
  w=Y64;x=X64
  for i in range(n):
    s=0;p=0
    for v in x:
      s+=w[p]*v
      p+=1

def t_dot(n):
  a=X64;b=Y64
  for i in range(n):
    s=0;q=0;j=0
    for u in range(64):
      s+=a[q]*b[j]
      q+=1
      j+=1

# sum() of a short list: is the cost per item or per call?
def t_sum(n):
  x=X64
  for i in range(n):
    c=sum(x)

# From CalcAI bench/template.py, same code as the timed models
def mv(p,R,x,y):
  w=WB
  t=128*sum(x)
  for r in range(R):
    s=-t
    for v in x:
      s+=w[p]*v
      p+=1
    s>>=7
    if s>127:
      s=127
    elif s<-127:
      s=-127
    y[r]=s
  return p

def norm(x):
  s=1
  for v in x:
    s+=v*v
  k=int(16384/(s/DM)**0.5)
  if k!=256:
    i=0
    for v in x:
      x[i]=(v*k)>>8
      i+=1

def block(x,slot):
  norm(x)
  p=mv(PE,DM,x,QQ)
  p=mv(p,DM,x,KK)
  p=mv(p,DM,x,VV)
  b=slot*DM
  i=b
  for v in KK:
    KC[i]=v
    i+=1
  i=b
  for v in VV:
    VC[i]=v
    i+=1
  w=WB
  e=EXPT
  sc=SC
  for h in range(HM):
    o=h*DH
    for c in range(CM):
      q=o
      i=c*DM+o
      s=0
      for u in range(DH):
        s+=QQ[q]*KC[i]
        q+=1
        i+=1
      s=(s>>9)+w[p+h*CM+(slot-c)%CM]-128
      if s>127:
        s=127
      elif s<-128:
        s=-128
      sc[c]=e[s+128]
    tot=sum(sc)+1
    for j in range(DH):
      s=0
      i=o+j
      for a in sc:
        s+=a*VC[i]
        i+=DM
      AA[o+j]=s//tot
  p+=HM*CM
  p=mv(p,DM,AA,OO)
  i=0
  for v in OO:
    x[i]+=v
    i+=1
  norm(x)
  p=mv(p,FM,x,FH)
  i=0
  for v in FH:
    if v<0:
      FH[i]=0
    i+=1
  mv(p,DM,FH,OO)
  i=0
  for v in OO:
    x[i]+=v
    i+=1

def step(tok,slot):
  p=tok*DM
  w=WB
  i=0
  while i<DM:
    XX[i]=w[p]-128
    p+=1
    i+=1
  block(XX,slot)
  norm(XX)
  mv(0,VM,XX,LG)
  m=max(LG)
  tot=0
  pr=[]
  for v in LG:
    s=v-m+255
    if s<0:
      s=0
    a=EXPT[s]
    tot+=a
    pr.append(a)
  r=random()*tot
  i=0
  for a in pr:
    r-=a
    if r<=0:
      return i
    i+=1
  return 0

# A 4x64 matrix-vector product, cost per multiply
def t_mv(n):
  for i in range(n):
    mv(0,4,X64,Y4)

# One norm, 16 values
def t_norm(n):
  x=X64[:16]
  for i in range(n):
    x[3]=40
    norm(x)

# Whole program: one token of a 1-layer model
def t_step(n):
  seed(1)
  tok=1
  slot=0
  for i in range(n):
    tok=step(tok,slot)
    slot=(slot+1)%CM

# (name, function, iterations, ops per iteration, baseline test)
T=[
 ("for",t_for,400000,1,None),
 ("bsub",t_bsub,97000,10,"for"),
 ("lsub",t_lsub,52000,10,"for"),
 ("lset",t_lset,48000,10,"for"),
 ("blen",t_blen,13900,10,"for"),
 ("bmul",t_bmul,46000,10,"for"),
 ("lit",t_lit,13000,64,"for"),
 ("mac",t_mac,3100,64,"for"),
 ("lmac",t_lmac,2600,64,"for"),
 ("dot",t_dot,1600,64,"for"),
 ("sum",t_sum,3000,1,"for"),
 ("mv",t_mv,380,256,"for"),
 ("norm",t_norm,6500,1,"for"),
 ("step",t_step,31,1,"for"),
 ("for2",t_for,400000,1,None),
]

run("bm_mac",T)
