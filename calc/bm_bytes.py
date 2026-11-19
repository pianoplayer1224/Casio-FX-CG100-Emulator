# bm_bytes: does bytes[i] or len(bytes) depend on size, index, contents or how the object was made?
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

# Sizes, all ASCII and no zero bytes
B1=b"A"*256
B2=b"A"*2576
B3=b"A"*25600
B4=b"A"*256000
# Same size as B2, other contents or origin. BW is built like bm_mac's weights
BW=bytes([(i*37+(i>>3))%256 for i in range(2576)])
BA=b"\xaa"*2576
BS=B3[100:2676]
# A constant from the source, 210 bytes
BL=b"AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAA"
X64=[(i*11)%255-127 for i in range(64)]

def t_for(n):
  for i in range(n):
    pass

def sub(b,j,n):
  for i in range(n):
    c=b[j];c=b[j];c=b[j];c=b[j];c=b[j];c=b[j];c=b[j];c=b[j];c=b[j];c=b[j]

def ln(b,n):
  for i in range(n):
    c=len(b);c=len(b);c=len(b);c=len(b);c=len(b);c=len(b);c=len(b);c=len(b);c=len(b);c=len(b)

# bytes[i], low index, by size
def t_bs1(n):
  sub(B1,5,n)

def t_bs2(n):
  sub(B2,5,n)

def t_bs3(n):
  sub(B3,5,n)

def t_bs4(n):
  sub(B4,5,n)

# bytes[i], index near the end, by size
def t_bh2(n):
  sub(B2,2571,n)

def t_bh3(n):
  sub(B3,25595,n)

def t_bh4(n):
  sub(B4,255995,n)

# bytes[i], other origins
def t_sw(n):
  sub(BW,5,n)

def t_sl(n):
  sub(BL,5,n)

# len(bytes), by size
def t_bl1(n):
  ln(B1,n)

def t_bl2(n):
  ln(B2,n)

def t_bl3(n):
  ln(B3,n)

def t_bl4(n):
  ln(B4,n)

# len(bytes), same size as bl2: mixed with zeros, non-ASCII, a slice
def t_lw(n):
  ln(BW,n)

def t_la(n):
  ln(BA,n)

def t_ls(n):
  ln(BS,n)

# len(bytes), constant from the source, 210 bytes
def t_ll(n):
  ln(BL,n)

# The model's multiply loop, 64 steps high in a 256,000-byte object (bm_mac mac: 18.80 us)
def t_mac4(n):
  w=B4;x=X64
  for i in range(n):
    s=0;p=200000
    for v in x:
      s+=w[p]*v
      p+=1

# (name, function, iterations, ops per iteration, baseline test)
# Large-object index tests are short in case their cost grows with size or index
T=[
 ("for",t_for,330000,1,None),
 ("bs1",t_bs1,37000,10,"for"),
 ("bs2",t_bs2,37000,10,"for"),
 ("bs3",t_bs3,20000,10,"for"),
 ("bs4",t_bs4,20000,10,"for"),
 ("bh2",t_bh2,37000,10,"for"),
 ("bh3",t_bh3,20000,10,"for"),
 ("bh4",t_bh4,20000,10,"for"),
 ("sw",t_sw,37000,10,"for"),
 ("sl",t_sl,37000,10,"for"),
 ("bl1",t_bl1,10000,10,"for"),
 ("bl2",t_bl2,5500,10,"for"),
 ("bl3",t_bl3,1000,10,"for"),
 ("bl4",t_bl4,105,10,"for"),
 ("lw",t_lw,5500,10,"for"),
 ("la",t_la,5500,10,"for"),
 ("ls",t_ls,5500,10,"for"),
 ("ll",t_ll,10000,10,"for"),
 ("mac4",t_mac4,1000,64,"for"),
 ("for2",t_for,330000,1,None),
]

run("bm_bytes",T)
