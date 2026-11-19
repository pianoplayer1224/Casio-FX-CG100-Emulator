# cgnames: every name in turtle and matplotlib.pyplot
# Shows dir() of each module on the screen, one page
# each: photograph each page, EXE = next page.
from casioplot import *
K=(0,0,0)
R=(255,0,0)

def wait():
  draw_string(330,182,"EXE",R,"small")
  show_screen()
  while not getkey():
    pass
  while getkey():
    pass

def page(title,names):
  clear_screen()
  draw_string(0,0,title+" ("+str(len(names))+")",K,"medium")
  x=0;y=20
  for n in names:
    w=7*len(n)+7
    if x+w>384:
      x=0;y+=12
    draw_string(x,y,n,K,"small")
    x+=w
  wait()

try:
  import turtle
  page("turtle",sorted(dir(turtle)))
except Exception as e:
  page("turtle error",[str(type(e)),str(e)])
try:
  import matplotlib
  page("matplotlib",sorted(dir(matplotlib)))
  import matplotlib.pyplot as plt
  page("pyplot",sorted(dir(plt)))
except Exception as e:
  page("pyplot error",[str(type(e)),str(e)])
