"""Utility functions for the jobs app."""

from django.contrib.auth import get_user_model

User = get_user_model()


def get_marnie_email() -> str:
    """Return the email address for Marnie."""
    try:
        marnie = User.objects.get(is_marnie=True)
    except User.DoesNotExist as err:
        msg = "No Marnie user found."
        raise User.DoesNotExist(msg) from err
    except User.MultipleObjectsReturned as err:
        msg = "Multiple Marnie users found."
        raise User.MultipleObjectsReturned(msg) from err
    else:
        return marnie.email
