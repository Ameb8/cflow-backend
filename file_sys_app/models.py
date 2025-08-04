import os
import shutil
import tempfile
from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import List

from django.db import models
from django.conf import settings

class FileTreeObj(models.Model, ABC):
    name = models.CharField(max_length=60)
    hidden = models.BooleanField(default=False)

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='file_tree'
    )

    parent = models.ForeignKey(
        'Folder',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    last_modified_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True

    def __str__(self) -> str:
        return f"{self.fmt_name}/{self.get_path()}"

    @abstractmethod
    def fmt_name(self) -> str:
        pass

    @abstractmethod
    def write(self, base_path: str):
        pass

    def get_path(self) -> str:
        path: List[str] = ["/"]
        obj: FileTreeObj = self

        while obj is not None:
            path.append(f"{obj.fmt_name}/")
            obj = obj.parent

        return "".join(path)

    @contextmanager
    def as_temp_dir(self):
        """
        Context manager that writes this FileTreeObj (and its children)
        to a temporary folder, yields the path, then cleans it up after.
        """
        temp_dir = tempfile.mkdtemp(prefix=f"{self.name}_")

        try:
            self.write(temp_dir)
            yield os.path.join(temp_dir, self.fmt_name())
        finally:
            shutil.rmtree(temp_dir)



class Folder(FileTreeObj):
    exec_file = models.BinaryField(blank= True, null=True)
    last_compiled_at = models.DateTimeField(auto_now=False, blank=True, null=True)

    class Meta:
        unique_together = ('name', 'user', 'parent')

    def write_to_temp(self, base_path: str) -> None:
        # Create folder
        folder_path = os.path.join(base_path, self.fmt_name())
        os.makedirs(folder_path, exist_ok=True)

        # Write Children
        for child in self.children.all():
            child.write_to_temp(folder_path)


    def fmt_name(self) -> str:
        return self.name


class File(FileTreeObj):
    extension = models.CharField(max_length=10, null=True, blank=True)

    class Meta:
        abstract = True

    def fmt_name(self) -> str:
        return f"{self.name}.{self.extension}"

class TextFile(File):
    file_content = models.TextField(blank=True, null=True)

    def write(self, base_path: str):
        file_path = os.path.join(base_path, self.fmt_name())
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(self.file_content or "")

class BinFile(File):
    content = models.BinaryField()
    is_executable = models.BooleanField(default=False)

    def write(self, base_path: str):
        file_path = os.path.join(base_path, self.fmt_name())
        with open(file_path, "wb") as f:
            f.write(self.content or b"")

    class Meta:
        unique_together = ('folder', 'file_name', 'extension')



class FileChange(models.Model):
    file = models.ForeignKey(TextFile, on_delete=models.CASCADE, related_name='changes')
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

