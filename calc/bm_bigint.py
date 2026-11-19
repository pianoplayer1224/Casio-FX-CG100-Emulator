# bm_bigint: how fast is big-integer maths on the calculator, and does it have to_bytes and from_bytes?
# The first screen answers the second question without filming: it stops there if either is missing.
# Film the screen. Top-left block flips black/white
# between timed phases. Do not touch keys until DONE 2.
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
  draw_string(140,66,"to_bytes yes",K,"small")
  draw_string(140,80,"from_bytes yes",K,"small")
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
  draw_string(140,110,"DONE 1, WAIT",K,"large")
  show_screen()

def missing(s):
  clear_screen()
  draw_string(4,4,"bm_bigint: no "+s,K,"medium")
  draw_string(4,30,"DONE, nothing to film",K,"medium")
  show_screen()
  raise SystemExit

try:
  (1<<100).to_bytes(16,"little")
except AttributeError:
  missing("to_bytes")
try:
  int.from_bytes(b"abcdefghijkl","little")
except AttributeError:
  missing("from_bytes")

X64=[(i*53)%255-127 for i in range(64)]
B64=bytes([(i*37+11)%93+32 for i in range(64*64)])

def col(n,c):
  a=0
  for j in range(n):
    a=(a<<24)+(j*c)%93+32
  return a

C16=col(16,7)
C64=col(64,7)
C256=col(256,7)
A16=col(16,11)*97
A64=col(64,11)*97
A256=col(256,11)*97
RAW=b"\0\0".join([B64[p:p+1] for p in range(64)])
O64=0
for j in range(64):
  O64=(O64<<24)+(1<<20)
S64=(A64+O64)>>5
BY=S64.to_bytes(192,"little")
CM=[col(64,3+2*i) for i in range(64)]
OK=[0]*64

def t_for(n):
  for i in range(n):
    pass

def t_mul16(n):
  a=C16
  for i in range(n):
    b=a*97

def t_mul64(n):
  a=C64
  for i in range(n):
    b=a*97

def t_mul256(n):
  a=C256
  for i in range(n):
    b=a*97

def t_add16(n):
  a=C16;c=A16
  for i in range(n):
    b=a+c

def t_add64(n):
  a=C64;c=A64
  for i in range(n):
    b=a+c

def t_add256(n):
  a=C256;c=A256
  for i in range(n):
    b=a+c

def t_shr64(n):
  a=A64
  for i in range(n):
    b=a>>5

def t_tob64(n):
  a=S64
  for i in range(n):
    b=a.to_bytes(192,"little")

def t_frb64(n):
  a=RAW
  for i in range(n):
    b=int.from_bytes(a,"little")

def t_join(n):
  w=B64
  for i in range(n):
    b=b"\0\0".join([w[p:p+1] for p in range(5,4096,64)])

# Reading 64 fields back, with the clamp
def t_read(n):
  b=BY;y=OK
  for q in range(n):
    r=0
    i=0
    while i<192:
      v=b[i]+(b[i+1]<<8)-32768
      if v>127:
        v=127
      elif v<-127:
        v=-127
      y[r]=v
      r+=1
      i+=3

# The model's multiply, 64 by 64, the plain way and with big integers
def t_mvp(n):
  w=B64;x=X64;y=OK
  for q in range(n):
    t=79*sum(x)
    p=0
    for r in range(64):
      s=-t
      for v in x:
        s+=w[p]*v
        p+=1
      s>>=5
      if s>127:
        s=127
      elif s<-127:
        s=-127
      y[r]=s

def t_mvb(n):
  a=CM;x=X64;y=OK
  for q in range(n):
    s=O64
    i=0
    for v in x:
      s+=a[i]*v
      i+=1
    b=(s>>5).to_bytes(192,"little")
    r=0
    i=0
    while i<192:
      v=b[i]+(b[i+1]<<8)-32768
      if v>127:
        v=127
      elif v<-127:
        v=-127
      y[r]=v
      r+=1
      i+=3

# (name, function, iterations, ops per iteration, baseline test)
T=[
 ("for",t_for,330000,1,None),
 ("mul16",t_mul16,10000,1,"for"),
 ("mul64",t_mul64,6000,1,"for"),
 ("mul256",t_mul256,2000,1,"for"),
 ("add16",t_add16,10000,1,"for"),
 ("add64",t_add64,6000,1,"for"),
 ("add256",t_add256,2000,1,"for"),
 ("shr64",t_shr64,6000,1,"for"),
 ("tob64",t_tob64,4000,1,"for"),
 ("frb64",t_frb64,4000,1,"for"),
 ("join",t_join,300,1,"for"),
 ("read",t_read,400,64,"for"),
 ("mvp",t_mvp,6,4096,"for"),
 ("mvb",t_mvb,40,1,"for"),
 ("for2",t_for,330000,1,None),
]

run("bm_bigint",T)
LIVE=[bytes(200) for i in range(2500)]
T=[("mvb2",t_mvb,40,1,"for"),("for3",t_for,330000,1,None)]
mark(W)
c=K
for t in T:
  for m in (t[2],2*t[2],2*t[2],t[2]):
    t[1](m)
    if c==K:
      c=W
    else:
      c=K
    mark(c)
mark(W)
draw_string(140,130,"DONE 2",K,"large")
show_screen()
