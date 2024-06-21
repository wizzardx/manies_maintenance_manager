"""Tests for the JobCompleteView view."""

# pylint: disable=magic-value-comparison

import datetime

from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.test import Client
from django.urls import reverse
from rest_framework import status
from typeguard import check_type

from marnies_maintenance_manager.jobs.models import Job
from marnies_maintenance_manager.jobs.tests.views.utils import assert_no_form_errors
from marnies_maintenance_manager.jobs.tests.views.utils import (
    check_basic_page_html_structure,
)
from marnies_maintenance_manager.jobs.utils import safe_read
from marnies_maintenance_manager.jobs.views.job_complete_view import JobCompleteView


def test_anonymous_users_are_redirected_to_login_page(
    client: Client,
    bob_job_with_deposit_pop: Job,
) -> None:
    """Ensure anonymous users are redirected to the login page.

    Args:
        client (Client): The Django test client.
        bob_job_with_deposit_pop (Job): The job created by Bob with the deposit POP.
    """
    response = check_type(
        client.get(
            reverse("jobs:job_complete", kwargs={"pk": bob_job_with_deposit_pop.pk}),
        ),
        HttpResponseRedirect,
    )
    assert response.status_code == status.HTTP_302_FOUND
    assert (
        response.url
        == f"/accounts/login/?next=/jobs/{bob_job_with_deposit_pop.pk}/complete/"
    )


def test_view_is_accessible_by_marnie_when_pop_has_been_uploaded(
    bob_job_with_deposit_pop: Job,
    marnie_user_client: Client,
) -> None:
    """Ensure Marnie can access the view after the admin uploaded the POP.

    Args:
        bob_job_with_deposit_pop (Job): The job created by Bob with the deposit POP.
        marnie_user_client (Client): The Django test client for Marnie.
    """
    response = marnie_user_client.get(
        reverse("jobs:job_complete", kwargs={"pk": bob_job_with_deposit_pop.pk}),
    )
    assert response.status_code == status.HTTP_200_OK


def test_view_is_inaccessible_by_agents(
    bob_job_with_deposit_pop: Job,
    bob_agent_user_client: Client,
) -> None:
    """Ensure agents cannot access the view.

    Args:
        bob_job_with_deposit_pop (Job): The job created by Bob with the deposit POP.
        bob_agent_user_client (Client): The Django test client for Bob.
    """
    response = bob_agent_user_client.get(
        reverse("jobs:job_complete", kwargs={"pk": bob_job_with_deposit_pop.pk}),
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_view_is_accessible_by_admins(
    bob_job_with_deposit_pop: Job,
    admin_client: Client,
) -> None:
    """Ensure admins can access the view.

    Args:
        bob_job_with_deposit_pop (Job): The job created by Bob with the deposit POP.
        admin_client (Client): The Django test client for the admin user.
    """
    response = admin_client.get(
        reverse("jobs:job_complete", kwargs={"pk": bob_job_with_deposit_pop.pk}),
    )
    assert response.status_code == status.HTTP_200_OK


def test_page_has_basic_correct_structure(
    marnie_user_client: Client,
    bob_job_with_deposit_pop: Job,
) -> None:
    """Test that the job update page has the correct basic structure.

    Args:
        marnie_user_client (Client): The Django test client for Marnie.
        bob_job_with_deposit_pop (Job): The job created by Bob with the deposit POP.
    """
    url = reverse("jobs:job_complete", kwargs={"pk": bob_job_with_deposit_pop.pk})
    check_basic_page_html_structure(
        client=marnie_user_client,
        url=url,
        expected_title="Complete the Job",
        expected_template_name="jobs/job_complete.html",
        expected_h1_text="Complete the Job",
        expected_func_name="view",
        expected_url_name="job_complete",
        expected_view_class=JobCompleteView,
    )


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


def test_view_has_comments_field(
    marnie_user_client: Client,
    bob_job_with_deposit_pop: Job,
    test_pdf: SimpleUploadedFile,
) -> None:
    """Ensure the view has a field for the comments.

    Args:
        marnie_user_client (Client): The Django test client for Marnie.
        bob_job_with_deposit_pop (Job): The job created by Bob with the deposit POP.
        test_pdf (SimpleUploadedFile): The test PDF file.
    """
    with safe_read(test_pdf):
        response = check_type(
            marnie_user_client.post(
                reverse(
                    "jobs:job_complete",
                    kwargs={"pk": bob_job_with_deposit_pop.pk},
                ),
                data={
                    "comments": "This job is now complete.",
                    "job_date": "2022-03-04",
                    "invoice": test_pdf,
                },
                follow=True,
            ),
            TemplateResponse,
        )

    # Assert the response status code is 200
    assert response.status_code == status.HTTP_200_OK

    # There shouldn't be any form errors:
    assert_no_form_errors(response)

    # Check the redirect chain that leads things up to here:
    expected_chain = [("/jobs/?agent=bob", status.HTTP_302_FOUND)]
    assert response.redirect_chain == expected_chain  # type: ignore[attr-defined]

    # Refresh the Maintenance Job from the database, and then check the updated
    # record:
    bob_job_with_deposit_pop.refresh_from_db()
    assert bob_job_with_deposit_pop.comments == "This job is now complete."
