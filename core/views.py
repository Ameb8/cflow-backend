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

                return Response({
                    'assembly': asm_contents,
                    'preprocessed': pre_contents
                })


            except subprocess.CalledProcessError as e:
                return Response({
                    "error": "Compilation failed.",
                    "stderr": e.stderr.decode() if e.stderr else str(e)
                }, status=status.HTTP_400_BAD_REQUEST)

            finally:
                subprocess.run(["docker", "rm", "-f", container_name], stdout=subprocess.DEVNULL)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


