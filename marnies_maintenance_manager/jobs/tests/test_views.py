"""Provide tests for job view access control in Marnie's Maintenance Manager."""

import pytest
from django.test import Client
from django.urls import reverse
from rest_framework import status


@pytest.mark.django_db()
class TestOnlyAgentUsersCanAccessJobListView:
    """Test access levels to the job list view based on user roles."""

    def test_bob_agent_user_can_access_job_list_view(
        self,
        bob_agent_user_client: Client,
    ) -> None:
        """
        Verify that agent user 'Bob' can access the job list view.

        Args:
            bob_agent_user_client (Client): A test client for agent user Bob.

        Returns:
            None
        """
        response = bob_agent_user_client.get(reverse("jobs:job_list"))
        assert response.status_code == status.HTTP_200_OK

    def test_peter_agent_user_can_access_job_list_view(
        self,
        peter_agent_user_client: Client,
    ) -> None:
        """
        Ensure that agent user 'Peter' can access the job list view.

        Args:
            peter_agent_user_client (Client): A test client for agent user Peter.

        Returns:
            None
        """
        response = peter_agent_user_client.get(reverse("jobs:job_list"))
        assert response.status_code == status.HTTP_200_OK

    def test_anonymous_user_cannot_access_job_list_view(self, client: Client) -> None:
        """
        Confirm that anonymous users cannot access the job list view.

        Args:
            client (Client): A test client for an anonymous user.

        Returns:
            None
        """
        response = client.get(reverse("jobs:job_list"))
        assert response.status_code == status.HTTP_302_FOUND  # Redirect

    def test_marnie_user_cannot_access_job_list_view(
        self,
        marnie_user_client: Client,
    ) -> None:
        """
        Check that user 'Marnie' cannot access the job list view.

        Args:
            marnie_user_client (Client): A test client for user Marnie.

        Returns:
            None
        """
        response = marnie_user_client.get(reverse("jobs:job_list"))
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_superuser_can_access_job_list_view(self, superuser_client: Client) -> None:
        """
        Validate that a superuser can access the job list view.

        Args:
            superuser_client (Client): A test client for a superuser.

        Returns:
            None
        """
        response = superuser_client.get(reverse("jobs:job_list"))
        assert response.status_code == status.HTTP_200_OK
