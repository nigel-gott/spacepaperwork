from django.contrib.auth import get_user_model


def run(*args):
    if len(args) != 1:
        raise Exception("Only pass a single arg of the user's username")

    User = get_user_model()  # noqa

    user = User.objects.get(username=args[0])
    print(f"Making {user} admin")
    user.is_staff = True
    user.is_superuser = True
    user.full_clean()
    user.save()
    user.refresh_from_db()
    print(user.is_staff)
