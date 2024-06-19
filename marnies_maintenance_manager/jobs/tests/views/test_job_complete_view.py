"""Tests for the JobCompleteView view."""

import datetime

from django.core.files.uploadedfile import SimpleUploadedFile
from django.template.response import TemplateResponse
from django.test import Client
from django.urls import reverse
from rest_framework import status
from typeguard import check_type

from marnies_maintenance_manager.jobs.models import Job
from marnies_maintenance_manager.jobs.tests.views.utils import assert_no_form_errors
from marnies_maintenance_manager.jobs.utils import safe_read



def test_view_has_job_date_field(
    marnie_user_client: Client,
    bob_job_with_deposit_pop: Job,
    test_pdf: SimpleUploadedFile,
) -> None:
    """Ensure the view has a field for the job date.

    Args:
        marnie_user_client (Client): The Django test client for Marnie.
        bob_job_with_deposit_pop (Job): The job created by Bob with the deposit POP.
        test_pdf (SimpleUploadedFile): The test PDF file.
    """
    response = submit_job_completion_form_and_assert_no_errors(
        marnie_user_client,
        bob_job_with_deposit_pop,
        test_pdf,
    )

    # Check the redirect chain that leads things up to here:
    expected_chain = [("/jobs/?agent=bob", status.HTTP_302_FOUND)]
    assert response.redirect_chain == expected_chain  # type: ignore[attr-defined]

    # Refresh the Maintenance Job from the database, and then check the updated
    # record:
    bob_job_with_deposit_pop.refresh_from_db()
    assert bob_job_with_deposit_pop.job_date == datetime.date(2022, 3, 4)


def submit_job_completion_form_and_assert_no_errors(
    client: Client,
    job: Job,
    test_pdf: SimpleUploadedFile,
) -> TemplateResponse:
    """Submit the job completion form and assert no errors.

    Args:
        client (Client): The Django test client.
        job (Job): The job instance to be updated.
        test_pdf (SimpleUploadedFile): The test PDF file.

    Returns:
        TemplateResponse: The response object after submitting the form.
    """
    test_pdf.seek(0)
    with safe_read(test_pdf):
        response = check_type(
            client.post(
                reverse(
                    "jobs:job_complete",
                    kwargs={"pk": job.pk},
                ),
                data={
                    "job_date": "2022-03-04",
                    "invoice": test_pdf,
                    "comments": "This job is now complete.",
                },
                follow=True,
            ),
            TemplateResponse,
        )

    # Assert the response status code is 200
    assert response.status_code == status.HTTP_200_OK

    # There shouldn't be any form errors:
    assert_no_form_errors(response)
    return response
