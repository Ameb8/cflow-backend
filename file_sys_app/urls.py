from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FolderViewSet, FileViewSet, get_user_filesystem, get_user_project, build_folder, apply_file_changes

router = DefaultRouter()
router.register(r'folders', FolderViewSet, basename='folder')
router.register(r'files', FileViewSet, basename='file')

urlpatterns = [
    path('filesystem/', get_user_filesystem, name='get_user_filesystem'),
    path('filesystem/<int:folder_id>/', get_user_project, name='get_user_project'),
    path('build-folder/<int:folder_id>', build_folder, name='build_folder'),
    path('files/<int:file_id>/apply-changes/', apply_file_changes, name='apply_file_changes'),
]

urlpatterns += router.urls
