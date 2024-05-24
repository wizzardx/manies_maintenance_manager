"""Tests for the job update view."""

import datetime

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
    response = client.get(
        reverse("jobs:job_update", kwargs={"pk": job_created_by_bob.pk}),
    )
    # This should be a redirect to a login page:
    assert response.status_code == status.HTTP_302_FOUND
    expected_url = f"/accounts/login/?next=/jobs/{job_created_by_bob.id}/update/"
    assert response.url == expected_url  # type: ignore[attr-defined]


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


class TestHasExpectedFields:  # pylint: disable=too-few-public-methods
    """Tests for the job update view to check that it has the expected fields."""

    @staticmethod
    def test_has_date_of_inspection_field(
        job_created_by_bob: Job,
        marnie_user_client: Client,
    ) -> None:
        """Test that the job update page has the 'date_of_inspection' field.

        Args:
            job_created_by_bob (Job): The job created by Bob.
            marnie_user_client (Client): The Django test client for Marnie.
        """
        response = marnie_user_client.post(
            reverse("jobs:job_update", kwargs={"pk": job_created_by_bob.pk}),
            {"date_of_inspection": "2001-02-05"},
            follow=True,
        )
        # Assert the response status code is 200
        assert response.status_code == status.HTTP_200_OK

        # Check the redirect chain that leads things up to here:
        assert response.redirect_chain == [
            (f"/jobs/{job_created_by_bob.pk}/", status.HTTP_302_FOUND),
        ]

        # Refresh the Maintenance Job from the database, and then check the updated
        # # record:
        job_created_by_bob.refresh_from_db()
        assert job_created_by_bob.date_of_inspection == datetime.date(2001, 2, 5)
