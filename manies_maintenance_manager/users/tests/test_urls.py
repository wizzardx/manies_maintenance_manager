"""
Unit tests for URL configurations in Manie's Maintenance Manager user module.

This module provides tests to ensure that URL routes resolve correctly to their
associated views for user detail, update, and redirection functionalities.
"""

from django.urls import resolve
from django.urls import reverse

from manies_maintenance_manager.users.models import User


def test_detail(user: User) -> None:
    """
    Verify the user detail URL and its resolution.

    Args:
        user (User): The user object to construct the URL.

    Tests the correctness of the reverse and resolve functions for the user
    detail view based on the provided user's username.
    """
    assert (
        reverse("users:detail", kwargs={"username": user.username})
        == f"/users/{user.username}/"
    )
    assert resolve(f"/users/{user.username}/").view_name == "users:detail"


def test_update() -> None:
    """
    Confirm that the update URL routes correctly.

    Ensures that the URL for updating user details resolves to the correct
    view name and matches the expected URL pattern.
    """
    assert reverse("users:update") == "/users/~update/"
    assert resolve("/users/~update/").view_name == "users:update"


@typechecked
def test_redirect() -> None:
    """
    Ensure that the redirect URL functions as intended.

    Validates that the URL designated for user redirection correctly resolves
    to the associated view and adheres to the expected URL pattern.
    """
    assert reverse("users:redirect") == "/users/~redirect/"
    assert resolve("/users/~redirect/").view_name == "users:redirect"
