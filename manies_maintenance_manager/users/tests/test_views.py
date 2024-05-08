"""
Unit tests for user views in Manie's Maintenance Manager.

This module provides tests for various user-related views, ensuring that
redirection, detail viewing, and profile updating operate as expected
within the application's user interface.
"""

from http import HTTPStatus

import pytest
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.models import AnonymousUser
from django.contrib.messages.middleware import MessageMiddleware
from django.contrib.sessions.middleware import SessionMiddleware
from django.http import HttpRequest
from django.http import HttpResponseRedirect
from django.test import RequestFactory
from django.urls import reverse
from django.utils.translation import gettext_lazy as _

from manies_maintenance_manager.users.forms import UserAdminChangeForm
from manies_maintenance_manager.users.models import User
from manies_maintenance_manager.users.tests.factories import UserFactory
from manies_maintenance_manager.users.views import UserRedirectView
from manies_maintenance_manager.users.views import UserUpdateView
from manies_maintenance_manager.users.views import user_detail_view

pytestmark = pytest.mark.django_db


class TestUserUpdateView:
    """
    Tests for the user profile update functionality.

    This class contains tests to verify the behavior of the UserUpdateView,
    focusing on URL redirection, object retrieval, and form processing within
    the view.

    TODO:
        extracting view initialization code as class-scoped fixture
        would be great if only pytest-django supported non-function-scoped
        fixture db access -- this is a work-in-progress for now:
        https://github.com/pytest-dev/pytest-django/pull/258
    """

    def dummy_get_response(self, request: HttpRequest) -> None:
        """
        Provide a dummy response for middleware usage.

        Args:
            request (HttpRequest): The incoming HTTP request.

        Returns:
            None
        """
        return

    def test_get_success_url(self, user: User, rf: RequestFactory) -> None:
        """
        Ensure the URL to redirect to after a successful update is correct.

        Args:
            user (User): The user object for which the URL is generated.
            rf (RequestFactory): Factory for creating request instances.

        Tests the get_success_url method of the UserUpdateView.
        """
        view = UserUpdateView()
        request = rf.get("/fake-url/")
        request.user = user

        view.request = request
        assert view.get_success_url() == f"/users/{user.username}/"

    def test_get_object(self, user: User, rf: RequestFactory) -> None:
        """
        Test that the correct user object is retrieved for update.

        Args:
            user (User): The user instance expected to be retrieved.
            rf (RequestFactory): Factory for creating request instances.

        Tests the get_object method of the UserUpdateView.
        """
        view = UserUpdateView()
        request = rf.get("/fake-url/")
        request.user = user

        view.request = request

        assert view.get_object() == user

    def test_form_valid(self, user: User, rf: RequestFactory) -> None:
        """
        Verify that the form processing and messaging work correctly.

        Args:
            user (User): The user instance to be updated.
            rf (RequestFactory): Factory for creating request instances.

        Tests the form_valid method of the UserUpdateView.
        """
        view = UserUpdateView()
        request = rf.get("/fake-url/")

        # Add the session/message middleware to the request
        (
            SessionMiddleware(self.dummy_get_response).  # type: ignore[arg-type]
            process_request(request)
        )
        (
            MessageMiddleware(self.dummy_get_response).  # type: ignore[arg-type]
            process_request(request)
        )
        request.user = user

        view.request = request

        # Initialize the form
        form = UserAdminChangeForm()
        form.cleaned_data = {}
        form.instance = user
        view.form_valid(form)

        messages_sent = [m.message for m in messages.get_messages(request)]
        assert messages_sent == [_("Information successfully updated")]


class TestUserRedirectView:
    """
    Tests for the UserRedirectView functionality.

    These tests ensure that the UserRedirectView correctly generates the
    expected URL to which a logged-in user should be redirected.
    """

    def test_get_redirect_url(self, user: User, rf: RequestFactory) -> None:
        """
        Test the URL generation for redirecting a logged-in user.

        Args:
            user (User): The logged-in user for whom the URL is generated.
            rf (RequestFactory): Factory for creating request instances.

        Tests the get_redirect_url method of the UserRedirectView.
        """
        view = UserRedirectView()
        request = rf.get("/fake-url")
        request.user = user

        view.request = request
        assert view.get_redirect_url() == f"/users/{user.username}/"


class TestUserDetailView:
    """
    Tests for the UserDetailView functionality.

    These tests verify that the UserDetailView behaves correctly under
    authenticated and unauthenticated scenarios.
    """

    def test_authenticated(self, user: User, rf: RequestFactory) -> None:
        """
        Ensure that an authenticated user can access the user detail view.

        Args:
            user (User): The user attempting to access their detail view.
            rf (RequestFactory): Factory for creating request instances.

        Tests the user_detail_view function for an authenticated user.
        """
        request = rf.get("/fake-url/")
        request.user = UserFactory()
        response = user_detail_view(request, username=user.username)

        assert response.status_code == HTTPStatus.OK

    def test_not_authenticated(self, user: User, rf: RequestFactory) -> None:
        """
        Check that an unauthenticated user is redirected to the login page.

        Args:
            user (User): The user attempting to access their detail view.
            rf (RequestFactory): Factory for creating request instances.

        Tests the user_detail_view function for an unauthenticated user.
        """
        request = rf.get("/fake-url/")
        request.user = AnonymousUser()
        response = user_detail_view(request, username=user.username)
        login_url = reverse(settings.LOGIN_URL)

        assert isinstance(response, HttpResponseRedirect)
        assert response.status_code == HTTPStatus.FOUND
        assert response.url == f"{login_url}?next=/fake-url/"
