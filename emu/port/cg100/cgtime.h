// fx-CG100 timing model: count events, virtual time = counts . costs.
//
// Every kind of work the calculator was measured doing gets an event
// counter. Costs (microseconds per event) come from emu/costs.txt, fitted
// to the filmed benchmarks by emu/fit.py. The interpreter sleeps so virtual
// time and wall-clock time stay in step.
#ifndef CG100_CGTIME_H
#define CG100_CGTIME_H

#include <stdint.h>
#include <stddef.h>

// Event layout
#define CG_EV_OP          0     // + bytecode opcode (256), families merged
#define CG_EV_BINOP       256   // + op * 5 + class, op < CG_BINOP_MAX
#define CG_BINOP_MAX      48
#define CG_CLS_SMALL      0     // small int
#define CG_CLS_FLOAT      1     // float involved
#define CG_CLS_BIG        2     // big (mpz) int involved
#define CG_CLS_BOOL       3     // bool with int/bool: generic dispatch, twice
#define CG_CLS_OTHER      4     // anything else (str, list, user class...)
#define CG_EV_UNARY       512
#define CG_EV_CALL_BC     513   // call of a Python function
#define CG_EV_CALL_ARG    514   // per positional argument
#define CG_EV_CALL_KW     515   // per keyword argument
#define CG_EV_CALL_NATIVE 516   // call of an unregistered native function
#define CG_EV_CALL_OTHER  517   // any other call
#define CG_EV_CALL_CLOSURE 518  // call of a closure (then also call_py)
#define CG_EV_CALL_BOUND  519   // call of a bound method object
#define CG_EV_CALL_NEW    520   // instantiating a user class
#define CG_EV_ALLOC       530   // heap allocation
#define CG_EV_ALLOC_SCAN  531   // allocation-table byte scanned
#define CG_EV_GC          532   // garbage collection
#define CG_EV_BIG_DIGITS  533   // mpz digits in big-int operands
#define CG_EV_POW_DIGITS  534   // result digits of a big-int power
#define CG_EV_MUL_WORK    535   // digit products of a big-int multiply
#define CG_EV_QSTR_FIND   536   // search of the interned strings (new str results)
#define CG_EV_QSTR_SCAN   537   // interned strings compared in that search
#define CG_EV_LEX_CHAR    538   // source character read by the compiler (scripts, imports)
#define CG_EV_SHOW_ROW    539   // canvas rows show_screen() sends (drawn on since the last call)
#define CG_EV_SHOW_ANY    582   // show_screen() calls with something drawn
#define CG_EV_ITER_LIST   540   // FOR_ITER step over a list
#define CG_EV_ITER_RANGE  541   // FOR_ITER step over a range object
#define CG_EV_ITER_OTHER  542   // FOR_ITER step over anything else
#define CG_EV_PIXEL_ON    550   // set_pixel inside the screen
#define CG_EV_PIXEL_OFF   551   // set_pixel outside the screen
#define CG_EV_CHAR_SMALL  552   // draw_string characters
#define CG_EV_CHAR_MEDIUM 553
#define CG_EV_CHAR_LARGE  554
#define CG_EV_PRINT_CHAR  555   // characters printed to the shell
#define CG_EV_PRINT_LINE  556   // newlines printed to the shell
#define CG_EV_GETKEY_IDLE 557   // getkey() with no key down (~8.2 ms, Cemetech)
#define CG_EV_GETKEY_HELD 558   // getkey() with a key held (cheap)
#define CG_EV_PRINT_WRITE 559   // separate writes to the shell (one per print() argument, separator, end)
#define CG_EV_SUM_ITEM    583   // items added by sum()
#define CG_EV_GC_MARK     587   // heap blocks scanned for pointers during a collection (bm_bigint mvb2: a full heap collects slower)
#define CG_EV_INT_BYTES   584   // bytes converted by int.to_bytes / int.from_bytes on a big int (bm_bigint)
#define CG_EV_MAP_PROBE   585   // hash-table slots examined by mp_map_lookup (a name not in a nearly full table walks far: bm_mac blen)
#define CG_EV_MAP_SCAN    586   // ordered-table (ROM) entries examined by mp_map_lookup
#define CG_EV_ATTR        560   // + kind * 4 + class (12)
#define CG_ATTR_LOAD      0
#define CG_ATTR_STORE     1
#define CG_ATTR_METHOD    2
#define CG_EV_SUBSCR      572   // + store * 5 + class (10)
#define CG_EV_FN          768   // + registered native function (256)
#define CG_FN_MAX         256
#define CG_EV_MAX         1024

extern uint64_t cg_count[CG_EV_MAX];
extern const uint8_t cg_opmap[256];

static inline void cg_event(int ev, uint32_t n) {
    cg_count[ev] += n;
}

// Called from the VM every CG_TICK_OPS opcodes: sleep to match virtual time.
#define CG_TICK_OPS 1024
extern uint32_t cg_tick_countdown;
void cg_tick(void);

// Around a wait for the user (input(), a drawing held until a key): the
// wait doesn't count as the script's time
void cg_time_pause(void);
void cg_time_resume(void);

// Virtual time in microseconds since start
double cg_vtime_us(void);

// Count a call; fun is the callable object
void cg_count_call(const void *fun, const void *type, size_t n_args, size_t n_kw);

// Count a binary op
void cg_count_binop(int op, uintptr_t lhs, uintptr_t rhs);

// Count a FOR_ITER step over iterator obj
void cg_count_iter(uintptr_t obj);

// Count an attribute access (kind CG_ATTR_*) or a subscript
void cg_count_attr(int kind, uintptr_t base);
void cg_count_subscr(int store, uintptr_t base);

// Setup: load costs, register native functions, read environment options
void cg_init(void);
const char *cg_event_name(int ev, char *buf, size_t len);

// Longest line the calculator opens a script with, in main.c (emu/LIMITATIONS.md)
#define CG_LINE_MAX 255
int cg_long_line(const char *path, size_t *len);

#endif

