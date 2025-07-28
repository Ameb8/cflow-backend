from allauth.socialaccount.models import SocialToken, SocialAccount

def get_github_token(user):
    try:
        account = SocialAccount.objects.get(user=user, provider='github')
        token = SocialToken.objects.get(account=account)

        # DEBUG *******
        print(f"\n\nAccount: {account}")
        print(f"Token: {token}\n\n")
        # END DEBUG ***

        return token.token
    except (SocialAccount.DoesNotExist, SocialToken.DoesNotExist):
        return None