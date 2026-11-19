// cgemu: emulator internals, for fitting and checking the timing model.
#include <string.h>
#include "py/runtime.h"
#include "py/obj.h"
#include "cgtime.h"

// counts() -> list of every event counter
STATIC mp_obj_t cgemu_counts(void) {
    mp_obj_t l = mp_obj_new_list(CG_EV_MAX, NULL);
    mp_obj_t *items;
    size_t len;
    mp_obj_list_get(l, &len, &items);
    for (int i = 0; i < CG_EV_MAX; i++) {
        items[i] = mp_obj_new_int_from_ull(cg_count[i]);
    }
    return l;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(cgemu_counts_obj, cgemu_counts);

// names() -> list of event names, same order as counts()
STATIC mp_obj_t cgemu_names(void) {
    mp_obj_t l = mp_obj_new_list(CG_EV_MAX, NULL);
    mp_obj_t *items;
    size_t len;
    char buf[64];
    mp_obj_list_get(l, &len, &items);
    for (int i = 0; i < CG_EV_MAX; i++) {
        const char *n = cg_event_name(i, buf, sizeof(buf));
        items[i] = mp_obj_new_str(n, strlen(n));
    }
    return l;
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(cgemu_names_obj, cgemu_names);

// vtime() -> virtual time in seconds
STATIC mp_obj_t cgemu_vtime(void) {
    return mp_obj_new_float(cg_vtime_us() / 1e6);
}
STATIC MP_DEFINE_CONST_FUN_OBJ_0(cgemu_vtime_obj, cgemu_vtime);

STATIC const mp_rom_map_elem_t cgemu_globals_table[] = {
    { MP_ROM_QSTR(MP_QSTR___name__), MP_ROM_QSTR(MP_QSTR_cgemu) },
    { MP_ROM_QSTR(MP_QSTR_counts), MP_ROM_PTR(&cgemu_counts_obj) },
    { MP_ROM_QSTR(MP_QSTR_names), MP_ROM_PTR(&cgemu_names_obj) },
    { MP_ROM_QSTR(MP_QSTR_vtime), MP_ROM_PTR(&cgemu_vtime_obj) },
};
STATIC MP_DEFINE_CONST_DICT(cgemu_globals, cgemu_globals_table);

const mp_obj_module_t mp_module_cgemu = {
    .base = { &mp_type_module },
    .globals = (mp_obj_dict_t*)&cgemu_globals,
};
