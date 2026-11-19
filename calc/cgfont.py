# cgfont: font chart and key codes
# Page 1: small+medium chars. Page 2: large chars.
# Photograph each page straight on, close up.
# Page 3: key codes. Press keys row by row from
# top-left (skip AC), then photograph the codes.
from casioplot import *
K=(0,0,0)
W=(255,255,255)
G=(255,0,0)
CH=[chr(c) for c in range(32,127)]

def wait():
  draw_string(300,180,"press EXE",G,"small")
  show_screen()
  # wait for any key, then for release (getkey() is None with no key)
  try:
    while not getkey():
      pass
    while getkey():
      pass
  except NameError:
    for i in range(200000):
      pass

def chart(y,size,per):
  for i in range(0,len(CH),per):
    draw_string(0,y,"".join(CH[i:i+per]),K,size)
    y+={"small":12,"medium":18,"large":24}[size]
  return y

clear_screen()
y=chart(0,"small",48)
# Pixel ruler: one pixel every 2, to check alignment
for x in range(0,384,2):
  set_pixel(x,y+2,K)
y=chart(y+6,"medium",32)
draw_string(0,y,"Wg|",K,"small")
draw_string(30,y,"Wg|",K,"medium")
draw_string(70,y,"Wg|",K,"large")
wait()
clear_screen()
y=chart(0,"large",24)
draw_string(0,y+4,"colour",(255,0,0),"medium")
draw_string(80,y+4,"colour",(0,0,255),"large")
draw_string(200,y+4,"bg",(10,200,10),"large")
wait()
clear_screen()
draw_string(0,0,"press keys; AC stops",K,"medium")
show_screen()
i=0;last=-1
try:
  while True:
    k=getkey()
    if k and k!=last:
      draw_string((i//13)*48,24+(i%13)*12,str(k),K,"small")
      i+=1
      show_screen()
    last=k
except NameError:
  draw_string(0,40,"no getkey()",K,"medium")
  show_screen()
