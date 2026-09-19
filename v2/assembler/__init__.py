import sys, subprocess, os
from enum import Enum
from pathlib import Path

basePath = Path(__file__).resolve().parent
customasmPath = str(basePath / 'customasm.exe')
buildPath = str(basePath / 'build.customasmbuild')

class OutputType(Enum):
    BOTH = 'Binary and Hex'
    BIN = 'Binary'
    HEX = 'Hexadecimal'

def assemble(output_type: OutputType = OutputType.BIN, assembly: str | None = None, input_file: str | None = None, min_addr_unit: int = 64):
    delete_inp = False
    if input_file is None:
        if assembly is not None:
            with open('input.customasmbuild','w') as f: f.write(assembly)
            input_file = 'input.customasmbuild'
            delete_inp = True
        else:
            raise ValueError('If an input file is not provided, a string with assembly code must be.')
    elif assembly is not None:
        raise ValueError('If an input file is provided, `assembly` argument must be None.')

    customasmCommand = [
        customasmPath,
        '-f', 'binstr',
        '-o', buildPath,
        str(Path(input_file).resolve()),
    ]
    
    if sys.platform != 'win32': customasmCommand.insert(0,'wine')

    try:
        subprocess.run(customasmCommand, check=True, stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True)
    except Exception as e:
        os.remove(input_file)
        raise e

    if delete_inp: os.remove(input_file)

    with open(buildPath,'r') as f: contents = f.read()
    os.remove(buildPath)

    binary_out = '\n'.join(contents[i:i+min_addr_unit] for i in range(0, len(contents), min_addr_unit))
    if output_type == OutputType.BIN: return binary_out
    
    hex_out = []
    for line in binary_out.splitlines():
        s = hex(int(line,2)).removeprefix('0x').upper().zfill(min_addr_unit // 4)
        hex_out.append(' '.join(s[i:i+2] for i in range(0, len(s), 2)))
    hex_out = '\n'.join(hex_out)

    if output_type == OutputType.BOTH: return (binary_out, hex_out)
    return hex_out

if __name__ == '__main__':
    text = assemble(OutputType.HEX,None,sys.argv[1],int(sys.argv[0].removeprefix('-min_addr_unit=')))
    subprocess.run(['code','-'],input=text,text=True,shell=True)

__all__ = ['assemble','OutputType']