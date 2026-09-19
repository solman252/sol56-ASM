from main import *

RULES_FOLDER = PROGRAMS_FOLDER / 'rules'
RULESETS_FOLDER = BASE_PATH / 'rulesets'

class Ruleset:
    def __init__(self, name: str, min_addr: int):
        self.name = name
        self.min_addr = min_addr

    def generate_file(self):
        info(f'Attempting to generate CustomASM ruleset file for ruleset "{self.name}" at "{RULES_FOLDER / (self.name+'.asm')}".')
        with open(RULES_FOLDER / (self.name+'.asm'),'w') as f:
            f.write(f'''#once
#bankdef rules {{ outp = 0 * 0b0
    #bits {self.min_addr}
}}

#ruledef rules {{
    nop => 0x00 @ 0x0 @ 0x0 @ 0x0000 @ 0x0000
}}''')
        info(f'CustomASM ruleset file for ruleset "{self.name}" has been generated.')

rulesets = {
    'sol48': Ruleset('sol48',16)
}