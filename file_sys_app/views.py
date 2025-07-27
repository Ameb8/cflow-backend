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



@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_filesystem(request):
    user = request.user
    root_folders = Folder.objects.filter(user=user, parent=None)
    serializer = FolderTreeSerializer(root_folders, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_user_project(request, folder_id):
    user = request.user
    try:
        root_folder = Folder.objects.get(id=folder_id, user=user)
    except Folder.DoesNotExist:
        return Response({"error": "Folder not found."}, status=404)

    serializer = FolderTreeSerializer(root_folder)
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


# views.py
from .models import File, FileChange
from .serializers import FileChangeInputSerializer

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def apply_file_changes(request, file_id):
    try:
        file = File.objects.get(id=file_id, folder__user=request.user)
    except File.DoesNotExist:
        return Response({"error": "File not found or access denied."}, status=status.HTTP_404_NOT_FOUND)

    # Validate incoming list of changes
    serializer = FileChangeInputSerializer(data=request.data.get('changes', []), many=True)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    # Apply changes in order
    changes = serializer.validated_data
    content = file.file_content or ""

    for change in changes:
        pos = change['position']
        if change['change_type'] == 'insert': # Insert text
            text = change.get('text') or ''
            content = content[:pos] + text + content[pos:]
        elif change['change_type'] == 'delete': # Remove text
            length = change.get('length') or 0
            content = content[:pos] + content[pos + length:]

    # Save updated file content
    file.file_content = content
    file.save()

    return Response({
        "message": "File updated successfully.",
        "updated_content": content
    }, status=status.HTTP_200_OK)

