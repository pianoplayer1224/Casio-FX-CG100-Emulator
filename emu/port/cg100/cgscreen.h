// The whole 384x216 panel as the viewer shows it: the status bar, then
// casioplot's canvas or the Python shell (see emu/README.md, "Screen").
#ifndef CG100_CGSCREEN_H
#define CG100_CGSCREEN_H

#include <stddef.h>
#include <stdint.h>
#include "cgshm.h"

// Shared memory with the viewer, or NULL without one ($CG100_SHM unset)
cg_shm_t *cg_screen_shm(void);

// Before the script: the shell as the calculator shows it when a script
// is run from the editor ("MicroPython v1.9.4", ">>>from NAME import *")
void cg_screen_start(const char *script);
// show_screen(): status bar + canvas
void cg_screen_canvas(const uint16_t *canvas);
// print() and tracebacks: added to the shell, which is not redrawn while
// the script runs (as on the calculator)
void cg_shell_write(const char *s, size_t n);
// input() without a window: the shell is shown while the answer is typed
// in the terminal
void cg_shell_input_begin(void);
void cg_shell_input_end(const char *s, size_t n);
// With a window: a line typed after what the shell shows, in the window
// (or on stdin), added to line. wait is CG_WAIT_INPUT or CG_WAIT_REPL.
// Returns 0 (Enter) or CG_IN_AC for [AC]; closing the window ends the
// emulator.
struct _vstr_t;
int cg_shell_readline(struct _vstr_t *line, int wait);
// The shell's ">>>" or "..." on a new line, also shown in the terminal
void cg_shell_prompt(const char *p);
// The script was refused without running: shows the message written so far
void cg_screen_refused(void);
// [AC]: 1 once for each press since the last call (or the last line typed).
// Ends the emulator if the window was closed.
int cg_screen_break(void);
// A statement typed at ">>>" starts running
void cg_screen_run(void);
// After the script, or a statement typed at ">>>": a drawing stays on the
// screen until a key is pressed, then the shell comes back.
void cg_screen_end(void);

#endif
