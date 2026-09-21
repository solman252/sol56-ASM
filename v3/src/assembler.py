from src import *

import customasm

def assemble(program: str, assembly: str, ruleset: rulesets.Ruleset | None = None) -> tuple[str, str]:
    starting_indent = logging.get_log_indent_level()
    logging.info(f'Attempting to assemble program "{program}"...')

    if assembly == '': assembly = ' '

    #region Fetch Ruleset
    if ruleset is None:
        #region Automatic Fetch
        logging.warning(f'No ruleset provided, attempting to fetch from program...',indent=1)

        line1 = assembly.splitlines()[0]
        if line1.startswith('#include "rulesets/') and line1.endswith('.asm"') and line1.count('"') == 2 and line1.count('/') == 2:
            ruleset = line1.removeprefix('#include "rulesets/').removesuffix('.asm"')

            if ruleset in rulesets.rulesets:
                logging.info(f'Ruleset defined by program to be "{ruleset}".')
                ruleset = rulesets.rulesets[ruleset]
            else:
                logging.info(f'Ruleset defined by program to be "{ruleset}".',indent=1)
                logging.warning(f'Ruleset "{ruleset}" could not be found.')
                logging.edit_log_indent_level(-1)
                ruleset = None
                assembly = assembly.removeprefix(line1+'\n')
        #endregion Automatic Fetch

        #region Manual Fetch
        if ruleset is None:
            logging.warning('No valid ruleset was defined, and will need to be manually provided.')

            if len(rulesets.rulesets) == 0: logging.error('No valid rulesets exist!')

            logging.edit_log_indent_level(1)

            ruleset_options = {(str(i+1)): v for i,v in enumerate(rulesets.rulesets.values())}
            print(f'{logging.get_log_indent()}Please select a ruleset by number:\n{logging.get_log_indent()}  {f'\n{logging.get_log_indent()}  '.join(f'{i}: "{v.name}"' for i,v in ruleset_options.items())}\n{logging.get_log_indent()}> ',end='')
            clear_len = 0
            while ruleset is None:
                try: inp = input(f'\033[s')
                except KeyboardInterrupt: exit()
                if inp in ruleset_options:
                    ruleset = ruleset_options[inp]
                    logging.info(f'Ruleset "{ruleset.name}" was manually selected.',indent=-1)
                    assembly = f'#include "rulesets/{ruleset.name}.asm"\n{assembly}'
                else:
                    print(f'{logging.get_log_indent()}"{inp}" is not an option.'+(' '*(clear_len-len(inp))))
                    clear_len = len(inp)
                    print('\033[u',' '*clear_len,f'\033[{clear_len}D',sep='',end='')
        #endregion Manual Fetch
    #endregion Fetch Ruleset

    # Ensure ruleset file is up to date
    logging.info(should_format=False)
    ruleset.generate_file(starting_indent+1)
    logging.info(should_format=False)

    #region Assemble
    import subprocess

    try:
        bytecode_bin, bytecode_hex = customasm.assemble(
            output_type=customasm.OutputType.BOTH,
            assembly=assembly,
            min_addr_unit=ruleset.min_addr
        )
    except subprocess.CalledProcessError as e:
        from strip_ansi import strip_ansi
        with open(logging.ASSEMBLE_ERROR_LOG,'w') as f: f.write(strip_ansi(e.stderr).removesuffix('\n'))
        logging.error(f'The program could not be assembled, see "{logging.ASSEMBLE_ERROR_LOG}" for more details.')
    #endregion Assemble

    logging.info(f'Program "{program}" succesfully assembled.',set_indent=True)

    return bytecode_bin, bytecode_hex

__all__ = [
    'assemble'
]