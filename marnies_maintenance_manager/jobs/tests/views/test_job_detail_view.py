"""Tests for the job detail view."""

# pylint: disable=no-self-use

from django.test import Client
from django.urls import reverse
from rest_framework import status

from marnies_maintenance_manager.jobs.models import Job

from .utils import check_basic_page_html_structure


class TestAbilityToReachJobDetailView:
    """Tests to ensure that users job detail view is correctly restricted."""

    def test_anonymous_user_cannot_access_job_detail_views(
        self,
        client: Client,
        job_created_by_bob: Job,
    ) -> None:
        """Ensure that an anonymous user cannot access the job detail view.

        Args:
            client (Client): The Django test client.
            job_created_by_bob (Job): The job created by Bob.
        """
        response = client.get(
            reverse("jobs:job_detail", kwargs={"pk": job_created_by_bob.pk}),
        )
        assert response.status_code == status.HTTP_302_FOUND

    def test_agent_users_cannot_access_job_detail_views(
        self,
        bob_agent_user_client: Client,
        job_created_by_bob: Job,
    ) -> None:
        """Ensure that an agent user cannot access the job detail view.

        Args:
            bob_agent_user_client (Client): The Django test client for Bob.
            job_created_by_bob (Job): The job created by Bob.
        """
        response = bob_agent_user_client.get(
            reverse("jobs:job_detail", kwargs={"pk": job_created_by_bob.pk}),
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_marnie_user_can_access_job_detail_view(
        self,
        marnie_user_client: Client,
        job_created_by_bob: Job,
    ) -> None:
        """Ensure Marnie can access the job detail view.

        Args:
            marnie_user_client (Client): The Django test client for Marnie.
            job_created_by_bob (Job): The job created by Bob.
        """
        response = marnie_user_client.get(
            reverse("jobs:job_detail", kwargs={"pk": job_created_by_bob.pk}),
        )
        assert response.status_code == status.HTTP_200_OK


def test_job_detail_view_has_correct_basic_structure(
    job_created_by_bob: Job,
    marnie_user_client: Client,
) -> None:
    """Ensure that the job detail view has the correct basic structure.

    Args:
        job_created_by_bob (Job): The job created by Bob.
        marnie_user_client (Client): The Django test client for Marnie.
    """
    check_basic_page_html_structure(
        client=marnie_user_client,
        url=reverse("jobs:job_detail", kwargs={"pk": job_created_by_bob.pk}),
        expected_title="Maintenance Job Details",
        expected_template_name="jobs/job_detail.html",
        expected_h1_text="Maintenance Job Details",
        expected_func_name="view",
        expected_url_name="job_detail",
        expected_view_class=None,
    )
