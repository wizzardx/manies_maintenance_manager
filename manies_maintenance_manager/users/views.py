"""
User view module for Manie's Maintenance Manager.

This module defines views for user interactions such as viewing user details,
updating user information, and redirecting to specific user pages, ensuring
access control through authentication.
"""

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from django.views.generic import DetailView
from django.views.generic import RedirectView
from django.views.generic import UpdateView

from manies_maintenance_manager.users.models import User


class UserDetailView(LoginRequiredMixin, DetailView):
    """
    Display the detailed view of a user profile.

    This view requires the user to be logged in and displays detailed
    information based on the username provided in the URL.
    """

    model = User
    slug_field = "username"
    slug_url_kwarg = "username"


user_detail_view = UserDetailView.as_view()


class UserUpdateView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    """
    Handle updates to a user's profile information.

    This view updates the user's profile, handles the form submission, and
    displays a success message upon update. It ensures that the user updating
    the profile is authenticated.
    """

    model = User
    fields = ["name"]
    success_message = _("Information successfully updated")

    def get_success_url(self):
        """
        Get the URL to redirect to after a successful update.

        Returns the URL for the user's detailed profile view.
        """
        # for mypy to know that the user is authenticated
        assert self.request.user.is_authenticated
        return self.request.user.get_absolute_url()

    def get_object(self):
        """
        Retrieve the object that this view will display.

        Ensures the user is authenticated and returns the current user's
        profile. Raises ValueError if an unauthenticated user is encountered.
        """
        return self.request.user


user_update_view = UserUpdateView.as_view()


class UserRedirectView(LoginRequiredMixin, RedirectView):
    """
    Redirect users to their detailed profile view.

    This view automatically redirects logged-in users to their own user detail
    page, improving the user navigation experience.
    """

    permanent = False

    def get_redirect_url(self):
        """
        Determine the URL to redirect the user to.

        Redirects to the detailed user profile page based on the logged-in
        user's username.
        """
        return reverse("users:detail", kwargs={"username": self.request.user.username})


user_redirect_view = UserRedirectView.as_view()
