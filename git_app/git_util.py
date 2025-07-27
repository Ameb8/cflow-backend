from allauth.socialaccount.models import SocialToken, SocialAccount

def get_github_token(user):
    try:
        account = SocialAccount.objects.get(user=user, provider='github')
        token = SocialToken.objects.get(account=account)
        return token.token
    except (SocialAccount.DoesNotExist, SocialToken.DoesNotExist):
        return None