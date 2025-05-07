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
    path('login/', views.custom_login, name='login'),
    path('logout/', views.custom_logout, name='logout'),
    path('register/', views.register, name='register'),
    path('csrf/', views.get_csrf_token, name='get_csrf_token'),
    path('filesystem/', views.get_user_filesystem, name='get_user_filesystem'),
    path('auth/', include('dj_rest_auth.urls')),
    path('auth/registration/', include('dj_rest_auth.registration.urls')),
    path('auth/user/', views.current_user),

] + router.urls
