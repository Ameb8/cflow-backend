from rest_framework import serializers
from .models import Folder, File

class FolderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Folder
        fields = ['id', 'user', 'folder_name', 'parent']
        read_only_fields = ['user']
        exclude = ['exec_file, last_modified_at', 'last_compiled_at']

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

class FileChangeInputSerializer(serializers.Serializer):
    change_type = serializers.ChoiceField(choices=['insert', 'delete'])
    position = serializers.IntegerField()
    text = serializers.CharField(required=False, allow_blank=True, allow_null=True)
    length = serializers.IntegerField(required=False, allow_null=True)

