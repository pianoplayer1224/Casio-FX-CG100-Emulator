// Screen and keyboard shared between the emulator and emu/viewer.c
#ifndef CG100_CGSHM_H
#define CG100_CGSHM_H

#include <stdint.h>

// The whole panel: status bar, then casioplot's canvas below it
#define CG_W 384
#define CG_H 216
#define CG_CANVAS_Y 24
#define CG_CANVAS_H 192
#define CG_SHM_MAGIC 0x43473132u   // "CG12"

// Typed characters, viewer -> shell: printable ASCII, and these
#define CG_IN_ENTER  '\n'
#define CG_IN_BACK   '\b'
#define CG_IN_AC     3
#define CG_IN_LEFT   2
#define CG_IN_RIGHT  6
#define CG_IN_UP     16
#define CG_IN_DOWN   14
#define CG_IN_SIZE   256

typedef struct {
    uint32_t magic;
    volatile uint32_t frame;    // incremented on every change of vram
    volatile uint32_t key;      // key held now (getkey() code), 0 = none
    volatile uint32_t quit;     // set by the viewer when its window closes
    volatile uint32_t running;  // a script is running: the viewer draws the busy spinner
    uint16_t vram[CG_H * CG_W]; // RGB565, the whole panel
    volatile uint32_t wait;     // what the emulator waits for: CG_WAIT_*
    volatile uint32_t breaks;   // [AC] presses, counted by the viewer
    volatile uint32_t in_head;  // typed characters: the viewer adds at in_head,
    volatile uint32_t in_tail;  // the emulator takes from in_tail (mod CG_IN_SIZE)
    uint8_t in_buf[CG_IN_SIZE];
} cg_shm_t;

#define CG_WAIT_NONE  0   // running
#define CG_WAIT_KEY   1   // a drawing is held until a key is pressed
#define CG_WAIT_INPUT 2   // input() in the shell
#define CG_WAIT_REPL  3   // the >>> prompt after the script

#endif
