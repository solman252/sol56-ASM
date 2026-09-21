from src import *

import inspect

class Ruleset:
    def __init__(self, name: str, min_addr_unit: int, instruction_size: int, registers: dict[str,int], flags: list[str], clock: Callable, instruction_factory: Callable):
        self.name = name
        self.min_addr = min_addr_unit
        self.path = paths.RULESETS / self.name
        self.registers = registers.copy()
        self.flags = flags.copy()
        self.clock = clock

        self.instructions: dict[str, Instruction] = instruction_factory()

        logging.debug('self.instructions -> {')
        logging.edit_log_indent_level(1)
        for k,v in self.instructions.items():
            logging.debug(f'{v.name} {v.arguments} => {k}',should_format=False)
        logging.debug('}',indent=-1,should_format=False)

    def generate_file(self, indent_level: int = 0):
        logging.set_log_indent_level(indent_level)
        logging.info(f'Attempting to generate CustomASM ruleset file for ruleset "{self.name}" at "{self.path / 'rules.asm'}".')
        with open(self.path / 'rules.asm','w') as f:
            f.write(f'''#once
#bankdef rules {{ outp = 0 * 0b0
    #bits {self.min_addr}
}}

#ruledef rules {{
    nop => 0x00 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000
}}''')
        logging.info(f'CustomASM ruleset file for ruleset "{self.name}" has been generated.')

class Instruction:
    def __init__(self, name: str, function: Callable, arguments: dict[str,int]):
        self.name = name
        self.function = function
        self.function = function
        self.arguments = arguments

def load_rulesets():
    import importlib, pkgutil

    ruleset_args: list[str] = [param.name for param in inspect.signature(Ruleset.__init__).parameters.values() if param.name != 'self']

    logging.info('Loading rulesets...')

    for _, name, _ in pkgutil.iter_modules(__path__):
        logging.info(f'Attempting to load ruleset "{name}"...',indent=1)
        indent_level = logging.get_log_indent_level()
        logging.edit_log_indent_level(1)
        module = importlib.import_module(f'{__name__}.{name}')
        kwargs = {k: getattr(module,k.upper()) for k in ruleset_args}
        rulesets[name] = Ruleset(**kwargs)
        logging.info(f'Ruleset "{name}" successfully loaded.',indent=indent_level,set_indent=True)
        if TYPE_CHECKING: __all__.append(name)

    logging.info(f'Rulesets loaded!',indent=-1)
    logging.info(should_format=False)

rulesets = {}

__all__ = [
    'Ruleset',
    'Instruction',
    'load_rulesets'
    'rulesets'
]