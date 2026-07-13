import sys, subprocess, os, pyperclip
from enum import Enum

class AssemblyOutputType(Enum):
    BOTH = 'Binary and Hex'
    BIN = 'Binary'
    HEX = 'Hexadecimal'

PATH = 'C:/Custom PATH Binaries/'

def assemble(output_type: AssemblyOutputType = AssemblyOutputType.BIN, assembly: str | None = None, input_file: str | None = None):
    delete_inp = False
    if input_file is None:
        if assembly is not None:
            with open(PATH+'input.customasmbuild','w') as f: f.write(assembly)
            input_file = PATH+'input.customasmbuild'
            delete_inp = True
        else:
            raise ValueError('If an input file is not provided, a string with assembly code must be.')
    elif assembly is not None:
        raise ValueError('If an input file is provided, `assembly` argument must be None.')
    
    subprocess.run([PATH+'customasm.exe', '-f', 'binstr', '-o', PATH+'build.customasmbuild', input_file], check=True, stdout=subprocess.PIPE)
    if delete_inp:os.remove(input_file)

    with open(PATH+'build.customasmbuild','r') as f: contents = f.read()
    os.remove(PATH+'build.customasmbuild')
    # edited = contents+('0'*(4096-len(contents)))

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

if __name__ == '__main__':
    
    output_type = AssemblyOutputType.BOTH
    copy = False
    save = False
    inp_file = None

    for i,argument in enumerate(sys.argv):
        if i == 0: continue

        if argument in ['-output-type=hex','-output-type=hexadecimal']:
            output_type = AssemblyOutputType.HEX
        elif argument in ['-output-type=bin','-output-type=binary']:
            output_type = AssemblyOutputType.BIN
        elif argument in ['-output-type=both','-output-type=hex,bin','-output-type=bin,hex']:
            output_type = AssemblyOutputType.BOTH

        elif argument == '-copy':
            copy = True
        elif argument == '-save':
            save = True
        
        elif argument.startswith('-file='):
            inp_file = argument.removeprefix('-file=')
        else:
            if sys.argv[i-1] == '-file=':
                inp_file = argument.removeprefix('-file=')
            else:
                raise ValueError(f'Unknown argument \'{sys.argv[i]}\'.')
        
    if inp_file == None: raise FileNotFoundError('No file was passed!')
    inp_file = inp_file.replace('\\','/')

    output = assemble(output_type,input_file=inp_file)
    if save:
        if output_type == AssemblyOutputType.BOTH:
            with open('assembled.custom_asm_bin','w') as f: f.write(output[0])
            print('Binary output saved as \'assembled.custom_asm_bin\'')
            with open('assembled.custom_asm_hex','w') as f: f.write(output[1])
            print('Hexadecimal output saved as \'assembled.custom_asm_hex\'')
        else:
            with open(f'assembled.custom_asm_{output_type.value[:3].lower()}','w') as f: f.write(output)
            print(f'{output_type.value} output saved as \'assembled.custom_asm_{output_type.value[:3].lower()}\'')
    
    if copy:
        if output_type == AssemblyOutputType.BOTH:
            pyperclip.copy(output[0])
            print('DLS ROM (Binary) copied to clipboard.')
            pyperclip.copy(output[1])
            print('DLS ROM (Hexadecimal) copied to clipboard.')
        else:
            pyperclip.copy(output)
            print(f'DLS ROM ({output_type.value}) copied to clipboard.')

__all__ = ['assemble','AssemblyOutputType']