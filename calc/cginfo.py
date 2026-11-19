# cginfo: what this Python has and its limits
# Run once. Writes cginfo.txt if files can be written,
# and prints everything; photograph the shell if not.
out=[]

# Exception class name; this Python's types have no __name__
def tn(e):
  try:
    return type(e).__name__
  except Exception:
    return str(type(e))

def say(*a):
  s=" ".join(str(x) for x in a)
  out.append(s)
  print(s)

say("== modules")
for m in ("builtins","math","cmath","random","casioplot","turtle","matplotl","matplotlib","gc","sys","time","os","array","collections","struct","micropython","ujson","json","re","io","kandinsky","ion"):
  try:
    mod=__import__(m)
    say(m,"yes")
  except Exception as e:
    say(m,"no",tn(e))

say("== dir")
for m in ("builtins","math","random","casioplot","sys","cmath","micropython"):
  try:
    say(m,sorted(dir(__import__(m))))
  except Exception as e:
    say(m,"-",tn(e))

say("== sys")
try:
  import sys
  for k in ("version","implementation","platform","maxsize","byteorder","path","modules"):
    try:
      say(k,getattr(sys,k))
    except Exception as e:
      say(k,"-",tn(e))
except Exception as e:
  say("sys -",tn(e))

say("== numbers")
say("0.1+0.2",repr(0.1+0.2))
say("double",1.0+2**-40!=1.0)
say("sqrt2",repr(2**0.5))
for e in ("1e308*10","1e-320","2**100","10**50//7","1/3","float('nan')","round(2.5)","round(3.14159,2)","int(1e20)","7//-2","-7%3","divmod(7,-2)"):
  try:
    say(e,repr(eval(e)))
  except Exception as x:
    say(e,"err",tn(x),x)

say("== recursion")
d=[0]
def rec(n):
  d[0]=n
  rec(n+1)
try:
  rec(1)
except Exception as e:
  say("depth",d[0],tn(e),e)

say("== strings")
for e in ("'%5.2f'%3.14159","'{:>6}'.format(12)","str(1e16)","str(123456789.123)","'é'","len('é')","chr(9608)","'abc'.upper()","'a,b'.split(',')"):
  try:
    say(e,repr(eval(e)))
  except Exception as x:
    say(e,"err",tn(x),x)

say("== random")
try:
  import random
  random.seed(1)
  say("seed1",random.random(),random.randint(1,100),random.random())
except Exception as e:
  say("random err",tn(e),e)

# Save what we have before the heap tests, which fill memory
say("== file")
try:
  f=open("cginfo.txt","w")
  f.write("\n".join(out)+"\n")
  f.close()
  say("wrote cginfo.txt")
except Exception as e:
  say("no file write",tn(e),e)
say("== heap")
# Each test in its own function so its objects die with the frame
def fill(make):
  L=[]
  try:
    while True:
      L.append(make(len(L)))
  except MemoryError:
    pass
  return len(L)

def largest():
  lo=0;hi=4000000
  while hi-lo>1000:
    m=(lo+hi)//2
    try:
      s="x"*m
      s=None
      lo=m
    except MemoryError:
      hi=m
  return lo

for name,f in (("kb strings",lambda: fill(lambda i:"x"*1000)),("largest string",largest),("2-tuples",lambda: fill(lambda i:(i,i))),("1-lists",lambda: fill(lambda i:[i]))):
  try:
    say(name,f())
  except Exception as e:
    say(name,"err",tn(e),e)

try:
  f=open("cginfo.txt","w")
  f.write("\n".join(out)+"\n")
  f.close()
  say("wrote cginfo.txt")
except Exception as e:
  say("no file write",tn(e),e)
