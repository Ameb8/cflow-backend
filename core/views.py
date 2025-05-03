from django.shortcuts import render
import subprocess
import tempfile
import os
import base64
import shutil
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from .serializers import CompileCCodeSerializer
from django.conf import settings



@api_view(['POST'])
def compile_c_code(request):
    serializer = CompileCCodeSerializer(data=request.data)
    if serializer.is_valid():
        code = serializer.validated_data['code']

        with tempfile.TemporaryDirectory() as tempdir:
            code_path = os.path.join(tempdir, "source.c")
            with open(code_path, "w") as f:
                f.write(code)

            container_name = "c_compile_" + next(tempfile._get_candidate_names())

            try:
                # Start container in background
                subprocess.run([
                    "docker", "run", "-d", "--rm",
                    "--name", container_name,
                    "--cpus=0.5", "--memory=256m", "--pids-limit=64",
                    "--network", "none",
                    "gcc:latest", "sleep", "30"
                ], check=True)

                # Copy code file into container
                subprocess.run(["docker", "cp", code_path, f"{container_name}:/home/source.c"], check=True)

                # Run preprocessing
                preprocess_cmd = [
                    "docker", "exec", "--user", "nobody", container_name,
                    "gcc", "-E", "/home/source.c", "-o", "/tmp/source.i"
                ]
                subprocess.run(preprocess_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                # Compile the code inside container as non-root
                compile_cmd = [
                    "docker", "exec", "--user", "nobody", container_name,
                    "gcc", "-g", "-ggdb", "/home/source.c", "-o", "/tmp/source.o"
                ]
                subprocess.run(compile_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                # Use objdump to extract assembly with line numbers from the object file
                objdump_cmd = [
                    "docker", "exec", "--user", "nobody", container_name,
                    "objdump", "-d", "--line-numbers", "/tmp/source.o"
                ]
                objdump_output = subprocess.run(objdump_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                # Copy result file back to host
               # asm_path = os.path.join(tempdir, "source.s")

                pre_path = os.path.join(tempdir, "source.i")
                #subprocess.run(["docker", "cp", f"{container_name}:/tmp/source.s", asm_path], check=True)
                subprocess.run(["docker", "cp", f"{container_name}:/tmp/source.i", pre_path], check=True)

                # Read and return the result
                #with open(asm_path, 'r') as asm_file:
                    #asm_contents = asm_file.read()

                # Convert object dump to asm
                asm_contents = objdump_output.stdout.decode()

                with open(pre_path, 'r') as pre_file:
                    pre_contents = pre_file.read()

                asm_line_mapping = parse_asm_lines(asm_contents)
                objdump_line_mapping = parse_objdump_lines(objdump_output.stdout.decode())
                combined_line_mapping = asm_line_mapping + objdump_line_mapping

                return Response({
                    'assembly': asm_contents,
                    'preprocessed': pre_contents,
                    'line_mapping': combined_line_mapping
                })


            except subprocess.CalledProcessError as e:
                return Response({
                    "error": "Compilation failed.",
                    "stderr": e.stderr.decode() if e.stderr else str(e)
                }, status=status.HTTP_400_BAD_REQUEST)

            finally:
                subprocess.run(["docker", "rm", "-f", container_name], stdout=subprocess.DEVNULL)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def parse_asm_lines(asm_contents):
    line_mapping = []
    current_line = None

    for line in asm_contents.splitlines():
        # Look for lines with line number info
        if line.startswith(".line"):
            parts = line.split()
            if len(parts) > 1:
                current_line = int(parts[1])
        elif current_line is not None:
            # Store the mapping of C line -> ASM line
            line_mapping.append({'c_line': current_line, 'asm_line': line.strip()})

    return line_mapping

def parse_objdump_lines(objdump_contents):
    line_mapping = []
    current_c_line = None
    current_asm_line = None

    for line in objdump_contents.splitlines():
        # Look for lines with C line information
        if line.startswith("   "):  # This is an instruction line
            parts = line.split()
            if len(parts) > 3 and parts[2] == '0x':
                current_asm_line = parts[0]  # The address of the instruction

        if line.startswith("   "):  # This is a line mapping
            parts = line.split()
            if len(parts) > 5 and parts[5].startswith(".L"):
                current_c_line = int(parts[5][1:])  # Line numbers in source code
                if current_c_line and current_asm_line:
                    line_mapping.append({'c_line': current_c_line, 'asm_line': current_asm_line})

    return line_mapping



'''
from django.shortcuts import render
import subprocess
import tempfile
import os
import base64
import shutil
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from .serializers import CompileCCodeSerializer
from django.conf import settings



@api_view(['POST'])
def compile_c_code(request):
    serializer = CompileCCodeSerializer(data=request.data)
    if serializer.is_valid():
        code = serializer.validated_data['code']

        with tempfile.TemporaryDirectory() as tempdir:
            code_path = os.path.join(tempdir, "source.c")
            with open(code_path, "w") as f:
                f.write(code)

            container_name = "c_compile_" + next(tempfile._get_candidate_names())

            try:
                # Start container in background
                subprocess.run([
                    "docker", "run", "-d", "--rm",
                    "--name", container_name,
                    "--cpus=0.5", "--memory=256m", "--pids-limit=64",
                    "--network", "none",
                    "gcc:latest", "sleep", "30"
                ], check=True)

                # Copy code file into container
                subprocess.run(["docker", "cp", code_path, f"{container_name}:/home/source.c"], check=True)

                # Run preprocessing
                preprocess_cmd = [
                    "docker", "exec", "--user", "nobody", container_name,
                    "gcc", "-E", "/home/source.c", "-o", "/tmp/source.i"
                ]
                subprocess.run(preprocess_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                # Compile the code inside container as non-root
                compile_cmd = [
                    "docker", "exec", "--user", "nobody", container_name,
                    "gcc", "-S", "/home/source.c", "-o", "/tmp/source.s"
                ]
                subprocess.run(compile_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                # Copy result file back to host
                asm_path = os.path.join(tempdir, "source.s")
                pre_path = os.path.join(tempdir, "source.i")
                subprocess.run(["docker", "cp", f"{container_name}:/tmp/source.s", asm_path], check=True)
                subprocess.run(["docker", "cp", f"{container_name}:/tmp/source.i", pre_path], check=True)

                # Read and return the result
                with open(asm_path, 'r') as asm_file:
                    asm_contents = asm_file.read()

                with open(pre_path, 'r') as pre_file:
                    pre_contents = pre_file.read()

                asm_line_mapping = parse_asm_lines(asm_contents)

                return Response({
                    'assembly': asm_contents,
                    'preprocessed': pre_contents,
                    'line_mapping': asm_line_mapping
                })


            except subprocess.CalledProcessError as e:
                return Response({
                    "error": "Compilation failed.",
                    "stderr": e.stderr.decode() if e.stderr else str(e)
                }, status=status.HTTP_400_BAD_REQUEST)

            finally:
                subprocess.run(["docker", "rm", "-f", container_name], stdout=subprocess.DEVNULL)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

def parse_asm_lines(asm_contents):
    line_mapping = []
    current_line = None

    for line in asm_contents.splitlines():
        # Look for lines with line number info
        if line.startswith(".line"):
            parts = line.split()
            if len(parts) > 1:
                current_line = int(parts[1])
        elif current_line is not None:
            # Store the mapping of C line -> ASM line
            line_mapping.append({'c_line': current_line, 'asm_line': line.strip()})

    return line_mapping



'''