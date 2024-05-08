"""
Unit tests for admin interfaces of Manie's Maintenance Manager user module.

These tests verify that admin functionalities such as listing, searching,
adding, and viewing users work correctly.
"""

import contextlib
from http import HTTPStatus
from importlib import reload

import pytest
from django.contrib import admin
from django.contrib.auth.models import AnonymousUser
from django.test.client import Client
from django.test.client import RequestFactory
from django.urls import reverse
from pytest_django.asserts import assertRedirects
from pytest_django.fixtures import SettingsWrapper

from manies_maintenance_manager.users.models import User


class TestUserAdmin:
    """Test admin operations for User model."""

    def test_changelist(self, admin_client: Client) -> None:
        """Verify that user changelist page loads correctly."""
        url = reverse("admin:users_user_changelist")
        response = admin_client.get(url)
        assert response.status_code == HTTPStatus.OK

    def test_search(self, admin_client: Client) -> None:
        """Ensure that user search functionality works correctly."""
        url = reverse("admin:users_user_changelist")
        response = admin_client.get(url, data={"q": "test"})
        assert response.status_code == HTTPStatus.OK

    def test_add(self, admin_client: Client) -> None:
        """Test adding a new user through the admin interface."""
        url = reverse("admin:users_user_add")
        response = admin_client.get(url)
        assert response.status_code == HTTPStatus.OK

        response = admin_client.post(
            url,
            data={
                "username": "test",
                "password1": "My_R@ndom-P@ssw0rd",
                "password2": "My_R@ndom-P@ssw0rd",
            },
        )
        assert response.status_code == HTTPStatus.FOUND
        assert User.objects.filter(username="test").exists()

    def test_view_user(self, admin_client: Client) -> None:
        """Confirm that user detail view in admin works as expected."""
        user = User.objects.get(username="admin")
        url = reverse("admin:users_user_change", kwargs={"object_id": user.pk})
        response = admin_client.get(url)
        assert response.status_code == HTTPStatus.OK

    @pytest.fixture()
    def _force_allauth(self, settings: SettingsWrapper) -> None:
        """Configure settings to force Allauth in admin for testing."""
        settings.DJANGO_ADMIN_FORCE_ALLAUTH = True
        # Reload the admin module to apply the setting change
        import manies_maintenance_manager.users.admin as users_admin

        with contextlib.suppress(admin.sites.AlreadyRegistered):
            reload(users_admin)

    @pytest.mark.django_db()
    @pytest.mark.usefixtures("_force_allauth")
    def test_allauth_login(
        self,
        rf: RequestFactory,
        settings: SettingsWrapper,
    ) -> None:
        """Check Allauth integration with admin login."""
        request = rf.get("/fake-url")
        request.user = AnonymousUser()
        response = admin.site.login(request)

        # The `admin` login view should redirect to the `allauth` login view
        target_url = reverse(settings.LOGIN_URL) + "?next=" + request.path
        assertRedirects(response, target_url, fetch_redirect_response=False)
