from src import *

def main():
    #region Init Submodules
    paths.generate_folders()
    logging.init()
    rulesets.load_rulesets()
    #endregion Init Submodules

    #region Argument Parsing
    import argparse

    arg_parser = argparse.ArgumentParser(formatter_class=argparse.MetavarTypeHelpFormatter)
    arg_parser.add_argument(
        '-p', '--program',
        default = str(paths.PROGRAMS / 'test.asm'),
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

    if args.program is None: logging.error(f'No program has been provided!')
    #endregion Argument Parsing

    try:
        with open(args.program,'r') as f: program = f.read()
    except FileNotFoundError:
        logging.error(f'Program "{args.program}" does not exist!')
    bytecode_bin, bytecode_hex = assembler.assemble(args.program,program)

if __name__ == '__main__': main()