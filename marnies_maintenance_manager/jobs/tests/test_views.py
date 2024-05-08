"""Provide tests for job view access control in Marnie's Maintenance Manager."""

import pytest
from django.test import Client
from django.urls import reverse
from rest_framework import status

from marnies_maintenance_manager.jobs.models import Job
from marnies_maintenance_manager.users.models import User


@pytest.fixture()
def job_created_by_bob(bob_agent_user: User) -> Job:
    """Create a job instance for Bob the agent."""
    return Job.objects.create(
        agent=bob_agent_user,
        date="2022-01-01",
        address_details="1234 Main St, Springfield, IL",
        gps_link="https://www.google.com/maps",
        quote_request_details="Replace the kitchen sink",
    )


@pytest.fixture()
def job_created_by_peter(peter_agent_user: User) -> Job:
    """Create a job instance for Peter the agent."""
    return Job.objects.create(
        agent=peter_agent_user,
        date="2022-01-01",
        address_details="1234 Main St, Springfield, IL",
        gps_link="https://www.google.com/maps",
        quote_request_details="Replace the kitchen sink",
    )


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


class TestAgentsAccessingJobListViewCanOnlySeeJobsThatTheyCreated:
    """Ensure agents only see their own jobs in the list view."""

    def test_bob_agent_can_see_their_own_created_jobs(
        self,
        job_created_by_bob: Job,
        bob_agent_user_client: Client,
    ) -> None:
        """Bob should only see his own created jobs in the list."""
        # Get page containing list of jobs
        response = bob_agent_user_client.get(reverse("jobs:job_list"))
        # Check that the job created by Bob is in the list
        assert job_created_by_bob in response.context["job_list"]

    def test_bob_agent_cannot_see_jobs_created_by_peter_agent(
        self,
        job_created_by_bob: Job,
        job_created_by_peter: Job,
        bob_agent_user_client: Client,
    ) -> None:
        """Bob should not see Peter's created jobs in the list."""
        # Get page containing list of jobs
        response = bob_agent_user_client.get(reverse("jobs:job_list"))
        # Check that the job created by Peter is not in the list
        assert job_created_by_peter not in response.context["job_list"]


def test_creating_a_new_job_sets_an_agent_from_the_request(
    bob_agent_user_client: Client,
    bob_agent_user: User,
) -> None:
    """Creating a job should automatically assign the agent from the request."""
    client = bob_agent_user_client
    response = client.post(
        reverse("jobs:job_create"),
        {
            "date": "2022-01-01",
            "address_details": "1234 Main St, Springfield, IL",
            "gps_link": "https://www.google.com/maps",
            "quote_request_details": "Replace the kitchen sink",
        },
    )
    assert response.status_code == status.HTTP_302_FOUND
    job = Job.objects.first()
    assert job is not None
    assert job.agent == bob_agent_user


class TestOnlyLoggedInUsersCanAccessJobCreateView:
    """Test access control for the job create view."""

    @pytest.mark.django_db()
    def test_anonymous_login_fails_to_access_job_create_view(
        self,
        client: Client,
    ) -> None:
        """Anonymous users should not be able to access the job create view."""
        response = client.get(reverse("jobs:job_create"))
        assert response.status_code == status.HTTP_302_FOUND

    def test_bob_agent_user_can_access_job_create_view(
        self,
        bob_agent_user_client: Client,
    ) -> None:
        """Bob the agent should be able to access the job create view."""
        response = bob_agent_user_client.get(reverse("jobs:job_create"))
        assert response.status_code == status.HTTP_200_OK
