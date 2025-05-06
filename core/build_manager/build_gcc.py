import subprocess
import os
from core.asm_parsing.filter_asm import filter_asm
from core.asm_parsing.mapper import map_asm

def generate_gcc_output_file(container_name, gcc_args, container_output_path, host_output_path):
    # Build and run command inside container
    cmd = ["docker", "exec", "--user", "nobody", container_name, "gcc"] + gcc_args + ["-o", container_output_path]
    result = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, check=True)

    # Copy result from container to host
    subprocess.run(["docker", "cp", f"{container_name}:{container_output_path}", host_output_path], check=True)

    return host_output_path, result.stderr.decode()

def read_file(file_path):
    with open(file_path, 'r') as file:
        return file.read()

def get_asm(container_name, tempdir):
    # Compile ASM and get compiler warnings
    asm_path, compile_warnings = generate_gcc_output_file(
        container_name,
        gcc_args=["-Wall", "-S", "/home/source.c"],
        container_output_path="/tmp/source.s",
        host_output_path=os.path.join(tempdir, "source.s")
    )

    # Get path to ASM file with debug metadata
    asm_dbg_path, _ = generate_gcc_output_file(
        container_name,
        gcc_args=["-g", "-S", "/home/source.c"],
        container_output_path="/tmp/source_dbg.s",
        host_output_path=os.path.join(tempdir, "source_dbg.s")
    )

    # Filter and map asm to C
    filter_asm(asm_path)
    asm_line_mapping = map_asm(asm_dbg_path, asm_path)

    return read_file(asm_path), asm_line_mapping, compile_warnings

def get_preprocessed(container_name, tempdir):
    pre_path, _ = generate_gcc_output_file(
        container_name,
        gcc_args=["-E", "/home/source.c"],
        container_output_path="/tmp/source.i",
        host_output_path=os.path.join(tempdir, "source.io")
    )

