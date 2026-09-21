#region Imports
from pathlib import Path
from datetime import datetime
from bitarray import bitarray as _bitarray
import logging

from typing import Callable

import assembler, rulesets
#endregion Imports

#region Constants
BASE_PATH = Path(__file__).resolve().parent
PROGRAMS_FOLDER = BASE_PATH / 'programs'
PROGRAMS_FOLDER.mkdir(parents=True,exist_ok=True)
#endregion Constants

def relative_path(path: Path | None = None) -> str:
    if path is None: path = Path(__file__).resolve()
    return str(path).removeprefix(str(BASE_PATH))[1:]

#region Logging
LOG_FOLDER = BASE_PATH / 'logs'
LOG_FOLDER.mkdir(parents=True,exist_ok=True)

TIMED_LOG = LOG_FOLDER / datetime.now().strftime('%d-%m-%Y.log')
LATEST_LOG = LOG_FOLDER / 'latest.log'
ASSEMBLE_ERROR_LOG = LOG_FOLDER / 'assemble_error.log'
CONSOLE_LOG_COLORS = {
    logging.DEBUG: '\033[1;35m',
    logging.INFO: '\033[1m',
    logging.WARNING: '\033[1;33m',
    logging.ERROR: '\033[1;31m',
}

class LoggerFormatter(logging.Formatter):
    def __init__(self, fmt = None, datefmt = None, style = "%", validate = True, *, defaults = None, colored: bool = False):
        super().__init__(fmt, datefmt, style, validate, defaults=defaults)
        self.colored = colored

    def format(self, record):
        color = CONSOLE_LOG_COLORS.get(record.levelno, '\033[0m') if self.colored else ''
        indent = '  '*getattr(record, 'indentation_level', 0)
        should_format = getattr(record, 'should_format', True)
        message = super().format(record) if should_format else record.msg
        return f'{indent}{color}{message}{'\033[0m' if self.colored else ''}'

logging_format = (
    '%(levelname)s (%(asctime)s): %(message)s',
    '%d/%m/%y %I:%M:%S %p'
)

logger_formatter = LoggerFormatter(*logging_format)
logger_console_formatter = LoggerFormatter(*logging_format, colored = True)

logger = logging.getLogger(relative_path())
logger.setLevel(logging.DEBUG)
logger.handlers.clear()

logger_console_handler = logging.StreamHandler()
logger_console_handler.setFormatter(logger_console_formatter)
logger.addHandler(logger_console_handler)

logger_latest_handler = logging.FileHandler(LATEST_LOG,mode='w')
logger_latest_handler.setFormatter(logger_formatter)
logger.addHandler(logger_latest_handler)

logger_timed_handler = logging.FileHandler(filename=TIMED_LOG,mode='a')
logger_timed_handler.setFormatter(logger_formatter)
logger.addHandler(logger_timed_handler)

persistent_log_indent = 0

def __log(level: int, *values: object, sep: str | None = ' ', end: str | None = '', indent: int = 0, set_indent: bool = False, should_format: bool = True):
    if set_indent: set_log_indent_level(indent)
    else: edit_log_indent_level(indent)
    logger.log(level, f'{sep.join(str(v) for v in values)}{end}', extra={'indentation_level': persistent_log_indent, 'should_format': should_format})

def debug(*values: object, sep: str | None = ' ', end: str | None = '', indent: int = 0, set_indent: bool = False, should_format: bool = True):
    __log(logging.DEBUG,*values,sep=sep,end=end,indent=indent,set_indent=set_indent,should_format=should_format)

def info(*values: object, sep: str | None = ' ', end: str | None = '', indent: int = 0, set_indent: bool = False, should_format: bool = True):
    __log(logging.INFO,*values,sep=sep,end=end,indent=indent,set_indent=set_indent,should_format=should_format)

def warning(*values: object, sep: str | None = ' ', end: str | None = '', indent: int = 0, set_indent: bool = False, should_format: bool = True):
    __log(logging.WARNING,*values,sep=sep,end=end,indent=indent,set_indent=set_indent,should_format=should_format)

def error(*values: object, sep: str | None = ' ', end: str | None = '', indent: int = 0, set_indent: bool = False, should_format: bool = True):
    __log(logging.ERROR,*values,sep=sep,end=end,indent=indent,set_indent=set_indent,should_format=should_format)
    exit(1)

def edit_log_indent_level(indent: int = 0):
    global persistent_log_indent
    persistent_log_indent += indent

def set_log_indent_level(indent: int = 0):
    global persistent_log_indent
    persistent_log_indent = indent

def get_log_indent(): return '  '*persistent_log_indent

def get_log_indent_level(): return persistent_log_indent
#endregion Logging

#region Emulation
class bitarray(_bitarray):
    def __new__(cls, initializer: int | str | 'bitarray' | None = None):
        if initializer is None: initializer = '0'
        if type(initializer) == bitarray: initializer = str(initializer)
        if type(initializer) == str and not all(c in {'0', '1'} for c in initializer):
            if initializer.startswith('0b'): initializer = initializer[2:]
            if initializer.startswith('0x'): initializer = bin(int(initializer[2:].lower(),16))[2:].zfill((len(initializer)-2)*4)
        elif initializer is None: initializer = ''
        return super().__new__(cls, initializer, endian='big', buffer=None)

    def __init__(self, initializer: int | str | 'bitarray' | None = None): _bitarray.__init__(initializer)

    def __str__(self): return '0b'+self.to01()

    def to01_rounded(self, rounding_size: int = 4):
        s = self.to01()
        fill_size = (len(s) + rounding_size - 1) // rounding_size * rounding_size
        if self.endian == 'little': return self.to01().ljust(fill_size,'0')
        else: return self.to01().zfill(fill_size)

    def to_hex(self):
        s = self.to01_rounded()
        return f'0x{int(s,2):0{len(s) // 4}x}'

    def __int__(self): return int(self.to01(),2)

    def to_signed_int(self):
        if self[0]: return -int(~self)-1
        else: return int(self)

    def __reversed__(self): return bitarray(self.to01()[::-1])

    def __rotate(self, k: int): return super().rotate(k)

    def rotate(self, k: int):
        out = self.copy()
        out.__rotate(k)
        return out

class Register:
    def __init__(self, name: str, bits: int):
        self.name = name
        self.bits = bits
        self.data = bitarray(bits)

    def reset(self): self.data.setall(0)

    def read(self): return self.data.copy()

    def write(self, data: bitarray | str | int):
        data = bitarray(data)
        if len(data) > len(self.data): self.data = bitarray(data.to01()[len(data)-len(self.data):])
        elif len(data) < len(self.data): self.data = bitarray(data.to01().zfill(len(self.data)))

    def __and__(self, other):
        if isinstance(other,Register): other = other.data
        return self.data & other
    def __rand__(self, other): return self.__and__(other)

    def __or__(self, other):
        if isinstance(other,Register): other = other.data
        return self.data | other
    def __or__(self, other): return self.__or__(other)

    def __xor__(self, other):
        if isinstance(other,Register): other = other.data
        return self.data ^ other
    def __xor__(self, other): return self.__xor__(other)

    def __invert__(self): return ~self.data

    def __lshift__(self, shift):
        if isinstance(shift,Register): shift = int(shift.data)
        elif isinstance(shift,bitarray): shift = int(shift)
        return self.data << shift

    def __rshift__(self, shift):
        if isinstance(shift,Register): shift = int(shift.data)
        elif isinstance(shift,bitarray): shift = int(shift)
        return self.data >> shift

    def rotate(self, k: int):
        if isinstance(k,Register): k = int(k.data)
        elif isinstance(k,bitarray): k = int(k)
        return self.data.rotate(k)
#endregion Emulation

def assemble(program: str, assembly: str, ruleset: rulesets.Ruleset | None = None) -> tuple[str, str]:
    starting_indent = get_log_indent_level()
    info(f'Attempting to assemble program "{program}"...')

    #region Fetch Ruleset
    if ruleset is None:
        #region Automatic Fetch
        warning(f'No ruleset provided, attempting to fetch from program...',indent=1)

        line1 = assembly.splitlines()[0]
        if line1.startswith('#include "rulesets/') and line1.endswith('/rules.asm"') and line1.count('"') == 2 and line1.count('/') == 2:
            ruleset = line1.removeprefix('#include "rulesets/').removesuffix('/rules.asm"')

            if ruleset in rulesets.rulesets:
                info(f'Ruleset defined by program to be "{ruleset}".')
                ruleset = rulesets.rulesets[ruleset]
            else:
                info(f'Ruleset defined by program to be "{ruleset}".',indent=1)
                warning(f'Ruleset "{ruleset}" could not be found.')
                edit_log_indent_level(-1)
                ruleset = None
                assembly = assembly.removeprefix(line1+'\n')
        #endregion Automatic Fetch

        #region Manual Fetch
        if ruleset is None:
            warning('No valid ruleset was defined, and will need to be manually provided.')
            edit_log_indent_level(1)

            if len(rulesets.rulesets) == 0: error('No valid rulesets exist!')

            ruleset_options = {(str(i+1)): v for i,v in enumerate(rulesets.rulesets.values())}
            print(f'{get_log_indent()}Please select a ruleset by number:\n{get_log_indent()}  {f'\n{get_log_indent()}  '.join(f'{i}: "{v.name}"' for i,v in ruleset_options.items())}\n{get_log_indent()}> ',end='')
            clear_len = 0
            while ruleset is None:
                try: inp = input(f'\033[s')
                except KeyboardInterrupt: exit()
                if inp in ruleset_options:
                    ruleset = ruleset_options[inp]
                    info(f'Ruleset "{ruleset.name}" was manually selected.',indent=-1)
                    assembly = f'#include "rulesets/{ruleset.name}/rules.asm"\n{assembly}'
                else:
                    print(f'{get_log_indent()}"{inp}" is not an option.'+(' '*(clear_len-len(inp))))
                    clear_len = len(inp)
                    print('\033[u',' '*clear_len,f'\033[{clear_len}D',sep='',end='')
        #endregion Manual Fetch
    #endregion Fetch Ruleset

    # Ensure ruleset file is up to date
    info(should_format=False)
    ruleset.generate_file(starting_indent+1)
    info(should_format=False)

    #region Assemble
    import subprocess

    try:
        bytecode_bin, bytecode_hex = assembler.assemble(
            output_type=assembler.OutputType.BOTH,
            assembly=assembly,
            min_addr_unit=ruleset.min_addr
        )
    except subprocess.CalledProcessError as e:
        from strip_ansi import strip_ansi
        with open(ASSEMBLE_ERROR_LOG,'w') as f: f.write(strip_ansi(e.stderr).removesuffix('\n'))
        error(f'The program could not be assembled, see "{ASSEMBLE_ERROR_LOG}" for more details.')
    #endregion Assemble

    info(f'Program "{program}" succesfully assembled.',set_indent=True)

    return bytecode_bin, bytecode_hex

def main():
    #region Argument Parsing
    import argparse

    arg_parser = argparse.ArgumentParser(formatter_class=argparse.MetavarTypeHelpFormatter)
    arg_parser.add_argument(
        '-p', '--program',
        default = str(PROGRAMS_FOLDER / 'test.asm'),
        help = 'the program to assemble',
        type = Path,
        required=False
    )
    arg_parser.add_argument(
        '-r', '--run',
        default = True,
        help = 'run the emulator',
        action='store_true'
    )

    args = arg_parser.parse_args()

    if args.program is None: error(f'No program has been provided!')
    #endregion Argument Parsing

    try:
        with open(args.program,'r') as f: program = f.read()
    except FileNotFoundError:
        error(f'Program "{args.program}" does not exist!')
    bytecode_bin, bytecode_hex = assemble(args.program,program)

#region Boilerplate
if __name__ == '__main__': main()
__all__ = [
    #region Libraries
    'Callable',
    #endregion Libraries

    #region Modules
    'rulesets',
    #endregion Modules

    #region Constants
    'BASE_PATH',
    'PROGRAMS_FOLDER',
    #endregion Constants

    #region Internals
    'relative_path',
    'bitarray',
    'Register',
    #endregion Internals

    #region Logging
    'debug',
    'info',
    'warning',
    'error',
    'set_log_indent_level',
    'edit_log_indent_level',
    'get_log_indent_level',
    'get_log_indent',
    #endregion Logging

    #region Core Functionality
    'assemble',
    'main',
    #endregion Core Functionality
]
#endregion Boilerplate