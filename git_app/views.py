from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
import requests

from allauth.socialaccount.models import SocialAccount, SocialToken
from .git_util import get_github_token

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def list_github_repos(request):
    user = request.user
    token = get_github_token(user)
    print(f"\n[DEBUG] Authenticated user: {user} (ID: {user.id})") # DEBUG ***

    if not token:
        print("[DEBUG] No GitHub token found for user.") # DEBUG ***
        return Response({"error": "GitHub token not found"}, status=400)

    headers = {
        "Authorization": f"token {token}",
        "Accept": "application/vnd.github+json"
    }

    # GitHub API to get user repos (owned and accessible)
    url = "https://api.github.com/user/repos"

    params = {
        "per_page": 100,  # max per page
        "sort": "updated"
    }

    try:
        r = requests.get(url, headers=headers, params=params)
        r.raise_for_status()
    except requests.RequestException as e:
        # return Response({"error": f"GitHub API error: {str(e)}"}, status=502)

        # DEBUG ******
        return Response({
            "error": f"GitHub API error: {str(e)}",
            "status_code": r.status_code,
            "github_response": r.text,
            "headers": dict(r.headers)
        }, status=r.status_code)
        # END DEBUG ***

    repos = r.json()
    # Optional: filter or format repos as needed
    # For example, return only name, full_name, private, html_url
    repo_list = [
        {
            "id": repo["id"],
            "name": repo["name"],
            "full_name": repo["full_name"],
            "private": repo["private"],
            "html_url": repo["html_url"],
            "description": repo.get("description"),
        }
        for repo in repos
    ]

    return Response(repo_list)
