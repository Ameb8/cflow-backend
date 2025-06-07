# auth_app/urls.py
from django.urls import path, include

urlpatterns = [
    path('', include('allauth.urls')),  # for allauth routes like /accounts/login/, /accounts/logout/, /accounts/github/login/
]
