from django.contrib.auth.hashers import make_password
from django.shortcuts import render
import subprocess
import tempfile
import os
import base64
import shutil
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view, permission_classes
from rest_framework import status, viewsets

from .build_manager.build_gcc import get_preprocessed, get_asm
from .build_manager.docker_util import to_docker, start_docker, clean_docker
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
from core.build_manager import build_gcc, docker_util

from .models import Folder, File
from .serializers import FolderSerializer, FileSerializer, FolderTreeSerializer

@api_view(['POST'])
def compile_c_code(request):
    serializer = CompileCCodeSerializer(data=request.data)

    if serializer.is_valid(): # Get user input code
        code = serializer.validated_data['code']

        # Create temporary file
        with tempfile.TemporaryDirectory() as tempdir:
            code_path = os.path.join(tempdir, "source.c")

            # Write user input code to file
            with open(code_path, "w") as f:
                f.write(code)

            container_name = "c_compile_" + next(tempfile._get_candidate_names())

            try:
                # Start docker and move C file
                start_docker(container_name)
                to_docker(container_name, code_path, "/home/source.c")

                # Generate files to return
                preprocessed = get_preprocessed(container_name, tempdir)
                asm, line_mapping, compile_warnings = get_asm(container_name, tempdir)

                return Response({
                    'assembly': asm,
                    'preprocessed': preprocessed,
                    'line_mapping': line_mapping,
                    'warnings': compile_warnings
                })

            # Return error info if compilation fails
            except subprocess.CalledProcessError as e:
                return Response({
                    "error": "Compilation failed.",
                    "stderr": e.stderr.decode() if e.stderr else str(e)
                }, status=status.HTTP_400_BAD_REQUEST)

            finally: # Remove files from container
                clean_docker(container_name)

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
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)

class FileViewSet(viewsets.ModelViewSet):
    queryset = File.objects.all()
    serializer_class = FileSerializer
    permission_classes = [IsAuthenticated]

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_filesystem(request):
    user = request.user
    root_folders = Folder.objects.filter(user=user, parent=None)
    serializer = FolderTreeSerializer(root_folders, many=True)
    return Response(serializer.data)