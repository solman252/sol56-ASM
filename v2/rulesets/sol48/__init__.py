from main import *
from rulesets import *

NAME = 'sol48'

MIN_ADDR_UNIT = 16
INSTRUCTION_SIZE = 48

REGISTERS = {
    'pc': 16,
    'iflags': 16,
    'res': 16,
    'ar': 16,
    'br': 16,
    'cr': 16,
    'dr': 16,
    'er': 16,
    'fr': 16,
}

FLAGS = [
    'zf',
    'sf',
    'cf',
    'of',
    'if',
    'rf',
]

def CLOCK():
    pass

def INSTRUCTION_FACTORY():
    INSTRUCTION_FORMAT = 'opcode`8 @ type1`4 @ type2`4 @ arg1`16 @ arg2`16'
    arguments = {k: bits for k,bits in (arg.split('`') for arg in INSTRUCTION_FORMAT.split(' @ ')) if k != 'opcode'}
    opcodes = {k: v for k,v in {
        'nop': '0x00',
        'time': '0x01',

        'mov': '0x10',

        'add': '0x20',
        'adc': '0x21',
        'sub': '0x22',
        'sbb': '0x23',
        'div': '0x24',
        'idiv': '0x25',
        'mul': '0x26',
        'imul': '0x27',
        'mod': '0x28',
        'imod': '0x29',
        'inc': '0x2a',
        'dec': '0x2b',
        'neg': '0x2c',
        'abs': '0x2d',
        'min': '0x2e',
        'max': '0x2f',

        'and': '0x30',
        'or': '0x31',
        'xor': '0x32',
        'not': '0x33',
        'nand': '0x34',
        'nor': '0x35',
        'xnor': '0x36',

        'shl': '0x40',
        'shr': '0x41',
        'sar': '0x42',
        'rol': '0x43',
        'ror': '0x44',
        'rcl': '0x45',
        'rcr': '0x46',

        'set': '0x50',
        'clr': '0x51',
        'cmp': '0x52',
        'test': '0x53',

        'jmp': '0x60',
        'jif': '0x61',
        'jnf': '0x62',
        'jlt': '0x63',
        'jle': '0x64',
        'jgt': '0x65',
        'jge': '0x66',
        'jbe': '0x67',
        'ja': '0x68',

        'hlt': '0x70',
        'int': '0x71',
        'intd': '0x72',
        'iret': '0x73',

        'pwd': '0x80',

        'debug msg enable': '0xa0',
        'debug msg disable': '0xa1',
        'debug msg whitelist': '0xa2',
        'debug msg blacklist': '0xa3',
        'debug msg whitelist all': '0xa4',
        'debug msg blacklist all': '0xa5',
        'debug read': '0xa6',
    }.items()}
    def dummy_func(): ...

    return {INSTRUCTION_FORMAT.replace('opcode`8',v): Instruction(k,globals().get(f'INST_{k.upper().replace(' ','_')}',dummy_func),arguments) for k,v in opcodes.items()}

def INST_NOP(type1: bitarray, type2: bitarray, arg1: bitarray, arg2: bitarray):
    pass