from django.shortcuts import render
import subprocess
import tempfile
import os
import base64
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status
from .serializers import CompileCCodeSerializer
from django.conf import settings


@api_view(['POST'])
def compile_c_code(request):
    # Deserialize the request data
    serializer = CompileCCodeSerializer(data=request.data)
    if serializer.is_valid():
        code = serializer.validated_data['code']

        tempdir = os.path.join(settings.BASE_DIR, 'tempcode', 'testsession')
        os.makedirs(tempdir, exist_ok=True)
        code_path = os.path.join(tempdir, "source.c")

        # Create a temporary directory to store the C code and output files
        with open(code_path, "w") as f:
            f.write(code)

        # DEBUG
        print(f"Tempdir: {tempdir}")
        # END DEBUG

        # Run the Docker container to compile the C code
        try:
            compile_command = [
                'docker', 'run', '--rm',
                '-v', f'{tempdir}:/usr/src/app',
                'gcc:latest',
                'gcc', '-S', '/usr/src/app/source.c', '-o', '/usr/src/app/source.s'
            ]
            result = subprocess.run(compile_command, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

            # DEBUG
            print(result.stdout.decode())
            print(result.stderr.decode())
            # END DEBUG

            # Return the paths to the compiled files
            #object_file_path = os.path.join(tempdir, "output.o")
            asm_file_path = os.path.join(tempdir, "source.s")

            if os.path.exists(asm_file_path):
                with open(asm_file_path, 'r') as asm_file:
                    asm_contents = asm_file.read()

                return Response({
                    'assembly': asm_contents
                })
            else:
                return Response({"error": "Compilation failed."}, status=status.HTTP_400_BAD_REQUEST)
        except subprocess.CalledProcessError as e:

            # DEBUG
            print("Docker STDOUT:", e.stdout.decode())
            print("Docker STDERR:", e.stderr.decode())
            # END DEBUG

            return Response({"error": "Error during compilation."}, status=status.HTTP_400_BAD_REQUEST)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
