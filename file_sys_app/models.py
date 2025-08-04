from typing import List

from django.db import models
from django.conf import settings


class Folder(models.Model):
    folder_name = models.CharField(max_length=60)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='folders'
    )

    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='subfolders'
    )

    exec_file = models.BinaryField(blank= True, null=True)
    last_modified_at = models.DateTimeField(auto_now=True)
    last_compiled_at = models.DateTimeField(auto_now=False, blank=True, null=True)

    class Meta:
        unique_together = ('folder_name', 'user', 'parent')

    def __str__(self) -> str:
        path: List[str] = []
        folder: Folder = self

        while folder is not None:
            path.append(folder.folder_name)
            folder = folder.parent

        return "/".join(reversed(path)) + "/"


class File(models.Model):
    file_name = models.CharField(max_length=60)
    folder = models.ForeignKey(
        Folder,
        on_delete=models.CASCADE,
        related_name='files'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    last_modified_at = models.DateTimeField(auto_now=True)
    extension = models.CharField(max_length=10, null=True, blank=True)
    file_content = models.TextField(blank=True, null=True)

    class Meta:
        unique_together = ('folder', 'file_name', 'extension')

    def __str__(self) -> str:
        return f"{str(self.folder)}{self.file_name}.{self.extension}"



class BinFile(models.Model):
    file_name = models.CharField(max_length=255)
    folder = models.ForeignKey(
        'Folder',
        on_delete=models.CASCADE,
        related_name='bin_files'
    )
    content = models.BinaryField()
    created_at = models.DateTimeField(auto_now_add=True)
    last_modified_at = models.DateTimeField(auto_now=True)

    extension = models.CharField(max_length=15, null=True, blank=True)
    is_executable = models.BooleanField(default=False)
    is_symlink = models.BooleanField(default=False)
    symlink_target = models.CharField(max_length=500, null=True, blank=True)

    class Meta:
        unique_together = ('folder', 'file_name', 'extension')
        indexes = [
            models.Index(fields=['folder', 'file_name']),
        ]

    def __str__(self):
        return f"{self.folder}/{self.file_name}"

class FileChange(models.Model):
    file = models.ForeignKey(File, on_delete=models.CASCADE, related_name='changes')
    created_at = models.DateTimeField(auto_now_add=True)

    change_type = models.CharField(max_length=10, choices=[
        ('insert', 'Insert'),
        ('delete', 'Delete'),
    ])

    position = models.IntegerField()
    text = models.TextField(blank=True, null=True)
    length = models.IntegerField(null=True, blank=True)

    class Meta:
        ordering = ['created_at']