import sys, subprocess, os
from enum import Enum

class AssemblyOutputType(Enum):
    BOTH = 'Binary and Hex'
    BIN = 'Binary'
    HEX = 'Hexadecimal'

def assemble(output_type: AssemblyOutputType = AssemblyOutputType.BIN, assembly: str | None = None, input_file: str | None = None):
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
    
    if sys.platform == 'win32':
        subprocess.run(['customasm.exe', '-f', 'binstr', '-o', 'build.customasmbuild', input_file], check=True, stdout=subprocess.PIPE)
    else:
        subprocess.run(['wine', 'customasm.exe', '-f', 'binstr', '-o', 'build.customasmbuild', input_file], check=True, stdout=subprocess.PIPE)

    if delete_inp:os.remove(input_file)

    with open('build.customasmbuild','r') as f: contents = f.read()
    os.remove('build.customasmbuild')

    binary_out = '\n'.join(contents[i:i+56] for i in range(0, len(contents), 56))
    if output_type == AssemblyOutputType.BIN:
        return binary_out
    
    hex_out = []
    for line in binary_out.splitlines():
        s = hex(int(line,2)).removeprefix('0x').upper()
        s = ('0'*(4-len(s))) + s

        hex_out.append(s[0:2]+' '+s[2:4])
    hex_out = '\n'.join(hex_out)

    if output_type == AssemblyOutputType.BOTH: return (binary_out, hex_out)
    return hex_out

__all__ = ['assemble','AssemblyOutputType']