from src import *

import logging as pylogger

TIMED_LOG = paths.LOGS / datetime.now().strftime('%d-%m-%Y.log')
LATEST_LOG = paths.LOGS / 'latest.log'
ASSEMBLE_ERROR_LOG = paths.LOGS / 'assemble_error.log'
CONSOLE_LOG_COLORS = {
    pylogger.DEBUG: '\033[1;35m',
    pylogger.INFO: '\033[1m',
    pylogger.WARNING: '\033[1;33m',
    pylogger.ERROR: '\033[1;31m',
}

class LoggerFormatter(pylogger.Formatter):
    def __init__(self, fmt = None, datefmt = None, style = "%", validate = True, *, defaults = None, colored: bool = False):
        super().__init__(fmt, datefmt, style, validate, defaults=defaults)
        self.colored = colored

    def format(self, record):
        color = CONSOLE_LOG_COLORS.get(record.levelno, '\033[0m') if self.colored else ''
        indent = '  '*getattr(record, 'indentation_level', 0)
        should_format = getattr(record, 'should_format', True)
        message = super().format(record) if should_format else record.msg
        return f'{indent}{color}{message}{'\033[0m' if self.colored else ''}'

pylogger_format = (
    '%(levelname)s (%(asctime)s): %(message)s',
    '%d/%m/%y %I:%M:%S %p'
)

logger = None
def init():
    global logger

    logger_formatter = LoggerFormatter(*pylogger_format)
    logger_console_formatter = LoggerFormatter(*pylogger_format, colored = True)
    
    logger = pylogger.getLogger()
    logger.setLevel(pylogger.DEBUG)
    logger.handlers.clear()

    logger_console_handler = pylogger.StreamHandler()
    logger_console_handler.setFormatter(logger_console_formatter)
    logger.addHandler(logger_console_handler)

    logger_latest_handler = pylogger.FileHandler(LATEST_LOG,mode='w')
    logger_latest_handler.setFormatter(logger_formatter)
    logger.addHandler(logger_latest_handler)

    logger_timed_handler = pylogger.FileHandler(filename=TIMED_LOG,mode='a')
    logger_timed_handler.setFormatter(logger_formatter)
    logger.addHandler(logger_timed_handler)

persistent_log_indent = 0

def __log(level: int, *values: object, sep: str | None = ' ', end: str | None = '', indent: int = 0, set_indent: bool = False, should_format: bool = True):
    if set_indent: set_log_indent_level(indent)
    else: edit_log_indent_level(indent)
    logger.log(level, f'{sep.join(str(v) for v in values)}{end}', extra={'indentation_level': persistent_log_indent, 'should_format': should_format})

def debug(*values: object, sep: str | None = ' ', end: str | None = '', indent: int = 0, set_indent: bool = False, should_format: bool = True):
    __log(pylogger.DEBUG,*values,sep=sep,end=end,indent=indent,set_indent=set_indent,should_format=should_format)

def info(*values: object, sep: str | None = ' ', end: str | None = '', indent: int = 0, set_indent: bool = False, should_format: bool = True):
    __log(pylogger.INFO,*values,sep=sep,end=end,indent=indent,set_indent=set_indent,should_format=should_format)

def warning(*values: object, sep: str | None = ' ', end: str | None = '', indent: int = 0, set_indent: bool = False, should_format: bool = True):
    __log(pylogger.WARNING,*values,sep=sep,end=end,indent=indent,set_indent=set_indent,should_format=should_format)

def error(*values: object, sep: str | None = ' ', end: str | None = '', indent: int = 0, set_indent: bool = False, should_format: bool = True):
    __log(pylogger.ERROR,*values,sep=sep,end=end,indent=indent,set_indent=set_indent,should_format=should_format)
    exit(1)

def edit_log_indent_level(indent: int = 0):
    global persistent_log_indent
    persistent_log_indent += indent

def set_log_indent_level(indent: int = 0):
    global persistent_log_indent
    persistent_log_indent = indent

def get_log_indent(): return '  '*persistent_log_indent

def get_log_indent_level(): return persistent_log_indent

__all__ = [
    'init',

    'debug',
    'info',
    'warning',
    'error',

    'set_log_indent_level',
    'edit_log_indent_level',
    'get_log_indent_level',
    'get_log_indent',
]