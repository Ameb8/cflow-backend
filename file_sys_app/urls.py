from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import FolderViewSet, FileViewSet, get_user_filesystem

router = DefaultRouter()
router.register(r'folders', FolderViewSet, basename='folder')
router.register(r'files', FileViewSet, basename='file')

urlpatterns = [
    path('filesystem/', get_user_filesystem, name='get_user_filesystem'),
]

urlpatterns += router.urls
