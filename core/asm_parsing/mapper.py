import re

def map_asm(asm_dbg_path, asm_pure_path):
    """
    Maps lines in C code to ASM file

    Parameters:
        asm_dbg_path (str): Path to assembly file with debug metadata (.txt file)
        asm_pure_path (str): Path to pure assembly file (.txt file)
    Returns:
        dict: A dictionary mapping C line numbers to assembly line numbers
              Entries: {C line number, [list of ASM line numbers]}
    """
    line_mappings = {} # return dict
    lines = []  # List of (C_line_num, asm_lines)

    # Extract assembly instructions and corresponding C line number
    with open(asm_dbg_path, 'r') as file:
        current_c_line = None
        current_asm_block = []

        for line in file:
            if '.loc' in line: #and line.startswith('.loc'): # Line contains C line number and file
                #print(f'Line num label found:\n{line}') # DEBUG ***
                tokens = line.split()
                if tokens[1] == '1': # User submitted source file
                    if current_c_line is not None and current_asm_block:
                        lines.append((current_c_line, current_asm_block))
                    current_c_line = int(tokens[2])
                    current_asm_block = []
                continue

            if any(unwanted in line for unwanted in ['.cfi', '.L', '.size', '.ident', '.section', '.file', '.type', '.globl', '.long', '.value', '.byte', '.uleb', '.string', '.quad']):
                continue

            if line.strip():
                current_asm_block.append(line.strip())

        if current_c_line is not None and current_asm_block:
            lines.append((current_c_line, current_asm_block))

    #print(f'lines with numbers:\n{lines}') # DEBUG ***

    # Read pure_asm into memory as lines
    with open(asm_pure_path, 'r') as file:
        asm_pure_lines = [line.strip() for line in file if line.strip()]

    # Match C mapped asm instructions to asm_pure line numbers
    for c_line, asm_block in lines:
        found = False
        block_len = len(asm_block)
        matched_line_nums = []

        for i in range(len(asm_pure_lines) - block_len + 1):
            if asm_pure_lines[i:i + block_len] == asm_block:
                matched_line_nums.append(i)

        if matched_line_nums:
            if c_line not in line_mappings:
                line_mappings[c_line] = []
            line_mappings[c_line].extend(matched_line_nums)
        else:
            print(f"Block for C line {c_line} not found in pure ASM.")

    return line_mappings

def test_map_asm():
    asm_pure_path = '/Users/pattycrowder/cflow_test/line_map_test/basic_math.s'
    asm_dbg_path = '/Users/pattycrowder/cflow_test/line_map_test/basic_math_dbg.s'
    print(map_asm(asm_dbg_path, asm_pure_path))

