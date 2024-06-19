"""Fixtures for the view tests."""

# pylint: disable=redefined-outer-name

import datetime

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template.response import TemplateResponse
from django.test import Client
from django.urls import reverse
from rest_framework import status
from typeguard import check_type

from marnies_maintenance_manager.jobs.models import Job
from marnies_maintenance_manager.jobs.tests.views.utils import assert_no_form_errors
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
def job_created_by_alice(alice_agent_user: User) -> Job:
    """Create a job instance for Alice the agent.

    Args:
        alice_agent_user (User): The User instance representing Alice the agent.

    Returns:
        Job: The job instance created for Alice.

    """
    return Job.objects.create(
        agent=alice_agent_user,
        date="2022-01-01",
        address_details="1234 Main St, Springfield, IL",
        gps_link="https://www.google.com/maps",
        quote_request_details="Replace the kitchen sink",
    )


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
def bob_job_with_initial_marnie_inspection(
    job_created_by_bob: Job,
    marnie_user_client: Client,
    bob_job_update_url: str,
    test_pdf: SimpleUploadedFile,
) -> Job:
    """Create a job with the initial inspection done by Marnie.

    Args:
        job_created_by_bob (Job): The job created by Bob.
        marnie_user_client (Client): The Django test client for Marnie.
        bob_job_update_url (str): The URL for the job update view for the job created
            by Bob.
        test_pdf (SimpleUploadedFile): The test PDF file.

    Returns:
        Job: The job created by Bob with the initial inspection done by Marnie.
    """
    job = job_created_by_bob

    # Check that the Job is in the correct initial state:
    assert job.status == Job.Status.PENDING_INSPECTION.value

    response = check_type(
        marnie_user_client.post(
            bob_job_update_url,
            {
                "date_of_inspection": "2001-02-05",
                "quote": test_pdf,
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
def job_rejected_by_bob(bob_job_with_initial_marnie_inspection: Job) -> Job:
    """Return a job where Bob has rejected the quote.

    Args:
        bob_job_with_initial_marnie_inspection (Job): The job created by Bob with the
            initial inspection done by Marnie.

    Returns:
        Job: The job where Bob has rejected the quote.
    """
    job = bob_job_with_initial_marnie_inspection
    job.status = Job.Status.QUOTE_REJECTED_BY_AGENT.value
    job.accepted_or_rejected = Job.AcceptedOrRejected.REJECTED.value
    job.save()
    return job


@pytest.fixture()
def job_accepted_by_bob(bob_job_with_initial_marnie_inspection: Job) -> Job:
    """Return a job where Bob has accepted the quote.

    Args:
        bob_job_with_initial_marnie_inspection (Job): The job created by Bob with the
            initial inspection done by Marnie.

    Returns:
        Job: The job where Bob has accepted the quote.
    """
    job = bob_job_with_initial_marnie_inspection
    job.status = Job.Status.QUOTE_ACCEPTED_BY_AGENT.value
    job.accepted_or_rejected = Job.AcceptedOrRejected.ACCEPTED.value
    job.save()
    return job


@pytest.fixture()
def bob_job_with_deposit_pop(
    job_accepted_by_bob: Job,
    test_pdf: SimpleUploadedFile,
) -> Job:
    """Return a job where Bob has uploaded the deposit proof of payment.

    Args:
        job_accepted_by_bob (Job): The job where Bob has accepted the quote.
        test_pdf (SimpleUploadedFile): The test PDF file.

    Returns:
        Job: The job where Bob has uploaded the deposit proof of payment.
    """
    job = job_accepted_by_bob
    job.deposit_proof_of_payment = test_pdf
    job.status = Job.Status.DEPOSIT_POP_UPLOADED.value
    job.save()
    return job
