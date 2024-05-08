"""Configuration and fixtures for pytest for the manies_maintenance_manager.

This module contains pytest fixtures and configurations that are used across
the tests for the Manie's Maintenance Manager application. It sets up
necessary environments for tests, such as user fixtures and media storage.
"""

import py
import pytest
import pytest_django.fixtures

from manies_maintenance_manager.users.models import User
from manies_maintenance_manager.users.tests.factories import UserFactory


@pytest.fixture(autouse=True)
def _media_storage(
    settings: pytest_django.fixtures.SettingsWrapper,
    tmpdir: py.path.local,
) -> None:
    settings.MEDIA_ROOT = tmpdir.strpath


# noinspection PyUnusedLocal
@pytest.fixture()
def user(db: None) -> User:
    """Provide a User instance from the UserFactory for use in tests.

    This fixture depends on the database fixture and returns a new user instance
    generated through the UserFactory.

    Returns:
        A new User instance.
    """
    return UserFactory()


@pytest.fixture()
def bob_agent_user(django_user_model: type[User]) -> User:
    """
    Create a user fixture named 'bob' for testing job creation and login.

    This fixture uses the Django user model to create a user and associated
    email address, setting up a typical user environment for tests.
    """
    user_ = django_user_model.objects.create_user(
        username="bob",
        password="password",  # noqa: S106
        is_agent=True,
    )
    user_.emailaddress_set.create(  # type: ignore[attr-defined]
        email="bob@example.com",
        primary=True,
        verified=True,
    )
    return user_


@pytest.fixture()
def marnie_user(django_user_model: type[User]) -> User:
    """
    Create a user fixture named 'marnie' for testing job creation and login.

    This fixture uses the Django user model to create a user and associated
    email address, setting up a typical user environment for tests.
    """
    user_ = django_user_model.objects.create_user(
        username="marnie",
        password="password",  # noqa: S106
    )
    user_.emailaddress_set.create(  # type: ignore[attr-defined]
        email="marnie@example.com",
        primary=True,
        verified=True,
    )
    return user_
