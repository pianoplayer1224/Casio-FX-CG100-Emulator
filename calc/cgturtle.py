# cgturtle: what turtle draws, for the emulator
# Run and film the screen until it stops moving,
# then photograph it. Default speed, pen and turtle.
from turtle import *
for i in range(5):
  forward(80)
  right(144)
penup()
goto(-120,-40)
pendown()
pensize(3)
pencolor("red")
circle(40)
write("turtle")
