// casioplot for the fx-CG100 emulator: 384x192 RGB565 canvas.
//
// Drawing goes to a back buffer; show_screen() puts it below the status bar
// in shared memory (file named by $CG100_SHM) where emu/viewer.c displays it.
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <unistd.h>

#include "py/runtime.h"
#include "cgscreen.h"
#include "cgtime.h"
#include "cgfont.h"

static uint16_t vram[CG_CANVAS_H * CG_W];
static FILE *trace;
static FILE *counts;   // every event counter at each show_screen(), for emu/fit.py
static int ready;

// show_screen() sends only the rows drawn on since the last call:
// 38.9 us when anything was drawn (CG_EV_SHOW_ANY) plus 52.2 us a row
// (CG_EV_SHOW_ROW), on top of the ~27 us call. Measured with
// calc/bm_show2.py (bm_core_videos/15, 3 films within 0.5%): one pixel
// and show 0.13 ms, 192 rows 10.1 ms. It does not depend on how much of a
// row was drawn on, or on whether the rows are adjacent (Bad Apple's film
// tracks best without a cost per separate group of rows).
static uint8_t dirty[CG_CANVAS_H];
static int ndirty;

static inline void touch(int y) {
    if (!dirty[y]) {
        dirty[y] = 1;
        ndirty++;
    }
}

static void setup(void) {
    if (ready) {
        return;
    }
    ready = 1;
    for (int i = 0; i < CG_W * CG_CANVAS_H; i++) {
        vram[i] = 0xffff;
    }
    const char *cf = getenv("CG100_COUNTS");
    if (cf) {
        counts = fopen(cf, "w");
        if (counts) {
            char buf[64];
            fprintf(counts, "pixel00");
            for (int i = 0; i < CG_EV_MAX; i++) {
                fprintf(counts, ",%s", cg_event_name(i, buf, sizeof(buf)));
            }
            fputc('\n', counts);
        }
    }
    const char *t = getenv("CG100_TRACE");
    if (t) {
        trace = fopen(t, "w");
        if (trace) {
            fprintf(trace, "vtime_s,pixel00\n");
        }
    }
}

static uint16_t to565(mp_obj_t color) {
    mp_obj_t *c;
    mp_obj_get_array_fixed_n(color, 3, &c);
    int r = mp_obj_get_int(c[0]), g = mp_obj_get_int(c[1]), b = mp_obj_get_int(c[2]);
    // values past 255 are taken as 255: (300, 0, 0) reads back as (248, 0, 0)
    // (photographed, bm_core_videos/15); below 0 assumed taken as 0
    r = r < 0 ? 0 : r > 255 ? 255 : r;
    g = g < 0 ? 0 : g > 255 ? 255 : g;
    b = b < 0 ? 0 : b > 255 ? 255 : b;
    return ((r & 0xf8) << 8) | ((g & 0xfc) << 3) | ((b & 0xff) >> 3);
}

static inline void put(int x, int y, uint16_t v) {
    if (x >= 0 && x < CG_W && y >= 0 && y < CG_CANVAS_H) {
        vram[y * CG_W + x] = v;
        touch(y);
    }
}

STATIC mp_obj_t casioplot_set_pixel(size_t n_args, const mp_obj_t *args) {
    setup();
    int x = mp_obj_get_int(args[0]), y = mp_obj_get_int(args[1]);
    uint16_t v = n_args > 2 ? to565(args[2]) : 0;
    if (x >= 0 && x < CG_W && y >= 0 && y < CG_CANVAS_H) {
        vram[y * CG_W + x] = v;
        touch(y);
        cg_event(CG_EV_PIXEL_ON, 1);
    } else {
        cg_event(CG_EV_PIXEL_OFF, 1);
    }
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(casioplot_set_pixel_obj, 2, 3, casioplot_set_pixel);

STATIC mp_obj_t casioplot_get_pixel(mp_obj_t x_in, mp_obj_t y_in) {
    setup();
    int x = mp_obj_get_int(x_in), y = mp_obj_get_int(y_in);
    if (x < 0 || x >= CG_W || y < 0 || y >= CG_CANVAS_H) {
        return mp_const_none;
    }
    uint16_t v = vram[y * CG_W + x];
    // RGB565 read back as 5/6/5 bits shifted up (red: 248,0,0), but white
    // reads as 255,255,255 (photographed in turtle_buffer, bm_core_videos/14)
    if (v == 0xffff) {
        mp_obj_t w[3] = {MP_OBJ_NEW_SMALL_INT(255), MP_OBJ_NEW_SMALL_INT(255), MP_OBJ_NEW_SMALL_INT(255)};
        return mp_obj_new_tuple(3, w);
    }
    mp_obj_t c[3] = {
        MP_OBJ_NEW_SMALL_INT((v >> 11) << 3),
        MP_OBJ_NEW_SMALL_INT(((v >> 5) & 0x3f) << 2),
        MP_OBJ_NEW_SMALL_INT((v & 0x1f) << 3),
    };
    return mp_obj_new_tuple(3, c);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_2(casioplot_get_pixel_obj, casioplot_get_pixel);

STATIC mp_obj_t casioplot_clear_screen(void) {
    setup();
    for (int i = 0; i < CG_W * CG_CANVAS_H; i++) {
        vram[i] = 0xffff;
    }
    memset(dirty, 1, sizeof(dirty));
    ndirty = CG_CANVAS_H;
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(casioplot_clear_screen_obj, casioplot_clear_screen);

static void write_counts(uint32_t pixel00) {
    fprintf(counts, "%u", pixel00);
    for (int i = 0; i < CG_EV_MAX; i++) {
        fprintf(counts, ",%llu", (unsigned long long)cg_count[i]);
    }
    fputc('\n', counts);
    fflush(counts);
}

STATIC mp_obj_t casioplot_show_screen(void) {
    setup();
    if (ndirty) {
        cg_event(CG_EV_SHOW_ANY, 1);
        cg_event(CG_EV_SHOW_ROW, ndirty);
    }
    memset(dirty, 0, sizeof(dirty));
    ndirty = 0;
    cg_tick();
    // (cg_tick() ends the emulator if the window was closed)
    cg_screen_canvas(vram);
    if (trace) {
        fprintf(trace, "%.6f,%d\n", cg_vtime_us() / 1e6, vram[0]);
        fflush(trace);
    }
    if (counts) {
        write_counts(vram[0]);
    }
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(casioplot_show_screen_obj, casioplot_show_screen);

STATIC mp_obj_t casioplot_draw_string(size_t n_args, const mp_obj_t *args) {
    setup();
    int x = mp_obj_get_int(args[0]), y = mp_obj_get_int(args[1]);
    size_t len;
    const char *s = mp_obj_str_get_data(args[2], &len);
    uint16_t v = n_args > 3 ? to565(args[3]) : 0;
    const char *size = n_args > 4 ? mp_obj_str_get_str(args[4]) : "medium";
    const uint32_t *font;
    const uint8_t *adv;
    int w, h, ev;
    if (strcmp(size, "small") == 0) {
        font = cgfont_small; adv = cgfont_small_adv; w = CGFONT_SMALL_W; h = CGFONT_SMALL_H;
        ev = CG_EV_CHAR_SMALL;
    } else if (strcmp(size, "large") == 0) {
        font = cgfont_large; adv = cgfont_large_adv; w = CGFONT_LARGE_W; h = CGFONT_LARGE_H;
        ev = CG_EV_CHAR_LARGE;
    } else {
        font = cgfont_medium; adv = cgfont_medium_adv; w = CGFONT_MEDIUM_W; h = CGFONT_MEDIUM_H;
        ev = CG_EV_CHAR_MEDIUM;
    }
    // ASCII only, transparent background
    for (size_t i = 0; i < len; i++) {
        int c = (unsigned char)s[i];
        if (c < CGFONT_FIRST || c > CGFONT_LAST) {
            c = '?';
        }
        const uint32_t *g = font + (c - CGFONT_FIRST) * h;
        // show_screen() then sends the character's whole cell, blank rows
        // too: one small "A" (ink in 9 of 10 rows) and show costs 702 us
        // (calc/bm_show.py), 692 with 10 rows, 640 with 9
        for (int yy = 0; yy < h; yy++) {
            if (y + yy >= 0 && y + yy < CG_CANVAS_H) {
                touch(y + yy);
            }
        }
        for (int yy = 0; yy < h; yy++) {
            for (int xx = 0; xx < w; xx++) {
                if (g[yy] >> xx & 1) {
                    put(x + xx, y + yy, v);
                }
            }
        }
        x += adv[c - CGFONT_FIRST];
    }
    cg_event(ev, len);
    return mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_VAR_BETWEEN(casioplot_draw_string_obj, 3, 5, casioplot_draw_string);

// The key held now, or None. On the calculator a call with no key down
// takes ~8.2 ms; [AC] interrupts the script.
#define CG_KEY_AC 0xffff
STATIC mp_obj_t casioplot_getkey(void) {
    setup();
    cg_shm_t *shm = cg_screen_shm();
    uint32_t k = shm ? shm->key : 0;
    cg_event(k ? CG_EV_GETKEY_HELD : CG_EV_GETKEY_IDLE, 1);
    cg_tick();
    if (k == CG_KEY_AC) {
        // one KeyboardInterrupt per press: cg_tick() may have taken it
        // already (then it is pending), and a held AC doesn't raise again
        if (cg_screen_break()) {
            mp_raise_msg(&mp_type_KeyboardInterrupt, NULL);
        }
        return mp_const_none;
    }
    return k ? MP_OBJ_NEW_SMALL_INT(k) : mp_const_none;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(casioplot_getkey_obj, casioplot_getkey);

STATIC const mp_rom_map_elem_t casioplot_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_casioplot) },
    { MP_ROM_QSTR(MP_QSTR_set_pixel), MP_ROM_PTR(&casioplot_set_pixel_obj) },
    { MP_ROM_QSTR(MP_QSTR_get_pixel), MP_ROM_PTR(&casioplot_get_pixel_obj) },
    { MP_ROM_QSTR(MP_QSTR_clear_screen), MP_ROM_PTR(&casioplot_clear_screen_obj) },
    { MP_ROM_QSTR(MP_QSTR_show_screen), MP_ROM_PTR(&casioplot_show_screen_obj) },
    { MP_ROM_QSTR(MP_QSTR_draw_string), MP_ROM_PTR(&casioplot_draw_string_obj) },
    { MP_ROM_QSTR(MP_QSTR_getkey), MP_ROM_PTR(&casioplot_getkey_obj) },
};
STATIC MP_DEFINE_CONST_DICT(casioplot_globals, casioplot_globals_table);

const mp_obj_module_t mp_module_casioplot = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t*)&casioplot_globals,
};
