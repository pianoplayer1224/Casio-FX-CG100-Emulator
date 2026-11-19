# cgshell: the shell's font and open() for writing
# Run, then photograph the shell straight on.
# Lines 1-3: every character; line 4: 40 digits
# (does the shell cut long lines?); then open().
print("".join(chr(c) for c in range(32,64)))
print("".join(chr(c) for c in range(64,96)))
print("".join(chr(c) for c in range(96,127)))
print("0123456789"*4)
f=open("cgshell.txt","w")
print(type(f),f)
try:
  print("read",repr(f.read()))
except Exception as e:
  print("read",type(e))
