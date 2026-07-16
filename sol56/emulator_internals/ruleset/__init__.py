from emulator_internals.helpers import *
import emulator_internals.ruleset.instructions as instructions

from typing import Any

__all__ = ['instructions','inst_depth','mem_depth','interrupt_codes','registers','flags','init','execution_stage']

inst_depth = 56
mem_depth = 16
interrupt_codes = 256
registers = {'a':16,'b':16,'c':16,'d':16,'e':16,'f':16,'g':16,'h':16,'res':16}
flags = ['s','c','z','n','o']

def init():
    ruleset = Ruleset(
        inst_depth,
        mem_depth,
        interrupt_codes,
        registers,
        flags,

        internal.video.init,
        internal.video.handler,
        internal.interrupts.caller,
        execution_stage,
    )

    ruleset.execution_funcs = {}

    for inst, (opcode, exec) in (inst for category in instructions.modules.values() for inst in category.instructions.items()):
        ruleset.add_rule(inst,opcode)
        ruleset.execution_funcs[inst] = exec
    
    return ruleset

def execution_stage(self: CPU, opcode: str, inst: str, args: dict[str,str]):
    debug(self,f'{inst}({str(args)[1:-2].replace('\'','').replace(',',', ')}) => {{',end='',indent=False)
    out: None | dict[str,Any] = self.ruleset.execution_funcs[inst](self,**args)
    if type(out) != dict: out = {}
    if out.get('PC += 1',True) == True: self.PC += 1
    debug(self,'}',indent=False)