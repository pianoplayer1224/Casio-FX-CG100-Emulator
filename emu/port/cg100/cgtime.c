// fx-CG100 timing model, see cgtime.h
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <signal.h>
#include <time.h>
#include <math.h>

#include "py/runtime.h"
#include "py/objint.h"
#include "py/objfun.h"
#include "py/objtype.h"
#include "cgtime.h"
#include "cgscreen.h"

uint64_t cg_count[CG_EV_MAX];

// Opcode -> event: opcode families that differ only in an operand encoded
// in the opcode (local slot, small constant, operator) share one event.
// Generated from py/bc0.h.
const uint8_t cg_opmap[256] = {
    0x00,0x01,0x02,0x03,0x04,0x05,0x06,0x07,0x08,0x09,0x0a,0x0b,0x0c,0x0d,0x0e,0x0f,
    0x10,0x10,0x10,0x13,0x10,0x15,0x10,0x10,0x18,0x19,0x1a,0x1b,0x1c,0x1d,0x1e,0x1f,
    0x20,0x21,0x22,0x23,0x24,0x25,0x26,0x27,0x28,0x29,0x2a,0x2b,0x2c,0x2d,0x2e,0x2f,
    0x30,0x31,0x32,0x33,0x34,0x35,0x36,0x36,0x38,0x38,0x3a,0x3b,0x3c,0x3d,0x3e,0x3f,
    0x40,0x41,0x42,0x43,0x44,0x45,0x46,0x47,0x48,0x49,0x4a,0x4b,0x4c,0x4d,0x4e,0x4f,
    0x50,0x51,0x52,0x53,0x54,0x55,0x56,0x57,0x58,0x59,0x5a,0x5b,0x5c,0x5d,0x5e,0x5f,
    0x60,0x61,0x62,0x63,0x64,0x65,0x66,0x67,0x68,0x69,0x6a,0x6b,0x6c,0x6d,0x6e,0x6f,
    0x10,0x10,0x10,0x10,0x10,0x10,0x10,0x10,0x10,0x10,0x10,0x10,0x10,0x10,0x10,0x10,
    0x10,0x10,0x10,0x10,0x10,0x10,0x10,0x10,0x10,0x10,0x10,0x10,0x10,0x10,0x10,0x10,
    0x10,0x10,0x10,0x10,0x10,0x10,0x10,0x10,0x10,0x10,0x10,0x10,0x10,0x10,0x10,0x10,
    0x10,0x10,0x10,0x10,0x10,0x10,0x10,0x10,0x10,0x10,0x10,0x10,0x10,0x10,0x10,0x10,
    0x19,0x19,0x19,0x19,0x19,0x19,0x19,0x19,0x19,0x19,0x19,0x19,0x19,0x19,0x19,0x19,
    0x22,0x22,0x22,0x22,0x22,0x22,0x22,0x22,0x22,0x22,0x22,0x22,0x22,0x22,0x22,0x22,
    0xd0,0xd0,0xd0,0xd0,0xd0,0xd0,0xd0,0xd7,0xd7,0xd7,0xd7,0xd7,0xd7,0xd7,0xd7,0xd7,
    0xd7,0xd7,0xd7,0xd7,0xd7,0xd7,0xd7,0xd7,0xd7,0xd7,0xd7,0xd7,0xd7,0xd7,0xd7,0xd7,
    0xd7,0xd7,0xd7,0xd7,0xd7,0xd7,0xd7,0xd7,0xd7,0xd7,0xd7,0xd7,0xd7,0xd7,0xd7,0xd7,
};

static const char *const opname[256] = {
    [0x10] = "load_const",
    [0x18] = "load_null",
    [0x19] = "load_fast",
    [0x1a] = "load_deref",
    [0x1b] = "load_name",
    [0x1c] = "load_global",
    [0x1d] = "load_attr",
    [0x1e] = "load_method",
    [0x1f] = "load_super_method",
    [0x20] = "load_build_class",
    [0x21] = "load_subscr",
    [0x22] = "store_fast",
    [0x23] = "store_deref",
    [0x24] = "store_name",
    [0x25] = "store_global",
    [0x26] = "store_attr",
    [0x27] = "store_subscr",
    [0x28] = "delete_fast",
    [0x29] = "delete_deref",
    [0x2a] = "delete_name",
    [0x2b] = "delete_global",
    [0x30] = "dup_top",
    [0x31] = "dup_top_two",
    [0x32] = "pop_top",
    [0x33] = "rot_two",
    [0x34] = "rot_three",
    [0x35] = "jump",
    [0x36] = "pop_jump_if",
    [0x38] = "jump_if_or_pop",
    [0x3d] = "setup_with",
    [0x3e] = "with_cleanup",
    [0x3f] = "setup_except",
    [0x40] = "setup_finally",
    [0x41] = "end_finally",
    [0x42] = "get_iter",
    [0x43] = "for_iter",
    [0x44] = "pop_block",
    [0x45] = "pop_except",
    [0x46] = "unwind_jump",
    [0x47] = "get_iter_stack",
    [0x50] = "build_tuple",
    [0x51] = "build_list",
    [0x53] = "build_map",
    [0x54] = "store_map",
    [0x56] = "build_set",
    [0x57] = "store_comp",
    [0x58] = "build_slice",
    [0x59] = "unpack_sequence",
    [0x5a] = "unpack_ex",
    [0x5b] = "return_value",
    [0x5c] = "raise_varargs",
    [0x5d] = "yield_value",
    [0x5e] = "yield_from",
    [0x60] = "make_function",
    [0x61] = "make_function_defargs",
    [0x62] = "make_closure",
    [0x63] = "make_closure_defargs",
    [0x64] = "call_function",
    [0x65] = "call_function_var_kw",
    [0x66] = "call_method",
    [0x67] = "call_method_var_kw",
    [0x68] = "import_name",
    [0x69] = "import_from",
    [0x6a] = "import_star",
    [0xd0] = "unary_op",
    [0xd7] = "binary_op",
};
uint32_t cg_tick_countdown = CG_TICK_OPS;

static double cost[CG_EV_MAX];
static int throttle;            // sleep to keep real time; off with CG100_FAST=1
static int have_costs;
static struct timespec start;
// Fast mode can also be switched while a script runs: SIGRTMIN turns it on, SIGRTMIN+1 off (calc.sealnet.xyz)
static volatile sig_atomic_t fast_req = -1;

static void on_fast(int sig) {
    fast_req = sig == SIGRTMIN;
}

// Registered native functions: pointer -> index, for per-function costs
#define FN_SLOTS 1024
static const void *fn_ptr[FN_SLOTS];
static uint16_t fn_idx[FN_SLOTS];
static char fn_name[CG_FN_MAX][32];
static int fn_count;

static size_t slot_of(const void *p) {
    return ((uintptr_t)p >> 2) * 2654435761u % FN_SLOTS;
}

static int fn_lookup(const void *p) {
    for (size_t s = slot_of(p); fn_ptr[s]; s = (s + 1) % FN_SLOTS) {
        if (fn_ptr[s] == p) {
            return fn_idx[s];
        }
    }
    return -1;
}

static void fn_register(const void *p, const char *prefix, qstr name) {
    if (fn_lookup(p) >= 0) {
        return;
    }
    if (fn_count == CG_FN_MAX) {
        fprintf(stderr, "cgtime: function table full, %s%s not timed separately\n",
                prefix, qstr_str(name));
        return;
    }
    size_t s = slot_of(p);
    while (fn_ptr[s]) {
        s = (s + 1) % FN_SLOTS;
    }
    fn_ptr[s] = p;
    fn_idx[s] = fn_count;
    snprintf(fn_name[fn_count], sizeof(fn_name[0]), "%s%s", prefix, qstr_str(name));
    fn_count++;
}

static void register_map(const mp_map_t *map, const char *prefix, int depth) {
    for (size_t i = 0; i < map->alloc; i++) {
        if (!MP_MAP_SLOT_IS_FILLED(map, i)) {
            continue;
        }
        mp_obj_t v = map->table[i].value;
        if (!MP_OBJ_IS_OBJ(v) || !mp_obj_is_callable(v)) {
            continue;
        }
        qstr name = MP_OBJ_QSTR_VALUE(map->table[i].key);
        fn_register(MP_OBJ_TO_PTR(v), prefix, name);
        // Methods of builtin types: str.join, list.append...
        if (depth == 0 && MP_OBJ_IS_TYPE(v, &mp_type_type)) {
            mp_obj_type_t *t = MP_OBJ_TO_PTR(v);
            if (t->locals_dict) {
                char sub[24];
                snprintf(sub, sizeof(sub), "%s.", qstr_str(name));
                register_map(&t->locals_dict->map, sub, 1);
            }
        }
    }
}

extern const mp_obj_module_t mp_module_builtins;
extern const mp_obj_module_t mp_module_math;
extern const mp_obj_module_t mp_module_cmath;
extern const mp_obj_module_t mp_module_urandom;
extern const mp_obj_module_t mp_module_casioplot;

static void load_costs(const char *path) {
    FILE *f = fopen(path, "r");
    if (!f) {
        fprintf(stderr, "cgtime: can't read costs file %s, running untimed\n", path);
        return;
    }
    char line[128], name[64], buf[64];
    double c;
    int unknown = 0;
    while (fgets(line, sizeof(line), f)) {
        if (line[0] == '#' || sscanf(line, "%63s %lf", name, &c) != 2) {
            continue;
        }
        int ev;
        for (ev = 0; ev < CG_EV_MAX; ev++) {
            if (strcmp(cg_event_name(ev, buf, sizeof(buf)), name) == 0) {
                cost[ev] = c;
                break;
            }
        }
        unknown += ev == CG_EV_MAX;
    }
    fclose(f);
    if (unknown) {
        fprintf(stderr, "cgtime: %d unknown events in %s\n", unknown, path);
    }
}

static const void *iternext_list, *iternext_range;

void cg_count_iter(uintptr_t obj) {
    const void *f = (const void*)mp_obj_get_type((mp_obj_t)obj)->iternext;
    cg_count[f == iternext_list ? CG_EV_ITER_LIST
             : f == iternext_range ? CG_EV_ITER_RANGE : CG_EV_ITER_OTHER]++;
}

void cg_init(void) {
    // iterator types aren't exported: take them from sample iterators
    iternext_list = (const void*)mp_obj_get_type(mp_getiter(mp_obj_new_list(0, NULL), NULL))->iternext;
    iternext_range = (const void*)mp_obj_get_type(mp_getiter(
        mp_call_function_1(MP_OBJ_FROM_PTR(&mp_type_range), MP_OBJ_NEW_SMALL_INT(1)), NULL))->iternext;
    register_map(&mp_module_builtins.globals->map, "", 0);
    register_map(&mp_module_math.globals->map, "math.", 1);
    #if MICROPY_PY_CMATH
    register_map(&mp_module_cmath.globals->map, "cmath.", 1);
    #endif
    register_map(&mp_module_urandom.globals->map, "random.", 1);
    register_map(&mp_module_casioplot.globals->map, "casioplot.", 1);
    const char *costs = getenv("CG100_COSTS");
    if (costs) {
        load_costs(costs);
    }
    // finish in step with the calculator, not up to CG_TICK_OPS early
    atexit(cg_tick);
    const char *fast = getenv("CG100_FAST");
    have_costs = costs != NULL;
    throttle = costs && !(fast && fast[0] == '1');
    clock_gettime(CLOCK_MONOTONIC, &start);
    signal(SIGRTMIN, on_fast);
    signal(SIGRTMIN + 1, on_fast);
}

const char *cg_event_name(int ev, char *buf, size_t len) {
    static const char *const cls[5] = {"small", "float", "big", "bool", "other"};
    if (ev < CG_EV_BINOP) {
        if (opname[ev]) {
            snprintf(buf, len, "op_%s", opname[ev]);
        } else {
            snprintf(buf, len, "op_%02x", ev);
        }
    } else if (ev < CG_EV_BINOP + CG_BINOP_MAX * 5) {
        int op = (ev - CG_EV_BINOP) / 5;
        qstr q = mp_binary_op_method_name[op];
        // a few ops share a method name (in / __contains__): number the later ones
        int dup = 0;
        for (int o = 0; o < op; o++) {
            dup |= mp_binary_op_method_name[o] == q;
        }
        if (dup) {
            snprintf(buf, len, "bin_%s%d_%s", qstr_str(q), op, cls[(ev - CG_EV_BINOP) % 5]);
        } else {
            snprintf(buf, len, "bin_%s_%s", qstr_str(q), cls[(ev - CG_EV_BINOP) % 5]);
        }
    } else if (ev >= CG_EV_ATTR && ev < CG_EV_ATTR + 12) {
        static const char *const kind[3] = {"load", "store", "method"};
        static const char *const ac[4] = {"instance", "module", "type", "native"};
        snprintf(buf, len, "attr_%s_%s", kind[(ev - CG_EV_ATTR) / 4], ac[(ev - CG_EV_ATTR) % 4]);
    } else if (ev >= CG_EV_SUBSCR && ev < CG_EV_SUBSCR + 10) {
        static const char *const sc[5] = {"list", "tuple", "str", "dict", "other"};
        snprintf(buf, len, "subscr_%s_%s", (ev - CG_EV_SUBSCR) / 5 ? "store" : "load",
                 sc[(ev - CG_EV_SUBSCR) % 5]);
    } else if (ev >= CG_EV_FN) {
        if (ev - CG_EV_FN < fn_count) {
            snprintf(buf, len, "fn_%s", fn_name[ev - CG_EV_FN]);
        } else {
            snprintf(buf, len, "fn_unused_%d", ev - CG_EV_FN);
        }
    } else {
        const char *n;
        switch (ev) {
            case CG_EV_UNARY: n = "unary"; break;
            case CG_EV_CALL_BC: n = "call_py"; break;
            case CG_EV_CALL_ARG: n = "call_arg"; break;
            case CG_EV_CALL_KW: n = "call_kw"; break;
            case CG_EV_CALL_NATIVE: n = "call_native"; break;
            case CG_EV_CALL_OTHER: n = "call_other"; break;
            case CG_EV_CALL_CLOSURE: n = "call_closure"; break;
            case CG_EV_CALL_BOUND: n = "call_bound"; break;
            case CG_EV_CALL_NEW: n = "call_new"; break;
            case CG_EV_ALLOC: n = "alloc"; break;
            case CG_EV_ALLOC_SCAN: n = "alloc_scan"; break;
            case CG_EV_GC: n = "gc"; break;
            case CG_EV_QSTR_FIND: n = "qstr_find"; break;
            case CG_EV_QSTR_SCAN: n = "qstr_scan"; break;
            case CG_EV_BIG_DIGITS: n = "big_digits"; break;
            case CG_EV_PIXEL_ON: n = "pixel_on"; break;
            case CG_EV_PIXEL_OFF: n = "pixel_off"; break;
            case CG_EV_CHAR_SMALL: n = "char_small"; break;
            case CG_EV_CHAR_MEDIUM: n = "char_medium"; break;
            case CG_EV_CHAR_LARGE: n = "char_large"; break;
            case CG_EV_PRINT_CHAR: n = "print_char"; break;
            case CG_EV_PRINT_LINE: n = "print_line"; break;
            case CG_EV_GETKEY_IDLE: n = "getkey_idle"; break;
            case CG_EV_GETKEY_HELD: n = "getkey_held"; break;
            case CG_EV_PRINT_WRITE: n = "print_write"; break;
            case CG_EV_POW_DIGITS: n = "pow_digits"; break;
            case CG_EV_LEX_CHAR: n = "lex_char"; break;
            case CG_EV_SHOW_ROW: n = "show_row"; break;
            case CG_EV_SHOW_ANY: n = "show_any"; break;
            case CG_EV_ITER_LIST: n = "iter_list"; break;
            case CG_EV_ITER_RANGE: n = "iter_range"; break;
            case CG_EV_ITER_OTHER: n = "iter_other"; break;
            case CG_EV_MUL_WORK: n = "mul_work"; break;
            case CG_EV_SUM_ITEM: n = "sum_item"; break;
            case CG_EV_INT_BYTES: n = "int_bytes"; break;
            case CG_EV_GC_MARK: n = "gc_mark"; break;
            case CG_EV_MAP_PROBE: n = "map_probe"; break;
            case CG_EV_MAP_SCAN: n = "map_scan"; break;
            default: n = NULL;
        }
        if (n) {
            snprintf(buf, len, "%s", n);
        } else {
            snprintf(buf, len, "ev_%d", ev);
        }
    }
    return buf;
}

double cg_vtime_us(void) {
    double t = 0;
    for (int i = 0; i < CG_EV_MAX; i++) {
        t += cost[i] * cg_count[i];
    }
    return t;
}

void cg_tick(void) {
    cg_tick_countdown = CG_TICK_OPS;
    // [AC] interrupts the script wherever it is, as on the calculator
    if (cg_screen_break()) {
        mp_obj_exception_clear_traceback(MP_OBJ_FROM_PTR(&MP_STATE_VM(mp_kbd_exception)));
        MP_STATE_VM(mp_pending_exception) = MP_OBJ_FROM_PTR(&MP_STATE_VM(mp_kbd_exception));
    }
    if (fast_req >= 0) {
        int want = have_costs && !fast_req;
        fast_req = -1;
        if (want && !throttle) {
            // Real time from here on: line the clock up with virtual time, so nothing is caught up
            clock_gettime(CLOCK_MONOTONIC, &start);
            double v = cg_vtime_us();
            long long s = (long long)(v / 1e6), ns = (long long)((v - s * 1e6) * 1e3);
            start.tv_sec -= s;
            start.tv_nsec -= ns;
            while (start.tv_nsec < 0) {
                start.tv_nsec += 1000000000;
                start.tv_sec--;
            }
        }
        throttle = want;
    }
    if (!throttle) {
        return;
    }
    struct timespec now;
    clock_gettime(CLOCK_MONOTONIC, &now);
    double wall = (now.tv_sec - start.tv_sec) * 1e6 + (now.tv_nsec - start.tv_nsec) / 1e3;
    double ahead = cg_vtime_us() - wall;
    if (ahead > 500) {
        struct timespec d = {(time_t)(ahead / 1e6), (long)((ahead - (time_t)(ahead / 1e6) * 1e6) * 1e3)};
        nanosleep(&d, NULL);
    }
}

// Waiting for the user is not the script's time: move the start of the
// clock on by the wait, or the script would run flat out afterwards to
// catch up
static struct timespec paused;

void cg_time_pause(void) {
    clock_gettime(CLOCK_MONOTONIC, &paused);
}

void cg_time_resume(void) {
    struct timespec now;
    clock_gettime(CLOCK_MONOTONIC, &now);
    start.tv_sec += now.tv_sec - paused.tv_sec;
    start.tv_nsec += now.tv_nsec - paused.tv_nsec;
    while (start.tv_nsec >= 1000000000) {
        start.tv_nsec -= 1000000000;
        start.tv_sec++;
    }
    while (start.tv_nsec < 0) {
        start.tv_nsec += 1000000000;
        start.tv_sec--;
    }
}

void cg_count_call(const void *fun, const void *type, size_t n_args, size_t n_kw) {
    int i = fn_lookup(fun);
    if (i >= 0) {
        cg_count[CG_EV_FN + i]++;
    } else if (type == &mp_type_fun_bc) {
        cg_count[CG_EV_CALL_BC]++;
    } else if (type == &mp_type_fun_builtin_0 || type == &mp_type_fun_builtin_1
               || type == &mp_type_fun_builtin_2 || type == &mp_type_fun_builtin_3
               || type == &mp_type_fun_builtin_var) {
        cg_count[CG_EV_CALL_NATIVE]++;
    } else if (((const mp_obj_type_t*)type)->name == MP_QSTR_closure) {
        cg_count[CG_EV_CALL_CLOSURE]++;
    } else if (((const mp_obj_type_t*)type)->name == MP_QSTR_bound_method) {
        cg_count[CG_EV_CALL_BOUND]++;
    } else if (type == &mp_type_type) {
        cg_count[CG_EV_CALL_NEW]++;
    } else {
        cg_count[CG_EV_CALL_OTHER]++;
    }
    cg_count[CG_EV_CALL_ARG] += n_args;
    cg_count[CG_EV_CALL_KW] += n_kw;
}

static int big_digits(mp_obj_t o) {
    if (MP_OBJ_IS_TYPE(o, &mp_type_int)) {
        return ((mp_obj_int_t*)MP_OBJ_TO_PTR(o))->mpz.len;
    }
    return -1;
}

void cg_count_binop(int op, uintptr_t lhs_u, uintptr_t rhs_u) {
    mp_obj_t lhs = (mp_obj_t)lhs_u, rhs = (mp_obj_t)rhs_u;
    // a += b costs the same as a + b for the immutable types measured
    if (op >= MP_BINARY_OP_INPLACE_OR && op <= MP_BINARY_OP_INPLACE_POWER) {
        op += MP_BINARY_OP_OR - MP_BINARY_OP_INPLACE_OR;
    }
    int cls;
    int dl = big_digits(lhs), dr = big_digits(rhs);
    // All ordering comparisons share one C path, as do == and !=
    if (op == MP_BINARY_OP_MORE || op == MP_BINARY_OP_LESS_EQUAL || op == MP_BINARY_OP_MORE_EQUAL) {
        op = MP_BINARY_OP_LESS;
    } else if (op == MP_BINARY_OP_NOT_EQUAL) {
        op = MP_BINARY_OP_EQUAL;
    }
    #define CG_BOOL(o) ((o) == mp_const_true || (o) == mp_const_false)
    if (MP_OBJ_IS_SMALL_INT(lhs) && MP_OBJ_IS_SMALL_INT(rhs)) {
        cls = CG_CLS_SMALL;
        // A small-int power that overflows becomes big-int work (3**200)
        mp_int_t b = MP_OBJ_SMALL_INT_VALUE(lhs), e = MP_OBJ_SMALL_INT_VALUE(rhs);
        if (op == MP_BINARY_OP_POWER && e > 1 && b != 0 && b != 1 && b != -1) {
            double bits = log2(fabs((double)b)) * e;
            if (bits > 30) {
                cls = CG_CLS_BIG;
                cg_count[CG_EV_POW_DIGITS] += (uint32_t)(bits / MPZ_DIG_SIZE) + 1;
            }
        }
    } else if ((CG_BOOL(lhs) || MP_OBJ_IS_SMALL_INT(lhs)) && (CG_BOOL(rhs) || MP_OBJ_IS_SMALL_INT(rhs))) {
        cls = CG_CLS_BOOL;
    } else if (mp_obj_is_float(lhs) || mp_obj_is_float(rhs)) {
        cls = CG_CLS_FLOAT;
    } else if (dl >= 0 || dr >= 0) {
        cls = CG_CLS_BIG;
        cg_count[CG_EV_BIG_DIGITS] += (dl > 0 ? dl : 1) + (dr > 0 ? dr : 1);
        if (op == MP_BINARY_OP_MULTIPLY) {
            cg_count[CG_EV_MUL_WORK] += (dl > 0 ? dl : 1) * (dr > 0 ? dr : 1);
        }
    } else {
        cls = CG_CLS_OTHER;
    }
    if (op < CG_BINOP_MAX) {
        cg_count[CG_EV_BINOP + op * 5 + cls]++;
    }
}

static int attr_class(mp_obj_t base) {
    mp_obj_type_t *t = mp_obj_get_type(base);
    if (mp_obj_is_instance_type(t)) {
        return 0;
    }
    if (t == &mp_type_module) {
        return 1;
    }
    if (t == &mp_type_type) {
        return 2;
    }
    return 3;
}

void cg_count_attr(int kind, uintptr_t base) {
    cg_count[CG_EV_ATTR + kind * 4 + attr_class((mp_obj_t)base)]++;
}

void cg_count_subscr(int store, uintptr_t base_u) {
    mp_obj_t base = (mp_obj_t)base_u;
    int cls;
    if (MP_OBJ_IS_TYPE(base, &mp_type_list)) {
        cls = 0;
    } else if (MP_OBJ_IS_TYPE(base, &mp_type_tuple)) {
        cls = 1;
    } else if (MP_OBJ_IS_STR(base)) {
        cls = 2;
    } else if (MP_OBJ_IS_TYPE(base, &mp_type_dict)) {
        cls = 3;
    } else {
        cls = 4;
    }
    cg_count[CG_EV_SUBSCR + store * 5 + cls]++;
}
