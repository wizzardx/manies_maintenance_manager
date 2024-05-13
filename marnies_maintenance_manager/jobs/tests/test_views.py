"""Provide tests for job view access control in Marnie's Maintenance Manager."""

# pylint: disable=unused-argument,redefined-outer-name,unused-argument

import pytest
from django.test import Client
from django.urls import reverse
from rest_framework import status

from marnies_maintenance_manager.jobs.models import Job
from marnies_maintenance_manager.jobs.utils import get_sysadmin_email
from marnies_maintenance_manager.users.models import User


@pytest.fixture()
def job_created_by_bob(bob_agent_user: User) -> Job:
    """
    Create a job instance for Bob the agent.

    Args:
        bob_agent_user (User): The User instance representing Bob the agent.

    Returns:
        Job: The job instance created for Bob.

    """
    return Job.objects.create(
        agent=bob_agent_user,
        date="2022-01-01",
        address_details="1234 Main St, Springfield, IL",
        gps_link="https://www.google.com/maps",
        quote_request_details="Replace the kitchen sink",
    )


@pytest.fixture()
def job_created_by_peter(peter_agent_user: User) -> Job:
    """
    Create a job instance for Peter the agent.

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

        """
        response = peter_agent_user_client.get(reverse("jobs:job_list"))
        assert response.status_code == status.HTTP_200_OK

    def test_anonymous_user_cannot_access_job_list_view(self, client: Client) -> None:
        """
        Confirm that anonymous users cannot access the job list view.

        Args:
            client (Client): A test client for an anonymous user.
        """
        response = client.get(reverse("jobs:job_list"))
        assert response.status_code == status.HTTP_302_FOUND  # Redirect

    def test_superuser_can_access_job_list_view(self, superuser_client: Client) -> None:
        """
        Validate that a superuser can access the job list view.

        Args:
            superuser_client (Client): A test client for a superuser.
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
        """
        Bob should only see his own created jobs in the list.

        Args:
            bob_agent_user_client (Client): A test client configured for Bob, an agent
                                            user.
            job_created_by_bob (Job): A job instance created for Bob.
        """
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
        """
        Bob should not see Peter's created jobs in the list.

        Args:
            bob_agent_user_client (Client): A test client configured for Bob, an agent
                                            user.
            job_created_by_bob (Job): A job instance created for Bob.
            job_created_by_peter (Job): A job instance created for Peter, not visible
                                        to Bob.
        """
        # Get page containing list of jobs
        response = bob_agent_user_client.get(reverse("jobs:job_list"))
        # Check that the job created by Peter is not in the list
        assert job_created_by_peter not in response.context["job_list"]


def test_creating_a_new_job_sets_an_agent_from_the_request(
    bob_agent_user_client: Client,
    bob_agent_user: User,
    marnie_user: User,
) -> None:
    """
    Creating a job should automatically assign the agent from the request.

    Args:
        bob_agent_user_client (Client): Client used by Bob, an agent user.
        bob_agent_user (User): Bob's user instance, an agent.
        marnie_user (User): Marnie's user instance, used for validation in this test.
    """
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
    """Ensure only logged-in users can access the job create view."""

    @pytest.mark.django_db()
    def test_anonymous_login_fails_to_access_job_create_view(
        self,
        client: Client,
    ) -> None:
        """
        Verify that anonymous users cannot access the job create view.

        Args:
            client (Client): A test client for an anonymous user.
        """
        response = client.get(reverse("jobs:job_create"))
        assert response.status_code == status.HTTP_302_FOUND

    def test_bob_agent_user_can_access_job_create_view(
        self,
        bob_agent_user_client: Client,
    ) -> None:
        """
        Ensure Bob the agent can access the job create view.

        Args:
            bob_agent_user_client (Client): A test client configured for Bob, an agent
                                            user.
        """
        response = bob_agent_user_client.get(reverse("jobs:job_create"))
        assert response.status_code == status.HTTP_200_OK


class TestMarnieAccessingJobListView:
    """Test Marnie's ability to access and filter job listings."""

    def test_with_agent_username_url_param_filters_by_agent(
        self,
        bob_agent_user: User,
        marnie_user_client: Client,
        job_created_by_bob: Job,
    ) -> None:
        """
        Test filtering job list by agent for Marnie with agent username parameter.

        Args:
            bob_agent_user (User): The agent user Bob whose jobs are to be filtered.
            job_created_by_bob (Job): A job instance created by Bob.
            marnie_user_client (Client): A test client used by Marnie to view the job
                                         list.
        """
        response = marnie_user_client.get(
            reverse("jobs:job_list") + f"?agent={bob_agent_user.username}",
        )
        assert response.status_code == status.HTTP_200_OK
        assert job_created_by_bob in response.context["job_list"]

    def test_without_agent_username_url_param_returns_bad_request_response(
        self,
        marnie_user_client: Client,
        job_created_by_bob: Job,
    ) -> None:
        """
        Check response when no agent username parameter is provided in request.

        Args:
            job_created_by_bob (Job): A job instance created for Bob.
            marnie_user_client (Client): A test client used by Marnie.
        """
        response = marnie_user_client.get(reverse("jobs:job_list"))
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.content.decode() == "Agent username parameter is missing"

    def test_with_nonexistent_agent_username_url_param_returns_not_found(
        self,
        marnie_user_client: Client,
    ) -> None:
        """
        Verify that using a nonexistent agent username returns a 'Not Found' response.

        Args:
            marnie_user_client (Client): A test client used by Marnie.
        """
        response = marnie_user_client.get(
            reverse("jobs:job_list") + "?agent=nonexistent",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.content.decode() == "Agent username not found"


class TestSuperUserAccessingJobListView:
    """Test superusers access to the job list view with different agent parameters."""

    def test_without_agent_username_url_param_returns_all_jobs(
        self,
        superuser_client: Client,
        job_created_by_bob: Job,
        job_created_by_peter: Job,
    ) -> None:
        """
        Ensure a superuser sees all jobs when no agent username is provided.

        Args:
            superuser_client (Client): A test client with superuser permissions.
            job_created_by_bob (Job): A job created by Bob, should be visible.
            job_created_by_peter (Job): A job created by Peter, should be visible.
        """
        response = superuser_client.get(reverse("jobs:job_list"))
        assert response.status_code == status.HTTP_200_OK
        assert job_created_by_bob in response.context["job_list"]
        assert job_created_by_peter in response.context["job_list"]

    def test_with_good_agent_username_url_param_returns_just_the_agents_jobs(
        self,
        superuser_client: Client,
        job_created_by_bob: Job,
        job_created_by_peter: Job,
    ) -> None:
        """
        Test superuser sees only the specified agent's jobs.

        Args:
            superuser_client (Client): A superuser client used to view jobs.
            job_created_by_bob (Job): A job created by Bob, should be visible.
            job_created_by_peter (Job): A job created by Peter, should not be visible
                                        in filter.
        """
        response = superuser_client.get(
            reverse("jobs:job_list") + f"?agent={job_created_by_bob.agent.username}",
        )
        assert response.status_code == status.HTTP_200_OK
        assert job_created_by_bob in response.context["job_list"]
        assert job_created_by_peter not in response.context["job_list"]

    def test_with_nonexistent_agent_username_url_param_returns_bad_request(
        self,
        superuser_client: Client,
    ) -> None:
        """
        Test response when a superuser uses a non-existent agent username.

        Args:
            superuser_client (Client): A test client with superuser permissions.
        """
        response = superuser_client.get(reverse("jobs:job_list") + "?agent=nonexistent")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.content.decode() == "Agent username not found"


class TestJobCreateViewCanOnlyBeReachedByAgentsAndSuperuser:
    """Ensure job create view access is restricted to agents and superusers."""

    @pytest.mark.django_db()
    def test_access_by_anonymous_user_is_denied(self, client: Client) -> None:
        """
        Verify that anonymous users cannot access the job create view.

        Args:
            client (Client): A test client for an anonymous user.
        """
        response = client.get(reverse("jobs:job_create"))
        assert response.status_code == status.HTTP_302_FOUND

    def test_access_by_marnie_user_is_denied(self, marnie_user_client: Client) -> None:
        """
        Test that Marnie cannot access the job create view.

        Args:
            marnie_user_client (Client): A test client configured for Marnie.
        """
        response = marnie_user_client.get(reverse("jobs:job_create"))
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_access_by_bob_agent_user_is_allowed(
        self,
        bob_agent_user_client: Client,
    ) -> None:
        """
        Confirm Bob the agent can access the job create view.

        Args:
            bob_agent_user_client (Client): A test client configured for Bob, an
                                            agent user.
        """
        response = bob_agent_user_client.get(reverse("jobs:job_create"))
        assert response.status_code == status.HTTP_200_OK

    def test_access_by_peter_agent_user_is_allowed(
        self,
        peter_agent_user_client: Client,
    ) -> None:
        """
        Confirm that Peter the agent can access the job create view.

        Args:
            peter_agent_user_client (Client): A test client configured for Peter, an
                                              agent user.
        """
        response = peter_agent_user_client.get(reverse("jobs:job_create"))
        assert response.status_code == status.HTTP_200_OK

    def test_access_by_superuser_user_is_allowed(
        self,
        superuser_client: Client,
    ) -> None:
        """
        Test that a superuser can access the job create view.

        Args:
            superuser_client (Client): A test client with superuser permissions.
        """
        response = superuser_client.get(reverse("jobs:job_create"))
        assert response.status_code == status.HTTP_200_OK


def test_create_job_form_uses_date_type_for_date_input_field(
    bob_agent_user_client: Client,
) -> None:
    """
    Ensure the job create form uses an HTML5 date input for the date field.

    Args:
        bob_agent_user_client (Client): A test client configured for Bob, an agent user.
    """
    response = bob_agent_user_client.get(reverse("jobs:job_create"))
    form = response.context["form"]
    date_widget = form.fields["date"].widget
    assert date_widget.input_type == "date"


class TestAgentCreatingAJobShowsThemFlashMessages:
    """Test that agents see flash messages when creating a job."""

    def test_a_success_flash_message(
        self,
        bob_agent_user_client: Client,
        marnie_user: User,
    ) -> None:
        """
        Ensure agents see a success message when a job is successfully created.

        Args:
            bob_agent_user_client (Client): A test client configured for Bob, an agent
                                            user.
            marnie_user (User): Marnie's user instance, included for context in tests.
        """
        response = bob_agent_user_client.post(
            reverse("jobs:job_create"),
            {
                "date": "2022-01-01",
                "address_details": "1234 Main St, Springfield, IL",
                "gps_link": "https://www.google.com/maps",
                "quote_request_details": "Replace the kitchen sink",
            },
        )
        assert response.status_code == status.HTTP_302_FOUND
        assert response.url == reverse("jobs:job_list")  # type: ignore[attr-defined]
        response = bob_agent_user_client.get(response.url)  # type: ignore[attr-defined]
        messages = list(response.context["messages"])
        assert len(messages) == 1
        assert str(messages[0]) == "Your maintenance request has been sent to Marnie."

    def test_error_flash_when_no_marnie_user_exists(
        self,
        bob_agent_user_client: Client,
        caplog: pytest.LogCaptureFixture,
        superuser_user: User,
    ) -> None:
        """
        Test that agents see an error message when no Marnie user exists.

        Args:
            bob_agent_user_client (Client): A test client for Bob, an agent user.
            caplog (LogCaptureFixture): Pytest fixture to capture log outputs.
            superuser_user (User): A superuser instance used for additional validation.
        """
        response = bob_agent_user_client.post(
            reverse("jobs:job_create"),
            {
                "date": "2022-01-01",
                "address_details": "1234 Main St, Springfield, IL",
                "gps_link": "https://www.google.com/maps",
                "quote_request_details": "Replace the kitchen sink",
            },
        )
        assert response.status_code == status.HTTP_302_FOUND
        assert response.url == reverse("jobs:job_list")  # type: ignore[attr-defined]
        response = bob_agent_user_client.get(response.url)  # type: ignore[attr-defined]
        messages = list(response.context["messages"])
        assert len(messages) == 1
        assert (
            str(messages[0])
            == (
                "No Marnie user found.\n"
                "Unable to send maintenance request.\n"
                "Please contact the system administrator at "
            )
            + get_sysadmin_email()
        )

        # Also check that an error message was logged at the same time
        assert len(caplog.records) == 1
        assert caplog.records[0].levelname == "ERROR"
        assert (
            caplog.records[0].message
            == "No Marnie user found. Unable to send maintenance request email."
        )
