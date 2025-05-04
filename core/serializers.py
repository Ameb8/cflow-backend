from rest_framework import serializers
from .models import Folder, File

class CompileCCodeSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=5000)

class FolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Folder
        fields = ['id', 'user', 'folder_name', 'parent']

class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ['file_name', 'folder', 'created_at', 'last_modified_at']