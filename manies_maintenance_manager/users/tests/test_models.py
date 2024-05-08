"""Unit tests for the User model in Manie's Maintenance Manager."""

from manies_maintenance_manager.users.models import User


def test_user_get_absolute_url(user: User) -> None:
    """Verify that the User model's get_absolute_url method returns the correct URL."""
    assert user.get_absolute_url() == f"/users/{user.username}/"
