"""User view module for Manie's Maintenance Manager.

This module defines views for user interactions such as viewing user details,
updating user information, and redirecting to specific user pages, ensuring
access control through authentication.
"""

from typing import TYPE_CHECKING
from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.db.models import QuerySet
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView
from django.views.generic import RedirectView
from django.views.generic import UpdateView
from typeguard import check_type

from manies_maintenance_manager.users.models import User

if TYPE_CHECKING:  # pragma: no cover  # pylint: disable=consider-ternary-expression
    TypedQuerySet = QuerySet[User]
else:
    TypedQuerySet = QuerySet


class UserDetailView(LoginRequiredMixin, DetailView):  # type: ignore[type-arg]
    """Display the detailed view of a user profile.

    This view requires the user to be logged in and displays detailed
    information based on the username provided in the URL.
    """

    model = User
    slug_field = "username"
    slug_url_kwarg = "username"


user_detail_view = UserDetailView.as_view()


class UserUpdateView(
    LoginRequiredMixin,
    SuccessMessageMixin,  # type: ignore[type-arg]
    UpdateView,  # type: ignore[type-arg]
):
    """Handle updates to a user's profile information.

    This view updates the user's profile, handles the form submission, and
    displays a success message upon update. It ensures that the user updating
    the profile is authenticated.
    """

    model = User
    fields = ["name"]
    success_message = _("Information successfully updated")

    def get_success_url(self) -> str:
        """Return the URL to redirect to after a successful profile update.

        Constructs the URL for the user's detailed profile view based on their
        authenticated status.

        Returns:
            str: The URL to redirect to the user's detailed profile view.
        """
        return check_type(self.request.user, User).get_absolute_url()

    def get_object(self, queryset: TypedQuerySet | None = None) -> User:
        """Retrieve and return the current user's profile.

        Ensures that the user is authenticated before retrieving their profile.
        If the user is not authenticated, this method raises a ValueError.

        Args:
            queryset (TypedQuerySet, optional): The queryset to retrieve the user
                profile from.

        Returns:
            User: The profile of the currently authenticated user.
        """
        return check_type(self.request.user, User)


user_update_view = UserUpdateView.as_view()


class UserRedirectView(LoginRequiredMixin, RedirectView):
    """Redirect users to their detailed profile view.

    This view automatically redirects logged-in users to their own user detail
    page, improving the user navigation experience.
    """

    permanent = False

    def get_redirect_url(self, *args: Any, **kwargs: Any) -> str:
        """Return the URL for the user's detailed profile view.

        Determines and returns the URL based on the logged-in user's username.
        This method constructs the URL by reversing the 'users:detail' view
        with the current user's username as a keyword argument.

        Args:
            *args (Any): Additional positional arguments.
            **kwargs (Any): Additional keyword arguments.

        Returns:
            str: The URL to redirect to the user's detailed profile view.
        """
        return reverse("users:detail", kwargs={"username": self.request.user.username})


user_redirect_view = UserRedirectView.as_view()
