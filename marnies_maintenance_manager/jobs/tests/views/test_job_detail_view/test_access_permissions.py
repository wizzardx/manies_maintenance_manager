"""Tests for access permissions in the job detail view.

This module contains tests to ensure that different types of users have the correct
permissions when attempting to access the job detail view.
"""

from django.test import Client
from django.urls import reverse
from rest_framework import status

from marnies_maintenance_manager.jobs.models import Job


class TestAbilityToReachJobDetailView:
    """Tests to ensure that users job detail view is correctly restricted."""

    @staticmethod
    def test_anonymous_user_cannot_access_job_detail_views(
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

    @staticmethod
    def test_agent_users_can_access_detail_view_for_job_they_created(
        bob_agent_user_client: Client,
        job_created_by_bob: Job,
    ) -> None:
        """Ensure Bob can access the job detail view for the job he created.

        Args:
            bob_agent_user_client (Client): The Django test client for Bob.
            job_created_by_bob (Job): The job created by Bob.
        """
        response = bob_agent_user_client.get(
            reverse("jobs:job_detail", kwargs={"pk": job_created_by_bob.pk}),
        )
        assert response.status_code == status.HTTP_200_OK

    @staticmethod
    def test_agent_users_cannot_access_detail_view_for_jobs_they_did_not_create(
        bob_agent_user_client: Client,
        job_created_by_alice: Job,
    ) -> None:
        """Ensure Bob cannot access the job detail view for the job Alice created.

        Args:
            bob_agent_user_client (Client): The Django test client for Bob.
            job_created_by_alice (Job): The job created by Alice.
        """
        response = bob_agent_user_client.get(
            reverse("jobs:job_detail", kwargs={"pk": job_created_by_alice.pk}),
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @staticmethod
    def test_marnie_user_can_access_job_detail_view(
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

    @staticmethod
    def test_admin_user_can_access_job_detail_view(
        admin_client: Client,
        job_created_by_bob: Job,
    ) -> None:
        """Ensure the admin user can access the job detail view.

        Args:
            admin_client (Client): The Django test client for the admin user.
            job_created_by_bob (Job): The job created by Bob.
        """
        response = admin_client.get(
            reverse("jobs:job_detail", kwargs={"pk": job_created_by_bob.pk}),
        )
        assert response.status_code == status.HTTP_200_OK
