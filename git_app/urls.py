from django.urls import path
from .views import list_github_repos

urlpatterns = [
    path('repos/', list_github_repos, name='list_github_repos'),
]