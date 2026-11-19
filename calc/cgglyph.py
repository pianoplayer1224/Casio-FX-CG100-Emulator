# cgglyph: the casioplot font, pixel by pixel
# Reads every character back with get_pixel and
# redraws it magnified: one tile per character,
# grey = its advance width, black = its pixels.
# Photograph each page straight on (EXE = next);
# after each size, a table of advance widths.
# Takes ~4 min before the first page, then ~1 min
# between sizes. A red square = probe too small.
from casioplot import *
K=(0,0,0)
W=(255,255,255)
GR=(190,190,190)
R=(255,0,0)
FIRST=32
LAST=126
# probe area per size, x0,x1,y0,y1 around the draw point:
# wider and taller than any glyph (tiles get a red mark
# if ink touches the edge). get_pixel costs ~1.6 ms.
BOX={"small":(-2,12,-3,13),"medium":(-2,17,-3,20),"large":(-2,21,-3,27)}
MAG={"small":4,"medium":3,"large":2}
X0=20
Y0=8

# get_pixel reads back RGB565 (white may be 248,252,248)
def ink(x,y):
  p=get_pixel(x,y)
  return p[0]+p[1]+p[2]<600

def glyph(c,size):
  # rows of c drawn at (X0,Y0): one bitmask per probe row
  # (bit i = column x0+i), and whether ink touched the
  # probe edge. Small ints only: lists of tuples would
  # fragment the heap between get_pixel's garbage.
  x0,x1,y0,y1=BOX[size]
  clear_screen()
  draw_string(X0,Y0,c,K,size)
  rows=[];edge=False
  for y in range(y0,y1):
    b=0
    for x in range(x0,x1):
      if ink(X0+x,Y0+y):
        b|=1<<(x-x0)
    rows.append(b)
  for i in range(len(rows)):
    if rows[i] and (i==0 or i==len(rows)-1 or rows[i]&1 or rows[i]>>(x1-x0-1)):
      edge=True
  return rows,edge

def hibit(b):
  n=-1
  while b:
    b>>=1;n+=1
  return n

def lobit(b):
  n=0
  while not b&1:
    b>>=1;n+=1
  return n

def advance(s,rows,size,before):
  # s ends with a character whose rows are `rows`;
  # `before` = advance of the characters ahead of it.
  # On a row holding its rightmost column, find where
  # its copy starts.
  x0=BOX[size][0];y0=BOX[size][2]
  r=max([hibit(b) for b in rows])
  i=[k for k in range(len(rows)) if rows[k]>>r&1][0]
  rmax=x0+r;lmin=x0+lobit(rows[i]);row=y0+i
  clear_screen()
  draw_string(X0,Y0,s,K,size)
  x=before+rmax+1
  while not ink(X0+x,Y0+row):
    x+=1
    if x>before+60:
      return -1
  return x-lmin

def measure(size):
  G={}
  for code in range(FIRST,LAST+1):
    c=chr(code)
    if c!=" ":
      rows,edge=glyph(c,size)
      G[c]=[advance(c+c,rows,size,0) if max(rows) else -1,rows,edge]
  # space: between two bars, after the bar's advance
  rows=G["|"][1];a=G["|"][0]
  G[" "]=[advance("| |",rows,size,a)-a,[0]*len(rows),False]
  return [G[chr(c)] for c in range(FIRST,LAST+1)]

def wait():
  draw_string(330,182,"EXE",R,"small")
  show_screen()
  try:
    while not getkey():
      pass
    while getkey():
      pass
  except NameError:
    for i in range(200000):
      pass

def block(x,y,m,c):
  for j in range(m):
    for i in range(m):
      set_pixel(x+i,y+j,c)

def pages(size,G):
  m=MAG[size]
  x0,x1,y0,y1=BOX[size]
  # common cell: probe rows that hold ink in any glyph,
  # columns from the leftmost ink to the widest advance
  allrows=0;top=99;bot=-99;wid=0
  for a,rows,e in G:
    for i in range(len(rows)):
      if rows[i]:
        top=min(top,i);bot=max(bot,i)
        allrows|=rows[i]
    wid=max(wid,a-x0)
  lft=lobit(allrows) if allrows else 0
  wid=max(wid,hibit(allrows)+1)-lft
  tw=wid*m+3
  th=(bot-top+1)*m+3
  cols=384//tw
  per=cols*((192-12)//th)
  i=0
  while i<len(G):
    clear_screen()
    draw_string(0,0,"%s %d-%d top %d left %d"%(size,FIRST+i,FIRST+min(i+per,len(G))-1,y0+top,x0+lft),K,"small")
    for k in range(min(per,len(G)-i)):
      a,rows,e=G[i+k]
      tx=(k%cols)*tw
      ty=12+(k//cols)*th
      for yy in range(bot-top+1):
        for xx in range(a-x0-lft):
          block(tx+xx*m,ty+yy*m,m,GR)
        b=rows[top+yy]>>lft
        xx=0
        while b:
          if b&1:
            block(tx+xx*m,ty+yy*m,m,K)
          b>>=1;xx+=1
      if e or a<0:
        block(tx,ty,m,R)
    i+=per
    wait()

def table(size,G):
  # advances as numbers, "code:advance", 8 per row
  clear_screen()
  draw_string(0,0,size+" advance (code:px)",K,"small")
  for k in range(len(G)):
    draw_string((k%8)*48,14+(k//8)*14,"%d:%d"%(FIRST+k,G[k][0]),K,"small")
  wait()

for size in ("small","medium","large"):
  G=measure(size)
  pages(size,G)
  table(size,G)
clear_screen()
draw_string(0,0,"done",K,"medium")
show_screen()
