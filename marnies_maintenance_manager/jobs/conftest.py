"""Define pytest fixtures for testing user authentication in job views."""

# pylint: disable=unused-argument

import pytest
from django.test.client import Client

from marnies_maintenance_manager.jobs.models import Job
from marnies_maintenance_manager.users.models import User


@pytest.fixture()
def bob_agent_user_client(client: Client, bob_agent_user: User) -> Client:
    """Provide a logged-in test client for agent user Bob.

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
def bob_agent_user_without_verified_email_client(
    client: Client,
    bob_agent_user_without_verified_email: User,
) -> Client:
    """Provide a logged-in test client for agent user Bob without a verified email.

    Args:
        client (Client): The fixture to use for creating an HTTP client.
        bob_agent_user_without_verified_email (User): The agent user Bob from the
            user model.

    Returns:
        Client: A Django test client logged in as agent user Bob without a verified
            email.
    """
    logged_in = client.login(username="bob", password="password")  # noqa: S106
    assert logged_in
    return client


@pytest.fixture()
def peter_agent_user_client(client: Client, peter_agent_user: User) -> Client:
    """Supply a logged-in test client for agent user Peter.

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
def superuser_client(client: Client, superuser_user: User) -> Client:
    """Create a logged-in test client for a superuser.

    Args:
        client (Client): The fixture to use for creating an HTTP client.
        superuser_user (User): The superuser from the user model.

    Returns:
        Client: A Django test client logged in as a superuser.
    """
    logged_in = client.login(username="admin", password="password")  # noqa: S106
    assert logged_in
    return client


@pytest.fixture()
def job_created_by_bob(bob_agent_user: User) -> Job:
    """Create a job instance that was created by Bob.

    This fixture ensures that the job data is valid and raises a ValidationError if
    the data does not comply with model constraints.

    Args:
        bob_agent_user (User): The User model instance for Bob, who is marked as an
                               agent.

    Returns:
        Job: A Job model instance representing a maintenance job created by Bob.
    """
    job = Job.objects.create(
        agent=bob_agent_user,
        date="2022-01-01",
        address_details="1234 Main St, Springfield, IL",
        gps_link="https://www.google.com/maps",
        quote_request_details="Replace the kitchen sink",
    )
    # Make sure that the job is valid before returning it
    job.full_clean()
    return job
