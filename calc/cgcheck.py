# cgcheck: which builtins and math functions exist
# Photograph the shell (2 screens).
# y = present, n = missing.
import math

# Largest single allocation, first, while the heap is still empty
# (others measured ~393 KB on a 1.029 MB heap)
def largest():
  lo=0;hi=1100000
  while hi-lo>1000:
    m=(lo+hi)//2
    try:
      b=bytearray(m)
      b=None
      lo=m
    except MemoryError:
      hi=m
  return lo
try:
  big=largest()
except Exception as e:
  big=str(type(e))

# Pack "name:y" entries into lines that fit the 38-column shell
def show(items):
  s=""
  for name,ok in items:
    w=name+(":y" if ok else ":n")
    if s and len(s)+1+len(w)>38:
      print(s)
      s=""
    s=(s+" "+w) if s else w
  if s:
    print(s)

def has_builtin(n):
  try:
    eval(n)
    return True
  except Exception:
    return False

B=("enumerate","filter","frozenset","reversed","UnicodeError","help","zip","map","sorted","min","max","sum","any","all","round","divmod","isinstance","setattr","bytearray","set","input","open","print","ord")
M=("isfinite","isinf","isnan","trunc","copysign","degrees","radians","expm1","log2","log10","acosh","asinh","atanh","erf","erfc","gamma","lgamma","fmod","frexp","ldexp","modf","hypot","atan2","ceil")

print("largest bytearray",big)
print("builtins")
show([(n,has_builtin(n)) for n in B])
print("math")
show([(n,hasattr(math,n)) for n in M])
for name,mod in (("builtins",None),("math",math)):
  try:
    n=len(dir(mod)) if mod else len(dir(__import__("builtins")))
    print("dir",name,n)
  except Exception as e:
    print("dir",name,"err",str(type(e)))
