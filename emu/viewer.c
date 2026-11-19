// fx-CG100 emulator screen: shows what the emulated script last passed to
// show_screen() and reports the key held down, through a shared-memory file.
//
//     viewer SHM_PATH [SCALE]
//
// The emulator (a 32-bit process) and this window (64-bit SDL2) are
// separate programs because there is no 32-bit SDL2 on this system.
#include <fcntl.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

#include <SDL2/SDL.h>

#include "micropython/ports/cg100/cgshm.h"

// PC key -> getkey() code. The calculator's codes are row*10+column
// (calc/cgfont.py page 3: 12-16, 21-26, 31-36, 41-46, 51-56, 61-64, 71-75,
// 81-85, 91-95). Arrows, OK, back, EXE and the digits also come from games
// that run on the real calculator (github.com/ayush-jha-ai/Casio-CG100-Games);
// DEL, the operators and the point are placed from the keypad layout.
// Esc is [AC]: it interrupts the script, as on the calculator.
// Text typed at the PC keyboard also goes to input() and the >>> prompt.
static const struct { SDL_Keycode pc; uint32_t code; } keymap[] = {
    {SDLK_UP, 14}, {SDLK_LEFT, 23}, {SDLK_RIGHT, 25}, {SDLK_DOWN, 34},
    {SDLK_SPACE, 24},                         // OK (centre of the arrows)
    {SDLK_RETURN, 95}, {SDLK_KP_ENTER, 95},   // EXE
    {SDLK_BACKSPACE, 12},                     // back
    {SDLK_PAGEUP, 16}, {SDLK_PAGEDOWN, 26},   // PAGE UP/DOWN rocker (Casio manual chart)
    {SDLK_ESCAPE, 0xffff},                    // AC
    {SDLK_7, 61}, {SDLK_8, 62}, {SDLK_9, 63},
    {SDLK_4, 71}, {SDLK_5, 72}, {SDLK_6, 73},
    {SDLK_1, 81}, {SDLK_2, 82}, {SDLK_3, 83},
    {SDLK_0, 91}, {SDLK_PERIOD, 92},
    {SDLK_DELETE, 64},                        // DEL
    {SDLK_ASTERISK, 74}, {SDLK_KP_MULTIPLY, 74}, {SDLK_SLASH, 75}, {SDLK_KP_DIVIDE, 75},
    {SDLK_PLUS, 84}, {SDLK_KP_PLUS, 84}, {SDLK_MINUS, 85}, {SDLK_KP_MINUS, 85},
};

// The busy spinner at the right of the status bar while a script runs:
// 8 dots, the bright end stepping clockwise about every 0.37 s (filmed).
static void spinner(uint16_t *px, uint32_t ms) {
    static const int8_t dot[8][2] = {{0, -6}, {4, -4}, {6, 0}, {4, 4}, {0, 6}, {-4, 4}, {-6, 0}, {-4, -4}};
    int head = (ms / 370) % 8;
    for (int i = 0; i < 8; i++) {
        int age = (head - i + 8) % 8;       // 0 = brightest
        int size = age < 3 ? 3 : 2;
        int g = 31 - age * 3;               // grey level, 5 bits
        uint16_t c = (g << 11) | ((g * 2) << 5) | g;
        int cx = 372 + dot[i][0], cy = 10 + dot[i][1];
        for (int y = 0; y < size; y++) {
            for (int x = 0; x < size; x++) {
                px[(cy - 1 + y) * CG_W + cx - 1 + x] = c;
            }
        }
    }
}

// PC key -> character typed into the shell, for keys that type no text
static const struct { SDL_Keycode pc; uint8_t c; } typemap[] = {
    {SDLK_RETURN, CG_IN_ENTER}, {SDLK_KP_ENTER, CG_IN_ENTER},
    {SDLK_BACKSPACE, CG_IN_BACK}, {SDLK_DELETE, CG_IN_BACK},
    {SDLK_ESCAPE, CG_IN_AC},
    {SDLK_LEFT, CG_IN_LEFT}, {SDLK_RIGHT, CG_IN_RIGHT}, {SDLK_UP, CG_IN_UP}, {SDLK_DOWN, CG_IN_DOWN},
};

static void type(cg_shm_t *shm, uint8_t c) {
    // a full buffer drops the character
    if (shm->in_head - shm->in_tail < CG_IN_SIZE) {
        shm->in_buf[shm->in_head % CG_IN_SIZE] = c;
        shm->in_head++;
    }
}

static uint32_t key_code(SDL_Keycode k) {
    for (size_t i = 0; i < sizeof(keymap) / sizeof(keymap[0]); i++) {
        if (keymap[i].pc == k) {
            return keymap[i].code;
        }
    }
    return 0;
}

int main(int argc, char **argv) {
    if (argc < 2) {
        fprintf(stderr, "usage: viewer SHM_PATH [SCALE]\n");
        return 2;
    }
    int scale = argc > 2 ? atoi(argv[2]) : 3;
    int fd = open(argv[1], O_RDWR | O_CREAT, 0600);
    if (fd < 0 || ftruncate(fd, sizeof(cg_shm_t)) != 0) {
        perror(argv[1]);
        return 1;
    }
    cg_shm_t *shm = mmap(NULL, sizeof(cg_shm_t), PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
    close(fd);
    if (shm == MAP_FAILED) {
        perror("mmap");
        return 1;
    }
    memset(shm, 0, sizeof(*shm));
    for (int i = 0; i < CG_W * CG_H; i++) {
        shm->vram[i] = 0xffff;
    }
    shm->magic = CG_SHM_MAGIC;

    if (SDL_Init(SDL_INIT_VIDEO) != 0) {
        fprintf(stderr, "SDL: %s\n", SDL_GetError());
        return 1;
    }
    SDL_Window *win = SDL_CreateWindow("fx-CG100", SDL_WINDOWPOS_CENTERED, SDL_WINDOWPOS_CENTERED,
                                       CG_W * scale, CG_H * scale, 0);
    SDL_Renderer *ren = SDL_CreateRenderer(win, -1, SDL_RENDERER_ACCELERATED);
    SDL_Texture *tex = SDL_CreateTexture(ren, SDL_PIXELFORMAT_RGB565, SDL_TEXTUREACCESS_STREAMING,
                                         CG_W, CG_H);
    // typed text for input() and the >>> prompt, besides getkey()'s key
    SDL_StartTextInput();
    uint32_t shown = (uint32_t)-1, step = (uint32_t)-1;
    static uint16_t px[CG_W * CG_H];
    for (;;) {
        SDL_Event e;
        while (SDL_PollEvent(&e)) {
            if (e.type == SDL_QUIT) {
                shm->quit = 1;
                SDL_Quit();
                unlink(argv[1]);
                return 0;
            }
            if (e.type == SDL_KEYDOWN) {
                if (!e.key.repeat) {
                    shm->key = key_code(e.key.keysym.sym);
                    if (shm->key == 0xffff) {
                        shm->breaks++;
                    }
                }
                for (size_t i = 0; i < sizeof(typemap) / sizeof(typemap[0]); i++) {
                    if (typemap[i].pc == e.key.keysym.sym) {
                        type(shm, typemap[i].c);
                    }
                }
            } else if (e.type == SDL_KEYUP) {
                shm->key = 0;
            } else if (e.type == SDL_TEXTINPUT) {
                for (const char *t = e.text.text; *t; t++) {
                    if (*t >= 32 && *t <= 126) {
                        type(shm, *t);
                    }
                }
            }
        }
        // The calculator's screen refreshes about every 16.1 ms
        uint32_t ms = SDL_GetTicks();
        uint32_t now = shm->running ? ms / 370 : (uint32_t)-1;
        if (shm->frame != shown || now != step) {
            shown = shm->frame;
            step = now;
            memcpy(px, shm->vram, sizeof(px));
            if (shm->running) {
                spinner(px, ms);
            }
            SDL_UpdateTexture(tex, NULL, px, CG_W * 2);
            SDL_RenderCopy(ren, tex, NULL, NULL);
            SDL_RenderPresent(ren);
        }
        SDL_Delay(16);
    }
}
