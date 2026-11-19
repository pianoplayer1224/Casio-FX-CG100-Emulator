// The whole 384x216 panel: status bar, then casioplot's canvas or the shell.
//
// Layout read from photos of the calculator (bm_core_videos 6, 7, 8):
// status bar rows 0-21 (black, battery at the left; the viewer adds the
// busy spinner at the right while a script runs), canvas rows 24-215.
// The shell shows 9 lines of 38 characters (10x18 cells from row 24, font
// cgfont_shell), long lines cut off, a scroll bar at the right and the
// Editor/Shell tabs at the bottom.
//
// Text typed in the viewer window (or on stdin) answers input() and the
// ">>>" prompt after the script. How the calculator shows typing is not
// photographed: here the line scrolls sideways to keep the cursor in view,
// and UP/DOWN scroll the shell.
#include <fcntl.h>
#include <poll.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/mman.h>
#include <unistd.h>

#include "py/mpconfig.h"
#include "py/misc.h"
#include "cgscreen.h"
#include "cgfont.h"
#include "cgtime.h"

#define BLACK 0x0000
#define WHITE 0xffff
#define HEADER 0x31ec          // the banner's slate blue, about (48,60,96)

#define SH_X 0
#define SH_Y 24
#define SH_COLS 38
#define SH_ROWS 9
#define SH_LINE 18
#define SH_MAX 400             // lines kept for scrolling back
#define TAB_Y 190

static cg_shm_t *shm;
static int mapped;
static uint16_t panel[CG_H * CG_W];
static int canvas_shown;       // the screen shows the canvas, not the shell

static struct {
    char text[SH_COLS + 1];
    uint8_t len, header;
} lines[SH_MAX];
static int nlines = 1;         // the last line is the one being written
static int cursor;
static int capture = 1;
static int scroll;             // lines scrolled back from the newest

// The line being typed, after the text already on the shell's last line
#define ED_MAX 255
static struct {
    int active, len, pos;
    char buf[ED_MAX];
} ed;
static uint32_t breaks_seen;

cg_shm_t *cg_screen_shm(void) {
    if (mapped) {
        return shm;
    }
    mapped = 1;
    const char *path = getenv("CG100_SHM");
    if (!path) {
        return NULL;
    }
    int fd = open(path, O_RDWR);
    if (fd >= 0) {
        void *p = mmap(NULL, sizeof(cg_shm_t), PROT_READ | PROT_WRITE, MAP_SHARED, fd, 0);
        close(fd);
        if (p != MAP_FAILED) {
            // the viewer may still be starting: give it up to a second
            for (int i = 0; i < 100 && ((cg_shm_t*)p)->magic != CG_SHM_MAGIC; i++) {
                usleep(10000);
            }
            if (((cg_shm_t*)p)->magic == CG_SHM_MAGIC) {
                shm = p;
            }
        }
    }
    if (!shm) {
        fprintf(stderr, "cg100: no viewer at %s, drawing off-screen\n", path);
    }
    return shm;
}

static void present(void) {
    if (cg_screen_shm()) {
        memcpy(shm->vram, panel, sizeof(panel));
        shm->frame++;
    }
}

static void fill(int x0, int y0, int x1, int y1, uint16_t c) {
    for (int y = y0; y <= y1; y++) {
        for (int x = x0; x <= x1; x++) {
            panel[y * CG_W + x] = c;
        }
    }
}

// '#' = colour c, anything else left alone
static void art(int x, int y, const char *const *rows, int n, uint16_t c) {
    for (int j = 0; j < n; j++) {
        for (int i = 0; rows[j][i]; i++) {
            if (rows[j][i] == '#') {
                panel[(y + j) * CG_W + x + i] = c;
            }
        }
    }
}

static const char *const battery[] = {
    "...########...",
    "...##....##...",
    "#####....#####",
    "##...####...##",
    "##...####...##",
    "##.########.##",
    "##.########.##",
    "##.########.##",
    "##.########.##",
    "##.########.##",
    "##.########.##",
    "##.########.##",
    "##.########.##",
    "##.########.##",
    "##.########.##",
    "##.########.##",
    "##..######..##",
    "##..........##",
    "##############",
    "##############",
};

static void status_bar(void) {
    fill(0, 0, CG_W - 1, 21, BLACK);
    art(1, 0, battery, 20, WHITE);
    fill(0, 22, CG_W - 1, CG_CANVAS_Y - 1, WHITE);
}

void cg_screen_canvas(const uint16_t *canvas) {
    status_bar();
    memcpy(panel + CG_CANVAS_Y * CG_W, canvas, CG_CANVAS_H * CG_W * sizeof(uint16_t));
    canvas_shown = 1;
    present();
}

// Editor/Shell tabs. The labels are casioplot's medium font (cgfont_calc.json),
// which matches the photographed labels in size and position.
static const char *const tab_left[] = {
    "###.....###",
    "###....####",
    "###...####.",
    "###..##########",
    "###.###########",
    "###..##########",
    "###...####.",
    "###....####",
    "###.....###",
};
static const char *const tab_right[] = {
    "....###.....###",
    "....####....###",
    ".....####...###",
    "##########..###",
    "###########.###",
    "##########..###",
    ".....####...###",
    "....####....###",
    "....###.....###",
};
static const char *const tab_editor[] = {
    "########.........##....##..............................",
    "########.........##....##......##......................",
    "##...............##....##......##......................",
    "##...............##............##......................",
    "##..........####.##..####....#######...######...##.####",
    "#######....########..####....#######..########..#######",
    "#######...###...###....##......##.....##....##..###....",
    "##........##.....##....##......##.....##....##..##.....",
    "##........##.....##....##......##.....##....##..##.....",
    "##........##.....##....##......##.....##....##..##.....",
    "##........###...###....##......##.....##....##..##.....",
    "########...########..######....#####..########..##.....",
    "########....####.##..######.....####...######...##.....",
};
static const char *const tab_shell[] = {
    "..#####...##...................##.....##..",
    ".#######..##...................##.....##..",
    "###...##..##...................##.....##..",
    "##........##...................##.....##..",
    "##........##.####....######....##.....##..",
    "####......########..########...##.....##..",
    ".######...###...##..##....##...##.....##..",
    "....####..##....##..########...##.....##..",
    "......##..##....##..########...##.....##..",
    "......##..##....##..##.........##.....##..",
    "##...###..##....##..##....##...##.....##..",
    "#######...##....##..########...####...####",
    ".#####....##....##...######.....###....###",
};

static void tabs(void) {
    fill(0, TAB_Y, CG_W - 1, CG_H - 1, WHITE);
    fill(0, TAB_Y + 3, 24, CG_H - 1, BLACK);           // left arrow area
    fill(358, TAB_Y + 1, CG_W - 1, CG_H - 1, BLACK);   // right arrow area
    fill(27, TAB_Y + 3, 180, 210, BLACK);              // Editor tab
    fill(0, 213, CG_W - 1, CG_H - 1, BLACK);           // below the white outline
    // rounded corners
    panel[210 * CG_W + 27] = panel[210 * CG_W + 28] = panel[209 * CG_W + 27] = WHITE;
    panel[212 * CG_W + 25] = panel[211 * CG_W + 25] = panel[212 * CG_W + 26] = BLACK;
    panel[212 * CG_W + 357] = panel[211 * CG_W + 357] = panel[212 * CG_W + 356] = BLACK;
    art(3, 198, tab_left, 9, WHITE);
    art(364, 198, tab_right, 9, WHITE);
    art(80, 196, tab_editor, 13, WHITE);
    art(252, 196, tab_shell, 13, BLACK);
}

static void glyph(int x, int y, int c, uint16_t colour) {
    if (c < CGFONT_FIRST || c > CGFONT_LAST) {
        c = '?';
    }
    const uint32_t *g = cgfont_shell + (c - CGFONT_FIRST) * CGFONT_SHELL_H;
    for (int j = 0; j < CGFONT_SHELL_H; j++) {
        for (int i = 0; i < CGFONT_SHELL_W; i++) {
            if (g[j] >> i & 1 && x + i < CG_W) {
                panel[(y + j) * CG_W + x + i] = colour;
            }
        }
    }
}

static void shell_draw(void) {
    status_bar();
    fill(0, 22, CG_W - 1, TAB_Y - 1, WHITE);
    // the last line counts while it holds text or the cursor
    int typing = cursor || ed.active;
    int n = nlines - (lines[nlines - 1].len == 0 && !typing);
    int first = n > SH_ROWS ? n - SH_ROWS : 0;
    if (scroll > first) {
        scroll = first;
    }
    first -= scroll;
    for (int k = first; k < n && k < first + SH_ROWS; k++) {
        int y = SH_Y + (k - first) * SH_LINE;
        uint16_t colour = lines[k].header ? HEADER : BLACK;
        if (k == nlines - 1 && typing) {
            // the text before the input, then the input, moved left as far
            // as needed to show the cursor
            char text[SH_COLS + ED_MAX];
            int len = lines[k].len;
            memcpy(text, lines[k].text, len);
            memcpy(text + len, ed.buf, ed.len);
            int at = len + ed.pos;
            len += ed.len;
            // (the cursor may sit just after a full line)
            int off = at > SH_COLS ? at - SH_COLS : 0;
            for (int i = off; i < len && i - off < SH_COLS; i++) {
                glyph(SH_X + (i - off) * CGFONT_SHELL_W, y, text[i], colour);
            }
            int x = SH_X + (at - off) * CGFONT_SHELL_W;
            if (x < CG_W - 2) {
                fill(x, y + 1, x + 1, y + 16, BLACK);
            }
        } else {
            for (int i = 0; i < lines[k].len; i++) {
                glyph(SH_X + i * CGFONT_SHELL_W, y, lines[k].text[i], colour);
            }
        }
    }
    if (n > SH_ROWS) {
        int track = SH_ROWS * SH_LINE;
        int h = track * SH_ROWS / n;
        if (h < 6) {
            h = 6;
        }
        int top = SH_Y + (track - h) * first / (n - SH_ROWS);
        fill(378, top, 379, top + h - 1, BLACK);
    }
    tabs();
    canvas_shown = 0;
    present();
}

static void new_line(void) {
    if (nlines == SH_MAX) {
        memmove(lines, lines + 1, sizeof(lines[0]) * (SH_MAX - 1));
        nlines--;
    }
    memset(&lines[nlines], 0, sizeof(lines[0]));
    nlines++;
}

static void add(const char *s, size_t n, int header) {
    for (size_t i = 0; i < n; i++) {
        char c = s[i];
        if (c == '\n') {
            new_line();
            continue;
        }
        if (c == '\r') {
            continue;
        }
        if ((unsigned char)c < 32 || (unsigned char)c > 126) {
            c = c == '\t' ? ' ' : '?';
        }
        int k = nlines - 1;
        lines[k].header = header;
        // the shell cuts long lines off
        if (lines[k].len < SH_COLS) {
            lines[k].text[lines[k].len++] = c;
        }
    }
}

void cg_shell_write(const char *s, size_t n) {
    if (capture) {
        add(s, n, 0);
    }
}

void cg_screen_start(const char *script) {
    const char *base = strrchr(script, '/');
    base = base ? base + 1 : script;
    size_t len = strlen(base);
    if (len > 3 && strcmp(base + len - 3, ".py") == 0) {
        len -= 3;
    }
    static const char banner[] = "MicroPython v1.9.4\n|CASIO COMPUTER CO., LTD.\n";
    add(banner, strlen(banner), 1);
    add(">>>from ", 8, 0);
    add(base, len, 0);
    add(" import *\n", 10, 0);
    if (cg_screen_shm()) {
        shm->running = 1;
        shell_draw();
    }
}

void cg_shell_input_begin(void) {
    // without a window: typed in the terminal, and shown when Enter is
    // pressed, not as echoed keys
    capture = 0;
    cursor = 1;
    shell_draw();
    cursor = 0;
    cg_time_pause();
}

void cg_shell_input_end(const char *s, size_t n) {
    cg_time_resume();
    capture = 1;
    add(s, n, 0);
    add("\n", 1, 0);
}

// Closing the window ends the emulator, wherever the script is (a script
// that catches every exception would otherwise carry on unseen)
static void closed(void) {
    if (shm->quit) {
        _exit(0);
    }
}

int cg_screen_break(void) {
    if (!cg_screen_shm()) {
        return 0;
    }
    closed();
    if (shm->breaks == breaks_seen) {
        return 0;
    }
    breaks_seen = shm->breaks;
    return 1;
}

static void term(const char *s, size_t n) {
    ssize_t r = write(STDOUT_FILENO, s, n);
    (void)r;
}

void cg_shell_prompt(const char *p) {
    if (lines[nlines - 1].len) {
        new_line();
    }
    add(p, strlen(p), 0);
    term(p, strlen(p));
}

// A line typed on stdin: the terminal (Enter sends it) or a pipe
static int stdin_line(void) {
    static int eof;
    struct pollfd pfd = {STDIN_FILENO, POLLIN, 0};
    if (eof || poll(&pfd, 1, 10) <= 0) {
        if (eof) {
            usleep(10000);
        }
        return 0;
    }
    ed.len = 0;
    char c;
    for (;;) {
        ssize_t r = read(STDIN_FILENO, &c, 1);
        if (r <= 0) {
            eof = 1;
            return ed.len > 0;
        }
        if (c == '\n') {
            return 1;
        }
        if (c != '\r' && ed.len < ED_MAX) {
            ed.buf[ed.len++] = c;
        }
    }
}

int cg_shell_readline(vstr_t *line, int wait) {
    // keys pressed before (a getkey() loop, the key that ended a drawing)
    // are not typed text
    shm->in_tail = shm->in_head;
    breaks_seen = shm->breaks;
    ed.active = 1;
    ed.len = ed.pos = 0;
    scroll = 0;
    shm->wait = wait;
    shell_draw();
    cg_time_pause();
    int ret, echo = 1;
    for (;;) {
        closed();
        if (shm->in_tail == shm->in_head) {
            if (stdin_line()) {
                // the terminal has shown it already, a pipe has not
                echo = !isatty(STDIN_FILENO);
                ret = 0;
                break;
            }
            continue;
        }
        uint8_t c = shm->in_buf[shm->in_tail % CG_IN_SIZE];
        shm->in_tail++;
        if (c == CG_IN_ENTER || c == CG_IN_AC) {
            ret = c == CG_IN_AC ? CG_IN_AC : 0;
            break;
        }
        if (c == CG_IN_BACK) {
            if (ed.pos > 0) {
                memmove(ed.buf + ed.pos - 1, ed.buf + ed.pos, ed.len - ed.pos);
                ed.pos--;
                ed.len--;
            }
        } else if (c == CG_IN_LEFT) {
            ed.pos -= ed.pos > 0;
        } else if (c == CG_IN_RIGHT) {
            ed.pos += ed.pos < ed.len;
        } else if (c == CG_IN_UP) {
            scroll++;
        } else if (c == CG_IN_DOWN) {
            scroll -= scroll > 0;
        } else if (c >= 32 && c <= 126 && ed.len < ED_MAX) {
            memmove(ed.buf + ed.pos + 1, ed.buf + ed.pos, ed.len - ed.pos);
            ed.buf[ed.pos++] = c;
            ed.len++;
            scroll = 0;
        }
        if (shm->in_tail == shm->in_head) {
            shell_draw();
        }
    }
    cg_time_resume();
    shm->wait = CG_WAIT_NONE;
    ed.active = 0;
    if (ret >= 0) {
        // [AC] leaves what was typed on the screen, but it isn't entered
        if (ret == 0) {
            vstr_add_strn(line, ed.buf, ed.len);
        }
        add(ed.buf, ed.len, 0);
        add("\n", 1, 0);
        if (echo) {
            term(ed.buf, ed.len);
            term("\n", 1);
        }
    }
    scroll = 0;
    return ret;
}

// A drawing stays on the screen until a key is pressed
static void hold(void) {
    shm->running = 0;
    shm->wait = CG_WAIT_KEY;
    present();
    cg_time_pause();
    // a key still down from the script doesn't count
    while (shm->key) {
        closed();
        usleep(10000);
    }
    while (!shm->key) {
        closed();
        usleep(10000);
    }
    cg_time_resume();
    shm->wait = CG_WAIT_NONE;
}

void cg_screen_run(void) {
    breaks_seen = shm->breaks;
    shm->running = 1;
    canvas_shown = 0;
}

void cg_screen_refused(void) {
    if (cg_screen_shm()) {
        shell_draw();
    }
}

void cg_screen_end(void) {
    if (lines[nlines - 1].len) {
        new_line();
    }
    if (!cg_screen_shm()) {
        return;
    }
    shm->running = 0;
    if (canvas_shown) {
        hold();
    }
}
