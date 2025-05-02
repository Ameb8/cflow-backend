from django.urls import path
from . import views

urlpatterns = [
    path('compile/', views.compile_c_code, name='compile_c_code'),
]
