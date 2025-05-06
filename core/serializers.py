from rest_framework import serializers
from .models import Folder, File

class CompileCCodeSerializer(serializers.Serializer):
    code = serializers.CharField(max_length=5000)

class FolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Folder
        fields = ['id', 'user', 'folder_name', 'parent']
        read_only_fields = ['user']

class FileSerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ['id', 'file_name', 'folder', 'created_at', 'last_modified_at', 'extension', 'file_content']

class FileNameOnlySerializer(serializers.ModelSerializer):
    class Meta:
        model = File
        fields = ['id', 'file_name', 'extension']

class FolderTreeSerializer(serializers.ModelSerializer):
    subfolders = serializers.SerializerMethodField()
    files = FileNameOnlySerializer(many=True)

    class Meta:
        model = Folder
        fields = ['id', 'folder_name', 'subfolders', 'files']

    def get_subfolders(self, obj):
        return FolderTreeSerializer(obj.subfolders.all(), many=True).data