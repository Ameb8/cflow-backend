from django.urls import path
from .views import list_github_repos, import_github_repo, RepoCreate

urlpatterns = [
    path('repos/', list_github_repos, name='list_github_repos'),
    # path('repos/import/', import_github_repo, name='import_github_repo'),
    path('repos/', RepoCreate.as_view()),

]