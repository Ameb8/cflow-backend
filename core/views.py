from django.shortcuts import render
import subprocess
import tempfile
import os
import base64
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from .serializers import CompileCCodeSerializer


@api_view(['POST'])
def compile_c_code(request):
    # Deserialize the request data
    serializer = CompileCCodeSerializer(data=request.data)
    if serializer.is_valid():
        code = serializer.validated_data['code']

        # Create a temporary directory to store the C code and output files
        with tempfile.TemporaryDirectory() as tempdir:
            # Write the C code to a temporary C file
            code_path = os.path.join(tempdir, "source.c")
            with open(code_path, "w") as f:
                f.write(code)

            # Run the Docker container to compile the C code
            try:
                compile_command = [
                    'docker', 'run', '--rm',
                    '-v', f'{tempdir}:/usr/src/app',
                    'gcc:latest',
                    'gcc', '/usr/src/app/source.c', '-o', '/usr/src/app/output.o', '-S'
                ]
                subprocess.run(compile_command, check=True)

                # Return the paths to the compiled files
                object_file_path = os.path.join(tempdir, "output.o")
                asm_file_path = os.path.join(tempdir, "source.s")

                if os.path.exists(object_file_path) and os.path.exists(asm_file_path):
                    # Read assembly file as plain text
                    with open(asm_file_path, 'r') as asm_file:
                        asm_contents = asm_file.read()

                    # Read object file as binary and encode to base64
                    with open(object_file_path, 'rb') as obj_file:
                        obj_bytes = obj_file.read()
                        obj_b64 = base64.b64encode(obj_bytes).decode('utf-8')

                    return Response({
                        'assembly': asm_contents,
                        'object_file_base64': obj_b64
                    })
                else:
                    return Response({"error": "Compilation failed."}, status=status.HTTP_400_BAD_REQUEST)
            except subprocess.CalledProcessError as e:
                return Response({"error": "Error during compilation."}, status=status.HTTP_400_BAD_REQUEST)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
