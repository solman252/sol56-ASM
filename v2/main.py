#region Imports
from pathlib import Path
import logging

import rulesets
#endregion Imports

#region Constants
BASE_PATH = Path(__file__).resolve().parent
PROGRAMS_FOLDER = BASE_PATH / 'programs'
#endregion Constants

def relative_path(path: Path | None = None) -> str:
    if path is None: path = Path(__file__).resolve()
    return str(path).removeprefix(str(BASE_PATH))[1:]

#region Logging
DEBUG_LOG = BASE_PATH / 'latest.log'
ERROR_LOG = BASE_PATH / 'error.log'

logger_format = {'datefmt':'%d/%m/%y %I:%M:%S %p', 'format':'%(levelname)s in %(name)s at (%(asctime)s): %(message)s'}
logger_formatter = logging.Formatter(logger_format['format'],logger_format['datefmt'])

logging.basicConfig(filename=DEBUG_LOG, filemode='w', encoding='utf-8', level=logging.DEBUG, datefmt=logger_format['datefmt'], format=logger_format['format'])
logger = logging.getLogger(relative_path())

class LogHandler(logging.Handler):
    def __init__(self):
        super().__init__()
        self.log = []

    def emit(self, record):
        match record.levelno:
            case logging.DEBUG: color = '\033[1;34m'
            case logging.INFO: color = '\033[1m'
            case logging.WARNING: color = '\033[1;33m'
            case logging.ERROR: color = '\033[1;31m'
        self.log.append(color+logger_formatter.format(record)+'\033[0m')

log_storage = LogHandler()
logger.addHandler(log_storage)

debug_mode = False
def __log(level: int, *values: object, sep: str | None = ' ', end: str | None = ''):
    logger.log(level, f'{sep.join(str(v) for v in values)}{end}')
    print(log_storage.log[-1])
def debug(*values: object, sep: str | None = ' ', end: str | None = ''):
    if debug_mode: __log(logging.DEBUG,*values,sep=sep,end=end)
def info(*values: object, sep: str | None = ' ', end: str | None = ''): __log(logging.INFO,*values,sep=sep,end=end)
def warning(*values: object, sep: str | None = ' ', end: str | None = ''): __log(logging.WARNING,*values,sep=sep,end=end)
def error(*values: object, sep: str | None = ' ', end: str | None = ''): __log(logging.ERROR,*values,sep=sep,end=end)
#endregion Logging

def assemble(program: str, assembly: str, ruleset: rulesets.Ruleset | None = None) -> tuple[str, str]:
    info(f'Attempting to assemble program "{program}"...')

    #region Fetch Ruleset
    if ruleset is None:
        #region Automatic Fetch
        warning(f'No ruleset provided, attempting to fetch from program...')

        line1 = assembly.splitlines()[0]
        if line1.startswith('#include "rules/') and line1.endswith('.asm"') and line1.count('"') == 2:
            ruleset = line1.removeprefix('#include "rules/').removesuffix('.asm"')
            info(f'Ruleset defined by program to be "{ruleset}".')

            if ruleset in rulesets.rulesets:
                ruleset = rulesets.rulesets[ruleset]
            else:
                warning(f'Ruleset "{ruleset}" could not be found.')
                ruleset = None
        #endregion Automatic Fetch

        #region Manual Fetch
        if ruleset is None:
            warning('No valid ruleset was defined, and will need to be manually provided.')

            ruleset_options = {(str(i+1)): v for i,v in enumerate(rulesets.rulesets.values())}
            print(f'Please select a ruleset by number:\n  {'\n  '.join(f'{i}: {v.name}' for i,v in ruleset_options.items())})',end='\n> ')
            clear_len = 0
            while ruleset is None:
                try: inp = input('\033[s')
                except KeyboardInterrupt: exit()
                if inp in ruleset_options:
                    ruleset = ruleset_options[inp]
                    info(f'Ruleset "{ruleset.name}" was manually selected.')
                else:
                    print(f'"{inp}" is not an option.'+(' '*(clear_len-len(inp))))
                    clear_len = len(inp)
                    print('\033[u',' '*clear_len,f'\033[{clear_len}D',sep='',end='')
        #endregion Manual Fetch
    #endregion Fetch Ruleset

    # Insert ruleset
    ruleset.generate_file()
    assembly = f'#include "rules/{ruleset.name}.asm"\n{assembly}'

    #region Assemble
    import assembler, subprocess

    try:
        bytecode_bin, bytecode_hex = assembler.assemble(
            output_type=assembler.OutputType.BOTH,
            assembly=assembly,
            min_addr_unit=ruleset.min_addr
        )
    except subprocess.CalledProcessError as e:
        from strip_ansi import strip_ansi
        with open(ERROR_LOG,'w') as f: f.write(strip_ansi(e.stderr).removesuffix('\n'))
        error(f'The program could not be assembled, see "{ERROR_LOG}" for more details.')
        exit(1)
    #endregion Assemble

    return bytecode_bin, bytecode_hex

def main():
    #region Argument Parsing
    import argparse

    arg_parser = argparse.ArgumentParser(formatter_class=argparse.MetavarTypeHelpFormatter)
    arg_parser.add_argument(
        '-p', '--program',
        default = str(PROGRAMS_FOLDER / 'test.asm'),
        help = 'the program to assemble',
        type = Path
    )
    arg_parser.add_argument(
        '-r', '--run',
        default = True,
        help = 'run the emulator',
        action='store_true'
    )
    arg_parser.add_argument(
        '-d', '--debug',
        default = True,
        help = 'enable debug logging',
        action='store_true'
    )

    args = arg_parser.parse_args()

    global debug_mode
    debug_mode = args.debug
    #endregion Argument Parsing
    
    try:
        with open(args.program,'r') as f: program = f.read()
    except FileNotFoundError:
        error(f'Program "{program}" does not exist!')
        exit(1)
    bytecode_bin, bytecode_hex = assemble(args.program,program)

#region Boilerplate
if __name__ == '__main__': main()
__all__ = [
    #region Modules
    'rulesets',
    #endregion Modules

    #region Constants
    'BASE_PATH',
    'PROGRAMS_FOLDER',
    #endregion Constants

    #region Helper Functions
    'relative_path',
    #endregion Helper Functions

    #region Logging
    'debug_mode',
    'debug',
    'info',
    'warning',
    'error',
    #endregion Logging

    #region Core Functionality
    'assemble',
    'main',
    #endregion Core Functionality
]
#endregion Boilerplate