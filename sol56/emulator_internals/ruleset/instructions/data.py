from emulator_internals.helpers import *

def exec_mov_lod(self: CPU, variant: str, reg1: str, f_reg2: str, val1: str, load: bool = False, all: bool = False):
    val_is_flag = variant == '0010' and not load
    reg_key = min(self.registers.keys(), key=lambda k: self.registers[k].size) if all else reg_keys[reg1]
    val = int_to_bin(int(self.flags[flag_keys[f_reg2]]),self.registers[reg_key].size) if val_is_flag else register_or_val(self,f_reg2,val1)
    if load: val = self.RAM.read(int(val,2)*self.ruleset.mem_depth,self.ruleset.mem_depth)

    for reg_key in (internal.ruleset.registers.keys() if all else [reg_key]):
        reg = self.registers[reg_key]
        v = val.zfill(reg.size)
        while len(v) > reg.size: v = v[1:]
        reg.write(v)
        debug(self,f'{'Result register' if reg_key == 'res' else f'Register {reg_key.upper()}'} set to 0x{bin_to_hex(v)}')

def exec_str(self: CPU, variant: str, reg1: str, reg2: str, val1: str, val2: str):
    

# CONTINUE HERE SOL

instructions = {
    'mov': ('0x12 @ 0x0 @ variant`4 @ reg1`4 @ f_reg2`4 @ val1`16 @ 0x0000', exec_mov_lod),
    'mov all': ('0x12 @ 0x1 @ variant`4 @ reg1`4 @ f_reg2`4 @ val1`16 @ 0x0000', lambda self, **kwargs: exec_mov_lod(self, **kwargs, all = True)),

    'ldr': ('0x13 @ 0x0 @ variant`4 @ reg1`4 @ f_reg2`4 @ val1`16 @ 0x0000', lambda self, **kwargs: exec_mov_lod(self, **kwargs, load = True)),
    'ldr all': ('0x13 @ 0x1 @ variant`4 @ reg1`4 @ f_reg2`4 @ val1`16 @ 0x0000', lambda self, **kwargs: exec_mov_lod(self, **kwargs, load = True, all = True)),
    
    'str': ('0x14 @ variant`8 @ reg1`4 @ reg2`4 @ val1`16 @ val2`16', dummy_func),
}