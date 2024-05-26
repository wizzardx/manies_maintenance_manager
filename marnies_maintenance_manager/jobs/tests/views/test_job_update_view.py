"""Tests for the job update view."""

import datetime

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse
from rest_framework import status

from marnies_maintenance_manager.jobs.models import Job
from marnies_maintenance_manager.jobs.views import JobUpdateView
from marnies_maintenance_manager.users.models import User

from .utils import check_basic_page_html_structure


def test_anonymous_user_cannot_access_the_view(
    client: Client,
    job_created_by_bob: User,
) -> None:
    """Test that the anonymous user cannot access the job update view.

    Args:
        client (Client): The Django test client.
        job_created_by_bob (User): The job created by Bob.
    """
    # Note: Django-FastDev causes a DeprecationWarning to be logged when using the
    # {% if %} template tag. This is somewhere deep within the Django-Allauth package,
    # while handling a GET request to the /accounts/login/ URL. We can ignore this
    # for the purpose of our testing.
    with pytest.warns(
        DeprecationWarning,
        match="set FASTDEV_STRICT_IF in settings, and use {% ifexists %} instead of "
        "{% if %}",
    ):
        response = client.get(
            reverse("jobs:job_update", kwargs={"pk": job_created_by_bob.pk}),
            follow=True,
        )

    # This should be a redirect to a login page:
    assert response.status_code == status.HTTP_200_OK

    expected_redirect_chain = [
        (
            f"/accounts/login/?next=/jobs/{job_created_by_bob.id}/update/",
            status.HTTP_302_FOUND,
        ),
    ]
    assert response.redirect_chain == expected_redirect_chain


def test_agent_user_cannot_access_the_view(
    bob_agent_user_client: Client,
    job_created_by_bob: User,
) -> None:
    """Test that the agent user cannot access the job update view.

    Args:
        bob_agent_user_client (Client): The Django test client for Bob.
        job_created_by_bob (User): The job created by Bob.
    """
    response = bob_agent_user_client.get(
        reverse("jobs:job_update", kwargs={"pk": job_created_by_bob.pk}),
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_admin_user_can_access_the_view(
    superuser_client: Client,
    job_created_by_bob: User,
) -> None:
    """Test that the admin user can access the job update view.

    Args:
        superuser_client (Client): The Django test client for the superuser.
        job_created_by_bob (User): The job created by Bob.
    """
    response = superuser_client.get(
        reverse("jobs:job_update", kwargs={"pk": job_created_by_bob.pk}),
    )
    assert response.status_code == status.HTTP_200_OK


def test_marnie_user_can_access_the_view(
    marnie_user_client: Client,
    job_created_by_bob: User,
) -> None:
    """Test that the Marnie user can access the job update view.

    Args:
        marnie_user_client (Client): The Django test client for Marnie.
        job_created_by_bob (User): The job created by Bob.
    """
    response = marnie_user_client.get(
        reverse("jobs:job_update", kwargs={"pk": job_created_by_bob.pk}),
    )
    assert response.status_code == status.HTTP_200_OK


def test_page_has_basic_correct_structure(
    marnie_user_client: Client,
    job_created_by_bob: User,
) -> None:
    """Test that the job update page has the correct basic structure.

    Args:
        marnie_user_client (Client): The Django test client for Marnie.
        job_created_by_bob (User): The job created by Bob.
    """
    check_basic_page_html_structure(
        client=marnie_user_client,
        url=reverse("jobs:job_update", kwargs={"pk": job_created_by_bob.pk}),
        expected_title="Update Maintenance Job",
        expected_template_name="jobs/job_update.html",
        expected_h1_text="Update Maintenance Job",
        expected_func_name="view",
        expected_url_name="job_update",
        expected_view_class=JobUpdateView,
    )


def test_view_has_date_of_inspection_field(
    job_created_by_bob: Job,
    marnie_user_client: Client,
) -> None:
    """Test that the job update page has the 'date_of_inspection' field.

    Args:
        job_created_by_bob (Job): The job created by Bob.
        marnie_user_client (Client): The Django test client for Marnie.
    """
    quote_pdf = SimpleUploadedFile(
        "new.pdf",
        b"new_file_content",
        content_type="application/pdf",
    )

    response = marnie_user_client.post(
        reverse("jobs:job_update", kwargs={"pk": job_created_by_bob.pk}),
        {
            "date_of_inspection": "2001-02-05",
            "quote": quote_pdf,
        },
        follow=True,
    )
    # Assert the response status code is 200
    assert response.status_code == status.HTTP_200_OK

    # Check the redirect chain that leads things up to here:
    assert response.redirect_chain == [
        (f"/jobs/{job_created_by_bob.pk}/", status.HTTP_302_FOUND),
    ]

    # Refresh the Maintenance Job from the database, and then check the updated
    # record:
    job_created_by_bob.refresh_from_db()
    assert job_created_by_bob.date_of_inspection == datetime.date(2001, 2, 5)


def test_view_has_quote_field(
    job_created_by_bob: Job,
    marnie_user_client: Client,
) -> None:
    """Test that the job update page has the 'quote' field.

    Args:
        job_created_by_bob (Job): The job created by Bob.
        marnie_user_client (Client): The Django test client for Marnie.
    """
    # New PDF file to upload
    new_pdf = SimpleUploadedFile(
        "new.pdf",
        b"new_file_content",
        content_type="application/pdf",
    )

    # URL for updating the PDF document
    url = reverse("jobs:job_update", kwargs={"pk": job_created_by_bob.pk})

    # POST request to upload new PDF
    response = marnie_user_client.post(
        url,
        {
            "date_of_inspection": "2001-02-05",
            "quote": new_pdf,
        },
        follow=True,
    )

    # Assert the response status code is 200
    assert response.status_code == status.HTTP_200_OK

    # Check the redirect chain that leads things up to here:
    assert response.redirect_chain == [
        (f"/jobs/{job_created_by_bob.pk}/", status.HTTP_302_FOUND),
    ]

    # Refresh the Maintenance Job from the database
    job_created_by_bob.refresh_from_db()

    # And confirm that the PDF file has been updated
    assert job_created_by_bob.quote.name.endswith("new.pdf")


def test_date_of_inspection_field_is_required(
    job_created_by_bob: Job,
    marnie_user_client: Client,
) -> None:
    """Test that the 'date_of_inspection' field is required.

    Args:
        job_created_by_bob (Job): The job created by Bob.
        marnie_user_client (Client): The Django test client for Marnie.
    """
    url = reverse("jobs:job_update", kwargs={"pk": job_created_by_bob.pk})
    response = marnie_user_client.post(
        url,
        follow=True,
    )
    assert response.status_code == status.HTTP_200_OK

    # If there was the expected error with input (because there was no input provided),
    # then there shouldn't have been any redirections.
    assert response.redirect_chain == []

    # Check that the expected error is present.
    field_name = "date_of_inspection"
    form_errors = response.context["form"].errors
    assert field_name in form_errors
    assert form_errors[field_name] == ["This field is required."]


def test_quote_field_is_required(
    job_created_by_bob: Job,
    marnie_user_client: Client,
) -> None:
    """Test that the 'quote' field is required.

    Args:
        job_created_by_bob (Job): The job created by Bob.
        marnie_user_client (Client): The Django test client for Marnie.
    """
    # URL for updating the PDF document
    url = reverse("jobs:job_update", kwargs={"pk": job_created_by_bob.pk})

    # POST request to upload new PDF
    response = marnie_user_client.post(
        url,
        follow=True,
    )

    # Assert the response status code is 200
    assert response.status_code == status.HTTP_200_OK

    # If there was the expected error with input (because there was no input provided),
    # then there shouldn't have been any redirections.
    assert response.redirect_chain == []

    # Check that the expected error is present.
    field_name = "quote"
    form_errors = response.context["form"].errors
    assert field_name in form_errors
    assert form_errors[field_name] == ["This field is required."]


def test_updating_job_changes_status_to_inspection_completed(
    job_created_by_bob: Job,
    marnie_user_client: Client,
):
    """Test that updating the job changes the status to 'Inspection Completed'.

    Args:
        job_created_by_bob (Job): The job created by Bob.
        marnie_user_client (Client): The Django test client for Marnie.
    """
    # New PDF file to upload
    new_pdf = SimpleUploadedFile(
        "new.pdf",
        b"new_file_content",
        content_type="application/pdf",
    )

    # URL for updating the PDF document
    url = reverse("jobs:job_update", kwargs={"pk": job_created_by_bob.pk})

    # POST request to upload new details:
    response = marnie_user_client.post(
        url,
        {
            "date_of_inspection": "2001-02-05",
            "quote": new_pdf,
        },
        follow=True,
    )

    # Assert the response status code is 200
    assert response.status_code == status.HTTP_200_OK

    # Check the redirect chain that leads things up to here:
    assert response.redirect_chain == [
        (f"/jobs/{job_created_by_bob.pk}/", status.HTTP_302_FOUND),
    ]

    # Refresh the Maintenance Job from the database
    job_created_by_bob.refresh_from_db()

    # Check that the status changed as expected
    assert job_created_by_bob.status == Job.Status.INSPECTION_COMPLETED.value
