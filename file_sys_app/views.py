from rest_framework import viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone

from build_manager.docker_util import compile_folder
from .models import File, Folder
from .serializers import FileSerializer, FolderSerializer, FolderTreeSerializer


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

    def perform_create(self, serializer):
        file = serializer.save(user=self.request.user)
        self.update_folder_saved(file.folder)

    def update_folder_saved(self, folder):
        while folder:
            folder.last_modified_at = timezone.now()
            folder.save(update_fields=['last_modified_at'])
            folder = folder.parent


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_filesystem(request):
    user = request.user
    root_folders = Folder.objects.filter(user=user, parent=None)
    serializer = FolderTreeSerializer(root_folders, many=True)
    return Response(serializer.data)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def build_folder(request, folder_id):
    try:  # Get folder by id
        folder = Folder.objects.get(id=folder_id, user=request.user)
    except Folder.DoesNotExist:  # Folder not found
        return Response({"error": "Folder not found or access denied."}, status=status.HTTP_404_NOT_FOUND)

    # Compile folder as project in container
    stdout, stderr, exec_file = compile_folder(folder)

    # Compilation failed, return errors
    if stderr and "error" in stderr.lower():
        return Response({
            "stdout": stdout,
            "stderr": stderr,
            "message": "Compilation failed."
        }, status=status.HTTP_400_BAD_REQUEST)

    # Update folder executable file
    folder.exec_file = exec_file
    folder.last_compiled_at = timezone.now()

    # Compilation successful, return results
    return Response({
        "stdout": stdout,
        "stderr": stderr,
        "message": "Compilation succeeded.",
    }, status=status.HTTP_200_OK)

