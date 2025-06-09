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
