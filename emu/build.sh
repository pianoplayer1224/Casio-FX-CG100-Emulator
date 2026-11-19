#!/bin/sh
# Build the fx-CG100 emulator's MicroPython (32-bit, like the calculator).
# Needs gcc with -m32 support (lib32-glibc). Usage: emu/build.sh [clean]
set -e
cd "$(dirname "$0")/micropython"
WARN="-Wall -Wno-error -Wno-dangling-pointer"
if [ "$1" = clean ]; then
  make -C mpy-cross clean
  make -C ports/cg100 clean
fi
# mpy-cross is a host tool: build it 64-bit, before the 32-bit port
make -C mpy-cross -j8 CWARN="$WARN"
# NLR_SETJMP: 1.9.4's x86 assembly exception handling crashes with modern gcc
make -C ports/cg100 -j8 \
  MICROPY_FORCE_32BIT=1 MICROPY_PY_BTREE=0 MICROPY_PY_FFI=0 MICROPY_PY_USSL=0 \
  MICROPY_PY_THREAD=0 MICROPY_PY_SOCKET=0 MICROPY_PY_TERMIOS=0 \
  CWARN="$WARN" CFLAGS_EXTRA="-DMICROPY_NLR_SETJMP=1 -DMICROPY_EMIT_X86=0"
ls -l ports/cg100/micropython
# Screen window: a separate 64-bit SDL2 program
cd ..
cc -O2 -Wall -o viewer viewer.c $(pkg-config --cflags --libs sdl2)
ls -l viewer
