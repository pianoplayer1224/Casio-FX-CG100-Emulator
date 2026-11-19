# bm_data: lists, dicts, strings, allocation
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

def t_lget(n):
  l=[1,2,3,4,5,6,7,8]
  for i in range(n):
    c=l[3];c=l[3];c=l[3];c=l[3];c=l[3];c=l[3];c=l[3];c=l[3];c=l[3];c=l[3]

def t_lset(n):
  l=[1,2,3,4,5,6,7,8];a=9
  for i in range(n):
    l[3]=a;l[3]=a;l[3]=a;l[3]=a;l[3]=a;l[3]=a;l[3]=a;l[3]=a;l[3]=a;l[3]=a

def t_lapp(n):
  for i in range(n):
    l=[];l.append(i);l.append(i);l.append(i);l.append(i);l.append(i);l.append(i);l.append(i);l.append(i);l.append(i);l.append(i)

def t_lnew(n):
  for i in range(n):
    l=[];l=[];l=[];l=[];l=[];l=[];l=[];l=[];l=[];l=[]

def t_slice(n):
  l=[1,2,3,4,5,6,7,8]
  for i in range(n):
    c=l[1:5];c=l[1:5];c=l[1:5];c=l[1:5];c=l[1:5];c=l[1:5];c=l[1:5];c=l[1:5];c=l[1:5];c=l[1:5]

def t_tget(n):
  t=(1,2,3,4,5,6,7,8)
  for i in range(n):
    c=t[3];c=t[3];c=t[3];c=t[3];c=t[3];c=t[3];c=t[3];c=t[3];c=t[3];c=t[3]

def t_unpk(n):
  t=(1,2)
  for i in range(n):
    a,b=t;a,b=t;a,b=t;a,b=t;a,b=t;a,b=t;a,b=t;a,b=t;a,b=t;a,b=t

def t_tnew(n):
  a=1
  for i in range(n):
    c=(a,a);c=(a,a);c=(a,a);c=(a,a);c=(a,a);c=(a,a);c=(a,a);c=(a,a);c=(a,a);c=(a,a)

def t_dget(n):
  d={"k":1,"j":2}
  for i in range(n):
    c=d["k"];c=d["k"];c=d["k"];c=d["k"];c=d["k"];c=d["k"];c=d["k"];c=d["k"];c=d["k"];c=d["k"]

def t_dset(n):
  d={"k":1,"j":2};a=3
  for i in range(n):
    d["k"]=a;d["k"]=a;d["k"]=a;d["k"]=a;d["k"]=a;d["k"]=a;d["k"]=a;d["k"]=a;d["k"]=a;d["k"]=a

def t_din(n):
  d={"k":1,"j":2}
  for i in range(n):
    c="k" in d;c="k" in d;c="k" in d;c="k" in d;c="k" in d;c="k" in d;c="k" in d;c="k" in d;c="k" in d;c="k" in d

def t_scat(n):
  s="abcd";u="efgh"
  for i in range(n):
    c=s+u;c=s+u;c=s+u;c=s+u;c=s+u;c=s+u;c=s+u;c=s+u;c=s+u;c=s+u

def t_sfmt(n):
  for i in range(n):
    c="%d"%i;c="%d"%i;c="%d"%i;c="%d"%i;c="%d"%i;c="%d"%i;c="%d"%i;c="%d"%i;c="%d"%i;c="%d"%i

def t_str(n):
  for i in range(n):
    c=str(i);c=str(i);c=str(i);c=str(i);c=str(i);c=str(i);c=str(i);c=str(i);c=str(i);c=str(i)

def t_sidx(n):
  s="abcdefgh"
  for i in range(n):
    c=s[3];c=s[3];c=s[3];c=s[3];c=s[3];c=s[3];c=s[3];c=s[3];c=s[3];c=s[3]

def t_lcomp(n):
  r=range(10)
  for i in range(n):
    c=[x for x in r]

def t_forl(n):
  l=[0]*100
  for i in range(n):
    for x in l:
      pass

def t_big(n):
  for i in range(n):
    c=[0]*1000

def t_sort(n):
  for i in range(n):
    l=[5,3,8,1,9,2,7,4,6,0];l.sort()

# (name, function, iterations, ops per iteration, baseline test)
T=[
 ("for",t_for,400000,1,None),
 ("lget",t_lget,54000,10,"for"),
 ("lset",t_lset,49000,10,"for"),
 ("lapp",t_lapp,14000,10,"for"),
 ("lnew",t_lnew,6500,10,"for"),
 ("slice",t_slice,4000,10,"for"),
 ("tget",t_tget,54000,10,"for"),
 ("unpk",t_unpk,52000,10,"for"),
 ("tnew",t_tnew,170,10,"for"),
 ("dget",t_dget,37000,10,"for"),
 ("dset",t_dset,34000,10,"for"),
 ("din",t_din,32000,10,"for"),
 ("scat",t_scat,7200,10,"for"),
 ("sfmt",t_sfmt,1900,10,"for"),
 ("str",t_str,1700,10,"for"),
 ("sidx",t_sidx,23000,10,"for"),
 ("lcomp",t_lcomp,14000,1,"for"),
 ("forl",t_forl,8800,100,None),
 ("big",t_big,1500,1,"for"),
 ("sort",t_sort,16000,1,"for"),
 ("for2",t_for,400000,1,None),
]

run("bm_data",T)
