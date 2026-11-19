# bm_str: what makes string + slow
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

# Controls, as in bm_data (scat) and bm_gap (sadd, sstr)
def t_scat(n):
  s="abcd";u="efgh"
  for i in range(n):
    c=s+u;c=s+u;c=s+u;c=s+u;c=s+u;c=s+u;c=s+u;c=s+u;c=s+u;c=s+u

def t_sadd(n):
  for i in range(n):
    s="";s=s+",";s=s+",";s=s+",";s=s+",";s=s+",";s=s+",";s=s+",";s=s+",";s=s+",";s=s+","

def t_sstr(n):
  k=7
  for i in range(n):
    c=str(k);c=str(k);c=str(k);c=str(k);c=str(k);c=str(k);c=str(k);c=str(k);c=str(k);c=str(k)

# Left side built at run time (a heap string, not an
# interned constant); no literal "wxyv" anywhere, so the
# result is not looked up into an existing constant
def t_hcat(n):
  h="wx";h=h+"yv";u="efgh"
  for i in range(n):
    c=h+u;c=h+u;c=h+u;c=h+u;c=h+u;c=h+u;c=h+u;c=h+u;c=h+u;c=h+u

# Both sides heap strings
def t_hh(n):
  h="wx";h=h+"yv";g="rs";g=g+"tk"
  for i in range(n):
    c=h+g;c=h+g;c=h+g;c=h+g;c=h+g;c=h+g;c=h+g;c=h+g;c=h+g;c=h+g

# bytes: same copy, but no search of the interned strings
def t_bcat(n):
  s=b"abcd";u=b"efgh"
  for i in range(n):
    c=s+u;c=s+u;c=s+u;c=s+u;c=s+u;c=s+u;c=s+u;c=s+u;c=s+u;c=s+u

# Result length 2, 16, 32, 64
def t_c2(n):
  s="q";u="z"
  for i in range(n):
    c=s+u;c=s+u;c=s+u;c=s+u;c=s+u;c=s+u;c=s+u;c=s+u;c=s+u;c=s+u

def t_c16(n):
  s="abcdefgh";u="ijklmnop"
  for i in range(n):
    c=s+u;c=s+u;c=s+u;c=s+u;c=s+u;c=s+u;c=s+u;c=s+u;c=s+u;c=s+u

def t_c32(n):
  s="abcdefghijklmnop";u="qrstuvwxyzABCDEF"
  for i in range(n):
    c=s+u;c=s+u;c=s+u;c=s+u;c=s+u;c=s+u;c=s+u;c=s+u;c=s+u;c=s+u

def t_c64(n):
  s="abcdefghijklmnopqrstuvwxyzABCDEF";u="GHIJKLMNOPQRSTUVWXYZ0123456789-_"
  for i in range(n):
    c=s+u;c=s+u;c=s+u;c=s+u;c=s+u;c=s+u;c=s+u;c=s+u;c=s+u;c=s+u

# Growing string to 50 characters, as text building does
def t_grow(n):
  for i in range(n):
    s=""
    for k in range(5):
      s=s+"x";s=s+"x";s=s+"x";s=s+"x";s=s+"x";s=s+"x";s=s+"x";s=s+"x";s=s+"x";s=s+"x"

# += instead of +
def t_iadd(n):
  s="abcd";u="efgh"
  for i in range(n):
    c=s;c+=u;c=s;c+=u;c=s;c+=u;c=s;c+=u;c=s;c+=u;c=s;c+=u;c=s;c+=u;c=s;c+=u;c=s;c+=u;c=s;c+=u

# str() of a 5-digit int (sstr is 1 digit)
def t_str5(n):
  k=12345
  for i in range(n):
    c=str(k);c=str(k);c=str(k);c=str(k);c=str(k);c=str(k);c=str(k);c=str(k);c=str(k);c=str(k)

def t_join(n):
  L=["ab","cd","ef","gh","ij","kl","mn","op","qr","st"]
  for i in range(n):
    c=",".join(L)

# (name, function, iterations, ops per iteration, baseline test)
# Controls from measured times, the rest from the emulator: N phases ~2-5 s
T=[
 ("for",t_for,400000,1,None),
 ("scat",t_scat,7000,10,"for"),
 ("sadd",t_sadd,2600,10,"for"),
 ("sstr",t_sstr,1900,10,"for"),
 ("hcat",t_hcat,4500,10,"for"),
 ("hh",t_hh,4500,10,"for"),
 ("bcat",t_bcat,4500,10,"for"),
 ("c2",t_c2,4500,10,"for"),
 ("c16",t_c16,4500,10,"for"),
 ("c32",t_c32,4500,10,"for"),
 ("c64",t_c64,4500,10,"for"),
 ("grow",t_grow,500,50,"for"),
 ("iadd",t_iadd,6500,10,"for"),
 ("str5",t_str5,1700,10,"for"),
 ("join",t_join,25000,1,"for"),
 ("for2",t_for,400000,1,None),
]

run("bm_str",T)
