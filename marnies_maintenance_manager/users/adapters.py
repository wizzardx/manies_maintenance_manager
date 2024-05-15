"""Provide adapters for account and social account handling."""

from __future__ import annotations

import typing
from typing import cast

from allauth.account.adapter import DefaultAccountAdapter
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.conf import settings

if typing.TYPE_CHECKING:
    from allauth.socialaccount.models import SocialLogin
    from django.http import HttpRequest

    from marnies_maintenance_manager.users.models import User  # noqa: TCH004


class AccountAdapter(DefaultAccountAdapter):  # type: ignore[misc]
    """Determine if the site is currently open for new user registrations."""

    def is_open_for_signup(self, request: HttpRequest) -> bool:
        """Check if the site is accepting new registrations.

        Args:
            request (HttpRequest): The HTTP request.

        Returns:
            bool: True if the site is open for new registrations, False otherwise.
        """
        return getattr(settings, "ACCOUNT_ALLOW_REGISTRATION", True)


class SocialAccountAdapter(DefaultSocialAccountAdapter):  # type: ignore[misc]
    """Handle signup conditions and user population for social accounts."""

    def is_open_for_signup(
        self,
        request: HttpRequest,
        sociallogin: SocialLogin,
    ) -> bool:
        """Check if the site is accepting new registrations via social accounts.

        Args:
            request (HttpRequest): The HTTP request.
            sociallogin (SocialLogin): The social login instance.

        Returns:
            bool: True if the site is open for new registrations, False otherwise.
        """
        return getattr(settings, "ACCOUNT_ALLOW_REGISTRATION", True)

    def populate_user(
        self,
        request: HttpRequest,
        sociallogin: SocialLogin,
        data: dict[str, typing.Any],
    ) -> User:
        # pylint: disable=line-too-long
        """Populate user information from social provider info.

        Args:
            request (HttpRequest): The HTTP request.
            sociallogin (SocialLogin): The social login instance.
            data (dict[str, typing.Any]): Data from the social provider.

        Returns:
            User: The populated user instance.

        See: https://docs.allauth.org/en/latest/socialaccount/advanced.html#creating-and-populating-user-instances
        """
        user = cast(User, super().populate_user(request, sociallogin, data))
        if not user.name:
            if name := data.get("name"):
                user.name = name
            elif first_name := data.get("first_name"):
                user.name = first_name
                if last_name := data.get("last_name"):
                    user.name += f" {last_name}"
        return user
