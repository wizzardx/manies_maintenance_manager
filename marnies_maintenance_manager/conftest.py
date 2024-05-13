"""Configuration and fixtures for pytest for the marnies_maintenance_manager.

This module contains pytest fixtures and configurations that are used across
the tests for the Marnie's Maintenance Manager application. It sets up
necessary environments for tests, such as user fixtures and media storage.
"""

import py
import pytest
import pytest_django.fixtures
from django.test import Client

from marnies_maintenance_manager.users.models import User
from marnies_maintenance_manager.users.tests.factories import UserFactory


@pytest.fixture(autouse=True)
def _media_storage(
    settings: pytest_django.fixtures.SettingsWrapper,
    tmpdir: py.path.local,
) -> None:
    """
    Automatically set the MEDIA_ROOT in Django settings to a temporary directory.

    Args:
        settings (SettingsWrapper): Pytest fixture that provides Django settings.
        tmpdir (py.path.local): Pytest fixture that provides a temporary directory path
                                object.
    """
    settings.MEDIA_ROOT = tmpdir.strpath


# noinspection PyUnusedLocal
@pytest.fixture()
def user(db: None) -> User:
    """
    Provide a User instance from the UserFactory for use in tests.

    This fixture depends on the database fixture and returns a new user instance
    generated through the UserFactory.

    Args:
        db (None): Fixture to ensure the database is accessible.

    Returns:
        User: A new User instance created by the UserFactory.
    """
    return UserFactory()


def _make_user(
    django_user_model: type[User],
    username: str,
    *,
    is_agent: bool = False,
    is_superuser: bool = False,
    is_marnie: bool = False,
) -> User:
    """
    Create and return a new user with optional agent and superuser status.

    This function helps in creating a user instance with additional properties
    like being an agent or a superuser. It sets the username and password,
    marks the email as verified, and assigns the role based on the parameters.

    Args:
        django_user_model (type[User]): The User model used to create new users.
        username (str): The username for the new user.
        is_agent (bool): Flag to indicate if the user is an agent.
        is_superuser (bool): Flag to indicate if the user is a superuser.
        is_marnie (bool): Flag to indicate if the user is Marnie.

    Returns:
        User: The newly created user instance.
    """
    user_ = django_user_model.objects.create_user(
        username=username,
        password="password",  # noqa: S106
        is_agent=is_agent,
        is_superuser=is_superuser,
        is_marnie=is_marnie,
        email=f"{username}@example.com",
    )
    user_.emailaddress_set.create(  # type: ignore[attr-defined]
        email=f"{username}@example.com",
        primary=True,
        verified=True,
    )
    return user_


@pytest.fixture()
def bob_agent_user(django_user_model: type[User]) -> User:
    """
    Create a user fixture named 'bob' for testing job creation and login.

    Args:
        django_user_model (type[User]): The Django User model.

    Returns:
        User: A Django User instance configured as an agent, named 'bob'.
    """
    return _make_user(django_user_model, "bob", is_agent=True)


@pytest.fixture()
def peter_agent_user(django_user_model: type[User]) -> User:
    """
    Create a user fixture named 'peter' for testing job creation and login.

    Args:
        django_user_model (type[User]): The Django User model.

    Returns:
        User: A Django User instance configured as an agent, named 'peter'.
    """
    return _make_user(django_user_model, "peter", is_agent=True)


@pytest.fixture()
def marnie_user(django_user_model: type[User]) -> User:
    """
    Create a user fixture named 'marnie' for testing job creation and login.

    Args:
        django_user_model (type[User]): The Django User model.

    Returns:
        User: A Django User instance configured as 'marnie', without agent privileges.
    """
    return _make_user(django_user_model, "marnie", is_marnie=True)


@pytest.fixture()
def superuser_user(django_user_model: type[User]) -> User:
    """
    Create a superuser fixture for testing administrative privileges.

    Args:
        django_user_model (type[User]): The Django User model.

    Returns:
        User: A Django User instance with superuser privileges, named 'admin'.
    """
    return _make_user(django_user_model, "admin", is_superuser=True)


@pytest.fixture()
def marnie_user_client(client: Client, marnie_user: User) -> Client:
    """
    Generate a logged-in test client for user Marnie.

    Args:
        client (Client): The fixture to use for creating an HTTP client.
        marnie_user (User): The non-agent user Marnie from the user model.

    Returns:
        Client: A Django test client logged in as non-agent user Marnie.
    """
    logged_in = client.login(username="marnie", password="password")  # noqa: S106
    assert logged_in
    return client
