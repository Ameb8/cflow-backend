from django.contrib.auth.hashers import make_password
from django.shortcuts import render
import subprocess
import tempfile
import os
import base64
import shutil
from rest_framework.response import Response
from rest_framework.decorators import api_view
from rest_framework import status, viewsets
from .serializers import CompileCCodeSerializer
from django.conf import settings
from django.contrib.auth.forms import UserCreationForm
from django.shortcuts import render, redirect
from django.contrib.auth import login, logout, authenticate
from django.http import JsonResponse
from django.contrib.auth.models import User
from django.contrib.auth import views as auth_views
from django.views.decorators.csrf import ensure_csrf_cookie
from core.asm_parsing.filter_asm import filter_asm
from core.asm_parsing.mapper import map_asm

from .models import Folder, File
from .serializers import FolderSerializer, FileSerializer



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
                    "gcc", "-Wall",  "-S", "/home/source.c", "-o", "/tmp/source.s"
                ]
                compile_proc = subprocess.run(compile_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
                compile_warnings = compile_proc.stderr.decode()

                # Compile with debug info
                compile_dbg_cmd = [
                    "docker", "exec", "--user", "nobody", container_name,
                    "gcc", "-g", "-S", "/home/source.c", "-o", "/tmp/source_dbg.s"
                ]
                subprocess.run(compile_dbg_cmd, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)

                # Copy result file back to host
                asm_path = os.path.join(tempdir, "source.s")
                asm_dbg_path = os.path.join(tempdir, "source_dbg.s")
                pre_path = os.path.join(tempdir, "source.i")
                subprocess.run(["docker", "cp", f"{container_name}:/tmp/source.s", asm_path], check=True)
                subprocess.run(["docker", "cp", f"{container_name}:/tmp/source_dbg.s", asm_dbg_path], check=True)
                subprocess.run(["docker", "cp", f"{container_name}:/tmp/source.i", pre_path], check=True)

                # Filter and map asm to C
                filter_asm(asm_path)
                asm_line_mapping = map_asm(asm_dbg_path, asm_path)

                # Read and return the result
                with open(asm_path, 'r') as asm_file:
                    asm_contents = asm_file.read()
                with open(asm_dbg_path, 'r') as asm_dbg_file:
                    asm_dbg_contents = asm_dbg_file.read()
                with open(pre_path, 'r') as pre_file:
                    pre_contents = pre_file.read()

                return Response({
                    'assembly': asm_contents,
                    'asm_dbg': asm_dbg_contents,
                    'preprocessed': pre_contents,
                    'line_mapping': asm_line_mapping,
                    'warnings': compile_warnings
                })


            except subprocess.CalledProcessError as e:
                return Response({
                    "error": "Compilation failed.",
                    "stderr": e.stderr.decode() if e.stderr else str(e)
                }, status=status.HTTP_400_BAD_REQUEST)

            finally:
                subprocess.run(["docker", "rm", "-f", container_name], stdout=subprocess.DEVNULL)

    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
def register(request):
    username = request.data.get('username')
    password = request.data.get('password')
    password2 = request.data.get('password2')

    if not username or not password:
        return Response({"error": "Username and password are required"}, status=status.HTTP_400_BAD_REQUEST)

    # Check if the password matches the confirmation
    if password != password2:
        return Response({"error": "Passwords do not match"}, status=status.HTTP_400_BAD_REQUEST)

    # Check if user already exists
    if User.objects.filter(username=username).exists():
        return Response({"error": "Username already exists"}, status=status.HTTP_400_BAD_REQUEST)

    # Create the user
    user = User.objects.create(
        username=username,
        password=make_password(password),  # Hash password
    )
    login(request, user)  # Log the user in

    return Response({"message": "User registered and logged in successfully"}, status=status.HTTP_201_CREATED)


@api_view(['POST'])
def custom_login(request):
    username = request.data.get('username')
    password = request.data.get('password')

    # Authenticate the user
    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        return JsonResponse({"message": "Login successful"})
    else:
        return JsonResponse({"error": "Invalid credentials"}, status=400)


@api_view(['POST'])
def custom_logout(request):
    if request.user.is_authenticated:
        logout(request)
        return JsonResponse({"message": "Logged out successfully"})
    else:
        return JsonResponse({"error": "User is not logged in"}, status=400)

@ensure_csrf_cookie
def get_csrf_token(request):
    return JsonResponse({'message': 'CSRF cookie set'})


class FolderViewSet(viewsets.ModelViewSet):
    queryset = Folder.objects.all()
    serializer_class = FolderSerializer

class FileViewSet(viewsets.ModelViewSet):
    queryset = File.objects.all()
    serializer_class = FileSerializer