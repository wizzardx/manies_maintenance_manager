"""Configuration and fixtures for pytest for the manies_maintenance_manager.

This module contains pytest fixtures and configurations that are used across
the tests for the Manie's Maintenance Manager application. It sets up
necessary environments for tests, such as user fixtures and media storage.
"""

# pylint: disable=redefined-outer-name,unused-argument

import py
import pytest
import pytest_django.fixtures
from django.test import Client

from manies_maintenance_manager.jobs.tests.utils import make_test_user
from manies_maintenance_manager.jobs.utils import get_test_user_password
from manies_maintenance_manager.users.models import User
from manies_maintenance_manager.users.tests.factories import UserFactory


@pytest.fixture(autouse=True)
def _media_storage(
    settings: pytest_django.fixtures.SettingsWrapper,
    tmpdir: py.path.local,  # pylint: disable=no-member
) -> None:
    """Automatically set the MEDIA_ROOT in Django settings to a temporary directory.

    Args:
        settings (SettingsWrapper): Pytest fixture that provides Django settings.
        tmpdir (py.path.local): Pytest fixture that provides a temporary directory path
                                object.
    """
    settings.MEDIA_ROOT = tmpdir.strpath


# noinspection PyUnusedLocal
@pytest.fixture()
def user(db: None) -> User:  # pylint: disable=unused-argument
    """Provide a User instance from the UserFactory for use in tests.

    This fixture depends on the database fixture and returns a new user instance
    generated through the UserFactory.

    Args:
        db (None): Fixture to ensure the database is accessible.

    Returns:
        User: A new User instance created by the UserFactory.
    """
    return UserFactory()


@pytest.fixture()
def bob_agent_user(django_user_model: type[User]) -> User:
    """Create a user fixture named 'bob' for testing job creation and login.

    Args:
        django_user_model (type[User]): The Django User model.

    Returns:
        User: A Django User instance configured as an agent, named 'bob'.
    """
    return make_test_user(django_user_model, "bob", is_agent=True)


@pytest.fixture()
def bob_agent_user_without_verified_email(django_user_model: type[User]) -> User:
    """Create a user fixture named 'bob' for testing job creation and login.

    Args:
        django_user_model (type[User]): The Django User model.

    Returns:
        User: A Django User instance configured as an agent, named 'bob'.
    """
    return make_test_user(django_user_model, "bob", is_agent=True, email_verified=False)


@pytest.fixture()
def alice_agent_user(django_user_model: type[User]) -> User:
    """Create a user fixture named 'alice' for testing job creation and login.

    Args:
        django_user_model (type[User]): The Django User model.

    Returns:
        User: A Django User instance configured as an agent, named 'alice'.
    """
    return make_test_user(django_user_model, "alice", is_agent=True)


@pytest.fixture()
def manie_user(django_user_model: type[User]) -> User:
    """Create a user fixture named 'manie' for testing job creation and login.

    Args:
        django_user_model (type[User]): The Django User model.

    Returns:
        User: A Django User instance configured as 'manie', without agent privileges.
    """
    return make_test_user(django_user_model, "manie", is_manie=True)


@pytest.fixture()
def manie_user_without_verified_email(django_user_model: type[User]) -> User:
    """Create a user fixture named 'manie' for testing job creation and login.

    Args:
        django_user_model (type[User]): The Django User model.

    Returns:
        User: A Django User instance configured as 'manie', without agent privileges.
    """
    return make_test_user(
        django_user_model,
        "manie",
        is_manie=True,
        email_verified=False,
    )


@pytest.fixture()
def superuser_user(django_user_model: type[User]) -> User:
    """Create a superuser fixture for testing administrative privileges.

    Args:
        django_user_model (type[User]): The Django User model.

    Returns:
        User: A Django User instance with superuser privileges, named 'admin'.
    """
    return make_test_user(django_user_model, "admin", is_superuser=True)


@pytest.fixture()
def manie_user_client(manie_user: User) -> Client:
    """Generate a logged-in test client for user Manie.

    Args:
        manie_user (User): The non-agent user Manie from the user model.

    Returns:
        Client: A Django test client logged in as non-agent user Manie.
    """
    client = Client()
    logged_in = client.login(username="manie", password=get_test_user_password())
    assert logged_in
    return client


@pytest.fixture()
def unknown_user(django_user_model: type[User]) -> User:
    """Create a user fixture named 'unknown' for testing job creation and login.

    Args:
        django_user_model (type[User]): The Django User model.

    Returns:
        User: A Django User instance configured as an unknown user.
    """
    return make_test_user(django_user_model, "unknown")


@pytest.fixture()
def unknown_user_client(unknown_user: User) -> Client:
    """Generate a logged-in test client for an unknown user.

    Args:
        unknown_user (User): The unknown user from the user model.

    Returns:
        Client: A Django test client logged in as an unknown user.
    """
    client = Client()
    logged_in = client.login(username="unknown", password=get_test_user_password())
    assert logged_in
    return client


@pytest.fixture()
def bob_agent_user_client(bob_agent_user: User) -> Client:
    """Provide a logged-in test client for agent user Bob.

    Args:
        bob_agent_user (User): The agent user Bob from the user model.

    Returns:
        Client: A Django test client logged in as agent user Bob.
    """
    client = Client()
    logged_in = client.login(username="bob", password=get_test_user_password())
    assert logged_in
    return client
