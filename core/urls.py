from django.urls import path, include
from django.contrib import admin
from django.contrib.auth import views as auth_views
from rest_framework.routers import DefaultRouter
from .views import FolderViewSet, FileViewSet
from . import views

router = DefaultRouter()
router.register(r'folders', FolderViewSet)
router.register(r'files', FileViewSet)

urlpatterns = [
    path('compile/', views.compile_c_code, name='compile_c_code'),
    path('admin/', admin.site.urls),
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('register/', views.register, name='register'),
    path('csrf/', views.get_csrf_token, name='get_csrf_token'),
] + router.urls
