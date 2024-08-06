"""View for the home page of the application."""

from django.http import HttpRequest
from django.http import HttpResponse
from django.shortcuts import render
from zen_queries import fetch

from manies_maintenance_manager.jobs.utils import user_has_verified_email_address
from manies_maintenance_manager.users.models import User

USER_COUNT_PROBLEM_MESSAGES = {
    "NO_ADMIN_USERS": "WARNING: There are no Admin users.",
    "MANY_ADMIN_USERS": "WARNING: There are multiple Admin users.",
    "NO_MANIE_USERS": "WARNING: There are no Manie users.",
    "MANY_MANIE_USERS": "WARNING: There are multiple Manie users.",
    "NO_AGENT_USERS": "WARNING: There are no Agent users.",
}


def home_page(request: HttpRequest) -> HttpResponse:
    """Render the home page for the application.

    Args:
        request (HttpRequest): The HTTP request.

    Returns:
        HttpResponse: The HTTP response.
    """
    context = {
        "userinfo": UserInfo(),
        "warnings": USER_COUNT_PROBLEM_MESSAGES,
    }
    return render(request, "pages/home.html", context)


def _user_has_primary_email_address(user: User) -> bool:
    """Check if the user has a primary email address.

    Args:
        user (User): The user.

    Returns:
        bool: True if the user has a primary email address, False otherwise.
    """
    return any(
        emailaddress.primary
        for emailaddress in user.emailaddress_set.all()  # type: ignore[attr-defined]
    )


class UserInfo:
    """Class to efficiently provide information about the users to Templates.

    One reason we use this is to avoid a very large amount of user-related querying
    when rendering the home page jor users. Instead, we instantiate this object once
    pass it as a template context variable to the home page view, and in there
    it uses its internal cache or calculates details without repeatedly querying
    the db in a horrible set of N+1 patterns.
    """

    def __init__(self) -> None:
        """Initialize the UserInfo object."""
        self._cached_users = fetch(
            User.objects.all().prefetch_related(
                "emailaddress_set",
            ),
        )
        self._user_emails = {
            user.id: list(user.emailaddress_set.all()) for user in self._cached_users
        }

    def count_admin_users(self) -> int:
        """Return the number of superuser users.

        Returns:
            int: The number of superuser users.
        """
        return sum(user.is_superuser for user in self._cached_users)

    def count_manie_users(self) -> int:
        """Return the number of Manie users.

        Returns:
            int: The number of Manie users.
        """
        return sum(user.is_manie for user in self._cached_users)

    def count_agent_users(self) -> int:
        """Return the number of Agent users.

        Returns:
            int: The number of Agent users.
        """
        return sum(user.is_agent for user in self._cached_users)

    def has_no_admin_users(self) -> bool:
        """Check if there are no superuser users.

        Returns:
            bool: True if there is no superuser, False otherwise.
        """
        return self.count_admin_users() == 0

    def has_many_admin_users(self) -> bool:
        """Check if there are more than one superusers.

        Returns:
            bool: True if there is more than one superuser, False otherwise.
        """
        return self.count_admin_users() > 1

    def has_no_manie_users(self) -> bool:
        """Check if there are no Manie users.

        Returns:
            bool: True if there are no Manie users, False otherwise.
        """
        return self.count_manie_users() == 0

    def has_many_manie_users(self) -> bool:
        """Check if there are more than one Manie users.

        Returns:
            bool: True if there are more than one Manie users, False otherwise.
        """
        return self.count_manie_users() > 1

    def has_no_agent_users(self) -> bool:
        """Check if there are no agent users.

        Returns:
            bool: True if there are no agent users, False otherwise.
        """
        return self.count_agent_users() == 0

    def users_with_no_verified_email_address(self) -> list[User]:
        """Get all users with no verified email address.

        Returns:
            list[User]: A list of all users with no verified email address.
        """
        return [
            user
            for user in self._cached_users
            if not user_has_verified_email_address(user)
        ]

    def users_with_no_primary_email_address(self) -> list[User]:
        """Get all users with no primary email address.

        Returns:
            list[User]: A list of all users with no primary email address.
        """
        return [
            user
            for user in self._cached_users
            if not _user_has_primary_email_address(user)
        ]

    def users_with_primary_verified_email_mismatch(self) -> list[User]:
        """Get all users with a mismatch between primary and verified email addresses.

        Returns:
            list[User]: A list of all users with a mismatch between primary and
                        verified email addresses.
        """
        mismatched_users = []

        for user in self._cached_users:
            primary_email_found = False
            verified_primary_email = False
            primary_email_matches = False

            for emailaddress in self._user_emails[user.id]:
                if emailaddress.primary:
                    primary_email_found = True
                    if emailaddress.verified:
                        verified_primary_email = True
                    if emailaddress.email == user.email:
                        primary_email_matches = True

            if primary_email_found and (
                not verified_primary_email or not primary_email_matches
            ):
                mismatched_users.append(user)

        return mismatched_users

    def users_with_no_email_address(self) -> list[User]:
        """Get all users with no email address.

        Returns:
            list[User]: A list of all users with no email address.
        """
        return [user for user in self._cached_users if not user.email]
