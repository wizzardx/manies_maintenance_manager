"""Define pytest fixtures for testing user authentication in job views."""

import pytest
from django.test.client import Client

from marnies_maintenance_manager.users.models import User


@pytest.fixture()
def bob_agent_user_client(client: Client, bob_agent_user: User) -> Client:
    """
    Provide a logged-in test client for agent user Bob.

    Args:
        client (Client): The fixture to use for creating an HTTP client.
        bob_agent_user (User): The agent user Bob from the user model.

    Returns:
        Client: A Django test client logged in as agent user Bob.
    """
    logged_in = client.login(username="bob", password="password")  # noqa: S106
    assert logged_in
    return client


@pytest.fixture()
def peter_agent_user_client(client: Client, peter_agent_user: User) -> Client:
    """
    Supply a logged-in test client for agent user Peter.

    Args:
        client (Client): The fixture to use for creating an HTTP client.
        peter_agent_user (User): The agent user Peter from the user model.

    Returns:
        Client: A Django test client logged in as agent user Peter.
    """
    logged_in = client.login(username="peter", password="password")  # noqa: S106
    assert logged_in
    return client


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


@pytest.fixture()
def superuser_client(client: Client, superuser_user: User) -> Client:
    """
    Create a logged-in test client for a superuser.

    Args:
        client (Client): The fixture to use for creating an HTTP client.
        superuser_user (User): The superuser from the user model.

    Returns:
        Client: A Django test client logged in as a superuser.
    """
    logged_in = client.login(username="admin", password="password")  # noqa: S106
    assert logged_in
    return client
