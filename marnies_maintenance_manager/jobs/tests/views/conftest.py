"""Fixtures for the view tests."""

import datetime
from pathlib import Path

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from rest_framework import status

from marnies_maintenance_manager.jobs.models import Job
from marnies_maintenance_manager.users.models import User


@pytest.fixture()
def job_created_by_bob(bob_agent_user: User) -> Job:
    """Create a job instance for Bob the agent.

    Args:
        bob_agent_user (User): The User instance representing Bob the agent.

    Returns:
        Job: The job instance created for Bob.

    """
    return Job.objects.create(
        agent=bob_agent_user,
        date=datetime.date(2022, 1, 1),
        address_details="1234 Main St, Springfield, IL",
        gps_link="https://www.google.com/maps",
        quote_request_details="Replace the kitchen sink",
    )


@pytest.fixture()
def job_created_by_peter(peter_agent_user: User) -> Job:
    """Create a job instance for Peter the agent.

    Args:
        peter_agent_user (User): The User instance representing Peter the agent.

    Returns:
        Job: The job instance created for Peter.

    """
    return Job.objects.create(
        agent=peter_agent_user,
        date="2022-01-01",
        address_details="1234 Main St, Springfield, IL",
        gps_link="https://www.google.com/maps",
        quote_request_details="Replace the kitchen sink",
    )


BASIC_TEST_PDF_FILE = Path(__file__).parent / "test.pdf"


@pytest.fixture()
def bob_job_update_url(job_created_by_bob: Job) -> str:
    """Return the URL for the job update view for the job created by Bob.

    Args:
        job_created_by_bob (Job): The job created by Bob.

    Returns:
        str: The URL for Bobs job update view.
    """
    return reverse("jobs:job_update", kwargs={"pk": job_created_by_bob.pk})


@pytest.fixture()
def test_pdf() -> SimpleUploadedFile:
    """Return a test PDF file as a SimpleUploadedFile.

    Returns:
        SimpleUploadedFile: The test PDF file.
    """
    return SimpleUploadedFile(
        "test.pdf",
        BASIC_TEST_PDF_FILE.read_bytes(),
        content_type="application/pdf",
    )


@pytest.fixture()
def bob_job_with_initial_marnie_inspection(
    job_created_by_bob,
    marnie_user_client,
    bob_job_update_url,
    test_pdf,
) -> Job:
    """Create a job with the initial inspection done by Marnie.

    Args:
        job_created_by_bob (Job): The job created by Bob.
        marnie_user_client (Client): The Django test client for Marnie.
        bob_job_update_url (str): The URL for the job update view for the job created
            by Bob.
        test_pdf (SimpleUploadedFile): The test PDF file.

    """
    job = job_created_by_bob

    # Check that the Job is in the correct initial state:
    assert job.status == Job.Status.PENDING_INSPECTION.value

    response = marnie_user_client.post(
        bob_job_update_url,
        {
            "date_of_inspection": "2001-02-05",
            "quote": test_pdf,
        },
        follow=True,
    )
    # Assert the response status code is 200
    assert response.status_code == status.HTTP_200_OK

    # Check that the job is in the correct state after inspection:
    job = Job.objects.get(pk=job.pk)
    assert job.status == Job.Status.INSPECTION_COMPLETED.value

    # Return the Job where Marnie has now inspected the site.
    return job
