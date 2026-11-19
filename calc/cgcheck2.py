# cgcheck2: the builtins still unaccounted for
# Photograph the shell (1 screen).
# dir(builtins) is 84 here, 89 in the emulator:
# lists the emulator's names this calculator lacks.

# Largest single allocation (bytes: bytearray is missing)
def largest():
  lo=0;hi=1100000
  while hi-lo>1000:
    m=(lo+hi)//2
    try:
      b=bytes(m)
      b=None
      lo=m
    except Exception:
      hi=m
  return lo
try:
  big=largest()
except Exception as e:
  big=str(type(e))

# The emulator's builtins, less the 5 cgcheck found missing
E=(
 "ArithmeticError","AssertionError","AttributeError",
 "BaseException","EOFError","Ellipsis","Exception",
 "GeneratorExit","ImportError","IndentationError",
 "IndexError","KeyError","KeyboardInterrupt","LookupError",
 "MemoryError","NameError","NotImplemented",
 "NotImplementedError","OSError","OverflowError",
 "RuntimeError","StopAsyncIteration","StopIteration",
 "SyntaxError","SystemExit","TypeError","ValueError",
 "ZeroDivisionError","__build_class__","__import__",
 "__name__","__repl_print__","abs","all","any","bin","bool",
 "bytes","callable","chr","classmethod","compile","complex",
 "dict","dir","divmod","eval","exec","float","getattr",
 "globals","hasattr","hash","hex","id","input","int",
 "isinstance","issubclass","iter","len","list","locals","map",
 "max","memoryview","min","next","object","oct","open","ord",
 "pow","print","property","range","repr","round","set",
 "setattr","slice","sorted","staticmethod","str","sum",
 "super","tuple","type","zip",
)
B=dir(__import__("builtins"))
miss=[n for n in E if n not in B]
extra=[n for n in B if n not in E]
print("largest bytes",big)
print("dir",len(B),"missing",len(miss))
s=""
for n in miss+["|"]+extra:
  if s and len(s)+1+len(n)>38:
    print(s)
    s=""
  s=(s+" "+n) if s else n
print(s)
