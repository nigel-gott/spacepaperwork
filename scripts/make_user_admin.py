
from core.models import GooseUser, DiscordUser

def run(*args):
    if len(args) != 1:
        raise Exception("Only pass a single arg of the user's username")

    # Fetch all questions
    user = GooseUser.objects.get(username=args[0])
    user.is_staff = True
    user.is_admin = True
    user.is_superuser = True
    user.save()
    