"""Define pytest fixtures for testing user authentication in job views."""

# pylint: disable=unused-argument, redefined-outer-name

import pytest
from django.template.response import TemplateResponse
from django.test import Client
from django.urls import reverse
from rest_framework import status
from typeguard import check_type

from marnies_maintenance_manager.jobs.models import Job
from marnies_maintenance_manager.jobs.tests.views.utils import assert_no_form_errors
from marnies_maintenance_manager.jobs.utils import get_test_user_password
from marnies_maintenance_manager.users.models import User


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
    logged_in = client.login(username="bob", password=get_test_user_password())
    assert logged_in
    return client


@pytest.fixture()
def alice_agent_user_client(client: Client, alice_agent_user: User) -> Client:
    """Supply a logged-in test client for agent user Alice.

    Args:
        client (Client): The fixture to use for creating an HTTP client.
        alice_agent_user (User): The agent user Alice from the user model.

    Returns:
        Client: A Django test client logged in as agent user Alice.
    """
    logged_in = client.login(username="alice", password=get_test_user_password())
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
    logged_in = client.login(username="admin", password=get_test_user_password())
    assert logged_in
    return client


@pytest.fixture()
def job_created_by_bob(bob_agent_user: User) -> Job:
    """Create a job instance, itself created by Bob.

    This fixture ensures that the job data is valid and raises a ValidationError if
    the data does not comply with model constraints.

    Args:
        bob_agent_user (User): The User model instance for Bob, who is marked as an
                               agent.

    Returns:
        Job: A Job model instance representing a maintenance job created by Bob.
    """
    return Job.objects.create(
        agent=bob_agent_user,
        date="2022-01-01",
        address_details="1234 Main St, Springfield, IL",
        gps_link="https://www.google.com/maps",
        quote_request_details="Replace the kitchen sink",
    )


@pytest.fixture()
def bob_job_with_initial_marnie_inspection(
    job_created_by_bob: Job,
    marnie_user_client: Client,
    bob_job_complete_inspection_url: str,
) -> Job:
    """Create a job with the initial inspection done by Marnie.

    Args:
        job_created_by_bob (Job): The job created by Bob.
        marnie_user_client (Client): The Django test client for Marnie.
        bob_job_complete_inspection_url (str): The URL for the view where Marnie can
            inspect the site from the job created by Bob.

    Returns:
        Job: The job created by Bob with the initial inspection done by Marnie.
    """
    job = job_created_by_bob

    # Check that the Job is in the correct initial state:
    assert job.status == Job.Status.PENDING_INSPECTION.value

    response = check_type(
        marnie_user_client.post(
            bob_job_complete_inspection_url,
            {
                "date_of_inspection": "2001-02-05",
            },
            follow=True,
        ),
        TemplateResponse,
    )

    # Assert the response status code is 200
    assert response.status_code == status.HTTP_200_OK

    # There should be no form errors
    assert_no_form_errors(response)

    # Check that the job is in the correct state after inspection:
    job.refresh_from_db()
    assert job.status == Job.Status.INSPECTION_COMPLETED.value

    # Return the Job where Marnie has now inspected the site.
    return job


@pytest.fixture()
def bob_job_complete_inspection_url(job_created_by_bob: Job) -> str:
    """Return the URL for "site inspection complete" view for the job created by Bob.

    Args:
        job_created_by_bob (Job): The job created by Bob.

    Returns:
        str: The URL for Bobs job "site inspection complete" view.
    """
    return reverse("jobs:job_complete_inspection", kwargs={"pk": job_created_by_bob.pk})


@pytest.fixture()
def bob_job_upload_quote_url(bob_job_with_initial_marnie_inspection: Job) -> str:
    """Return the URL for "upload quote" view for the job created by Bob.

    Args:
        bob_job_with_initial_marnie_inspection (Job): The job created by Bob with the
            initial inspection done by Marnie.

    Returns:
        str: The URL for Bobs job "upload quote" view.
    """
    return reverse(
        "jobs:quote_upload",
        kwargs={"pk": bob_job_with_initial_marnie_inspection.pk},
    )
