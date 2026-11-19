"""Screenshots of the emulator without a window.

    python3 tools/emushot.py SCRIPT.py OUTDIR ["typed lines"]

Runs SCRIPT.py in the emulator (fast) with a fake viewer and saves the
384x216 panel (2x, PNG) as OUTDIR/pageNN.png whenever it waits:
- for a line (input() or the ">>>" prompt): the next of the typed lines
  (separated by real newlines) is typed, as in the window;
- for nothing (a drawing held, or a getkey() loop) for a second: EXE is
  pressed.
When a line is wanted and none are left, the screen is saved as
OUTDIR/final.png and the window is "closed".
"""
import mmap, os, struct, subprocess, sys, time
import numpy as np
from PIL import Image
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EMU = os.path.join(ROOT, "emu/micropython/ports/cg100/micropython")
script, outdir = os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2])
typed = sys.argv[3].split("\n") if len(sys.argv) > 3 else []
os.makedirs(outdir, exist_ok=True)
shm = os.path.join(outdir, "shm")
# emu/micropython/ports/cg100/cgshm.h
H = 20; V = 384 * 216 * 2
WAIT, BREAKS, HEAD, TAIL, BUF = H + V, H + V + 4, H + V + 8, H + V + 12, H + V + 16
IN_SIZE = 256; size = BUF + IN_SIZE
WAIT_KEY, WAIT_INPUT, WAIT_REPL = 1, 2, 3
with open(shm, "wb") as f:
    f.write(struct.pack("<IIIII", 0x43473132, 0, 0, 0, 0) + b"\xff" * V + b"\0" * (size - H - V))
m = mmap.mmap(os.open(shm, os.O_RDWR), size)
env = dict(os.environ, CG100_SHM=shm, CG100_FAST="1",
           CG100_COSTS=os.path.join(ROOT, "emu/costs.txt"),
           MICROPYPATH=os.path.join(ROOT, "emu/lib"))
def u32(off):
    return struct.unpack_from("<I", m, off)[0]
def save(name):
    v = np.frombuffer(m, dtype="<u2", count=384 * 216, offset=H).reshape(216, 384)
    rgb = np.dstack([((v >> 11) & 31) * 255 // 31, ((v >> 5) & 63) * 255 // 63, (v & 31) * 255 // 31]).astype(np.uint8)
    Image.fromarray(rgb).resize((768, 432), Image.NEAREST).save(os.path.join(outdir, name))
def type_text(t):
    head = u32(HEAD)
    for c in t.encode():
        m[BUF + head % IN_SIZE] = c
        head += 1
        struct.pack_into("<I", m, HEAD, head)
p = subprocess.Popen([EMU, script], env=env, cwd=os.path.dirname(script),
                     stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
last, since, page = -1, time.time(), 0
while p.poll() is None:
    fr = u32(4)
    if fr != last:
        last, since = fr, time.time()
    elif time.time() - since > 0.3 and u32(WAIT) in (WAIT_INPUT, WAIT_REPL):
        if not typed:
            save("final.png")
            struct.pack_into("<I", m, 12, 1)
            break
        save("page%02d.png" % page); page += 1
        type_text((typed.pop(0) if typed else "") + "\n")
        since = time.time()
    elif time.time() - since > 1.0:
        save("page%02d.png" % page); page += 1
        struct.pack_into("<I", m, 8, 95); time.sleep(0.3)
        struct.pack_into("<I", m, 8, 0); time.sleep(0.3)
        since = time.time()
    time.sleep(0.05)
p.wait()
if not os.path.exists(os.path.join(outdir, "final.png")):
    save("final.png")
print("exit", p.returncode, "pages", page)
print(p.stdout.read().decode()[-1500:])
