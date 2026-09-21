from sol48.emulator_internals.helpers import *
import sol48.emulator_internals.ruleset.instructions as instructions

__all__ = ['instructions','inst_depth','mem_depth','interrupt_codes','registers','flags','init','execution_stage']

inst_depth = 3
mem_depth = 16
interrupt_codes = 256
registers = {'pc':16,'iflags':16,'res':16,'a':16,'b':16,'c':16,'d':16,'e':16,'f':16,'g':16}
flags = ['z','s','c','o','i','r']

def init(debug_mode: bool = False):

    if debug_mode: print('Initializing Ruleset')

    ruleset = Ruleset(
        inst_depth,
        mem_depth,
        interrupt_codes,
        registers,
        flags,

        internal.video.init,
        internal.video.handler,
        internal.interrupts.caller,
        internal.interrupts.exception_handler,
        [0x04,0x05,0x06,0x07],
        internal.interrupts.on_enter,
        internal.interrupts.on_exit,
        execution_stage,
        setup
    )

    ruleset.execution_funcs = {}

    if debug_mode: print('  Initializing Rules:')

    for category_name, category_module in instructions.modules.items():
        if debug_mode: print(f'    Initializing Category "{category_name}":')
        exec_funcs: dict[str,FunctionType] = {k: v for k,v in category_module.__dict__.items() if k.startswith('exec_')}
        for func_name, func in exec_funcs.items():
            opcode = func_name.split('_')[1]
            if debug_mode: print(f'      Opcode "{opcode}" assigned to function {category_name}.{func_name}')
            ruleset.add_rule(opcode,f'{opcode} @ arg1_type`4 @ arg2_type`4 @ arg1`16 @ arg2`16')
            ruleset.execution_funcs[opcode] = func

    if debug_mode: print('Init complete.\n')

    return ruleset

def setup(self: CPU):
    self._debug_indented = False
    self._debug_whitelist = [True]*0xFF
    self.start_time = 0
    self.cstate_PC = 0

def execution_stage(self: CPU, inst_binary: str, inst: str, args: dict[str,str]):
    opcode = int(inst_binary[:8],2)
    if inst is not None:
        if opcode == 0xa0: self.debug_mode = True
        arg1_type = ARGTYPE(int(args['arg1_type'],2)) ; arg2_type = ARGTYPE(int(args['arg2_type'],2))
        debug(self,opcode,
            f'0x{int_to_hex(self.PC,self.ruleset.mem_depth)}: ', # Address
            f'{inst}({f'{arg1_type.name}: 0x{bin_to_hex(args['arg1'])}' if arg1_type != ARGTYPE.NONE else ''}{f', {arg2_type.name}: 0x{bin_to_hex(args['arg2'])}' if arg2_type != ARGTYPE.NONE else ''}) => {{' # instruction and arguments
        ,sep='',end='',indent=False)

        out: None | dict[str,Any] = self.ruleset.execution_funcs[inst](self,**args)
    else: out = {'Debug Closing': False}
    if type(out) != dict: out = {}

    if out.get('Debug Closing') is not False: debug(self,opcode,'}',indent=False,ignore_debug_mode=out.get('Debug Closing')) # closing bracket

    if out.get('INC PC',True) is True: self.PC = (self.PC + self.ruleset.inst_depth) % (0xFFFF+1)
    self.registers['pc'].write(int_to_bin(self.PC,self.registers['pc'].size))

    if out.get('Exit',False) is True: exit()