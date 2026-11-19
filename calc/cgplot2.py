# cgplot2: pyplot with a window set, for the emulator
# Run and photograph the screen straight on.
import matplotlib.pyplot as plt
plt.axis([-3,3,-1,9])
x=[i/10 for i in range(-30,31)]
plt.plot(x,[v*v for v in x],"r")
plt.scatter([-2,0,2],[1,2,3])
plt.bar([1,2],[4,6],0.5)
plt.arrow(-2,6,1,1)
plt.text(-2.8,8,"y=x^2")
plt.grid(True)
plt.show()
