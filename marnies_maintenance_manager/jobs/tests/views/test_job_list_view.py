"""Unit tests for the Job list view."""

from typing import cast

# pylint: disable=no-self-use, magic-value-comparison, unused-argument
import pytest
from bs4 import BeautifulSoup
from django.db.models import QuerySet
from django.http import HttpResponse
from django.template.response import TemplateResponse
from django.test import Client
from django.urls import reverse
from rest_framework import status
from typeguard import check_type

from marnies_maintenance_manager.jobs.models import Job
from marnies_maintenance_manager.users.models import User

HTML_FOR_FINAL_PAYMENT_POP_DOWNLOAD_TEMPLATE_START = '<a href="'
HTML_FOR_FINAL_PAYMENT_POP_DOWNLOAD_TEMPLATE_END = '">Download Final Payment POP</a>'

HTML_FOR_FINAL_PAYMENT_POP_DOWNLOAD_TEMPLATE = (
    HTML_FOR_FINAL_PAYMENT_POP_DOWNLOAD_TEMPLATE_START
    + "{url}"
    + HTML_FOR_FINAL_PAYMENT_POP_DOWNLOAD_TEMPLATE_END
)


@pytest.mark.django_db()
class TestOnlySomeUsersCanAccessJobListView:
    """Test access levels to the job list view based on user roles."""

    def test_bob_agent_user_can_access_job_list_view(
        self,
        bob_agent_user_client: Client,
    ) -> None:
        """Verify that agent user 'Bob' can access the job list view.

        Args:
            bob_agent_user_client (Client): A test client for agent user Bob.
        """
        response, _ = get_job_list_response(bob_agent_user_client, "bob")
        assert response.status_code == status.HTTP_200_OK

    def test_alice_agent_user_can_access_job_list_view(
        self,
        alice_agent_user_client: Client,
    ) -> None:
        """Ensure that agent user 'Alice' can access the job list view.

        Args:
            alice_agent_user_client (Client): A test client for agent user Alice.

        """
        response, _ = get_job_list_response(alice_agent_user_client, "alice")
        assert response.status_code == status.HTTP_200_OK

    def test_anonymous_user_cannot_access_job_list_view(self, client: Client) -> None:
        """Confirm that anonymous users cannot access the job list view.

        Args:
            client (Client): A test client for an anonymous user.
        """
        response = client.get(reverse("jobs:job_list"))
        assert response.status_code == status.HTTP_302_FOUND  # Redirect

    def test_superuser_can_access_job_list_view(self, superuser_client: Client) -> None:
        """Validate that a superuser can access the job list view.

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
        """Bob should only see his own created jobs in the list.

        Args:
            bob_agent_user_client (Client): A test client configured for Bob, an agent
                                            user.
            job_created_by_bob (Job): A job instance created for Bob.
        """
        # Get page containing a list of jobs
        _, job_list = get_job_list_response(bob_agent_user_client, "bob")
        # Check that the job created by Bob is in the list
        assert job_created_by_bob in job_list

    def test_bob_agent_cannot_see_jobs_created_by_alice_agent(
        self,
        job_created_by_bob: Job,
        job_created_by_alice: Job,
        bob_agent_user_client: Client,
    ) -> None:
        """Bob should not see Alice's created jobs in the list.

        Args:
            bob_agent_user_client (Client): A test client configured for Bob, an agent
                                            user.
            job_created_by_bob (Job): A job instance created for Bob.
            job_created_by_alice (Job): A job instance created for Alice, not visible
                                        to Bob.
        """
        # Get page containing a list of jobs
        _, job_list = get_job_list_response(bob_agent_user_client, "bob")
        # Check that the job created by Alice is not in the list
        assert job_created_by_alice not in job_list


def check_response_status_and_get_title(
    response: HttpResponse,
    expected_title: str,
) -> BeautifulSoup:
    """Check response status and get the page title using BeautifulSoup.

    Args:
        response (HttpResponse): The response object from the client request.
        expected_title (str): The expected title of the page.

    Returns:
        BeautifulSoup: The BeautifulSoup object for the page.
    """
    assert response.status_code == status.HTTP_200_OK

    page_text = response.content.decode()

    # Use BeautifulSoup to get the title:
    soup = BeautifulSoup(page_text, "html.parser")
    title = soup.find("title")
    assert title is not None

    # Check that the title is as expected
    assert title.text.strip() == expected_title

    return soup


class TestMarnieAccessingJobListView:
    """Test Marnie's ability to access and filter job listings."""

    def test_with_agent_username_url_param_filters_by_agent(
        self,
        bob_agent_user: User,
        marnie_user_client: Client,
        job_created_by_bob: Job,
    ) -> None:
        """Test filtering job list by agent for Marnie with agent username parameter.

        Args:
            bob_agent_user (User): The agent user Bob whose jobs are to be filtered.
            job_created_by_bob (Job): A job instance created by Bob.
            marnie_user_client (Client): A test client used by Marnie to view the job
                                         list.
        """
        _, job_list = get_job_list_response(
            marnie_user_client,
            bob_agent_user.username,
        )
        assert job_created_by_bob in job_list

    def test_without_agent_username_url_param_returns_bad_request_response(
        self,
        marnie_user_client: Client,
        job_created_by_bob: Job,
    ) -> None:
        """Check response when no agent username parameter is provided in request.

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
        """Verif using a nonexistent agent username returns a 'Not Found' response.

        Args:
            marnie_user_client (Client): A test client used by Marnie.
        """
        response = marnie_user_client.get(
            reverse("jobs:job_list") + "?agent=nonexistent",
        )
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.content.decode() == "Agent username not found"

    def test_with_agent_username_url_includes_username_in_title_and_header(
        self,
        bob_agent_user: User,
        marnie_user_client: Client,
    ) -> None:
        """Ensure the agent username is included in the header when filtering by agent.

        Args:
            bob_agent_user (User): The agent user Bob whose jobs are to be filtered.
            marnie_user_client (Client): A test client used by Marnie.
        """
        response = check_type(
            marnie_user_client.get(
                reverse("jobs:job_list") + f"?agent={bob_agent_user.username}",
            ),
            HttpResponse,
        )
        soup = check_response_status_and_get_title(
            response,
            f"Maintenance Jobs for {bob_agent_user.username}",
        )

        # Get the header text:
        header = soup.find("h1")
        assert header is not None

        # Check that its updated correctly for the agent:
        assert header.text == f"Maintenance Jobs for {bob_agent_user.username}"

    def test_without_agent_username_url_does_not_include_username_in_title_and_header(
        self,
        bob_agent_user_client: Client,
    ) -> None:
        """Ensure the title, header, do not include an agent username when not filtered.

        Args:
            bob_agent_user_client (Client): A test client configured for Bob, an agent.
        """
        response = check_type(
            bob_agent_user_client.get(reverse("jobs:job_list")),
            HttpResponse,
        )
        soup = check_response_status_and_get_title(response, "Maintenance Jobs")

        # Get the header text:
        header = soup.find("h1")
        assert header is not None

        # Check that its updated correctly for the agent:
        assert header.text == "Maintenance Jobs"

    def test_create_maintenance_job_button_present_for_agent_but_not_for_marnie(
        self,
        bob_agent_user_client: Client,
        marnie_user_client: Client,
        bob_agent_user: User,
    ) -> None:
        """Ensure the 'Create Maintenance Job' button is only visible to agents.

        Args:
            bob_agent_user_client (Client): A test client configured for Bob, an agent.
            marnie_user_client (Client): A test client configured for Marnie.
            bob_agent_user (User): The agent user Bob.
        """
        expected_text = "Create Maintenance Job"

        # Confirm that the button is present for Bob the Agent:
        response = bob_agent_user_client.get(reverse("jobs:job_list"))
        assert response.status_code == status.HTTP_200_OK, response.content
        assert expected_text in response.content.decode()

        # But that it isn't present for Marnie:
        response = marnie_user_client.get(
            reverse("jobs:job_list") + f"?agent={bob_agent_user.username}",
        )
        assert response.status_code == status.HTTP_200_OK
        assert expected_text not in response.content.decode()

    def test_number_cell_is_a_link_to_the_job_details(  # pylint: disable=too-many-locals
        self,
        job_created_by_bob: Job,
        marnie_user_client: Client,
        bob_agent_user: User,
    ) -> None:
        """Ensure the number cell is a link to the job details page.

        Args:
            job_created_by_bob (Job): A job instance created by Bob.
            marnie_user_client (Client): A test client configured for Marnie.
            bob_agent_user (User): The agent user Bob.
        """
        # The 'job_created_by_bob' fixture gives us the required Job. Now see if
        # Marnie can see a link in the "Number" cell of the table.

        # Start by getting the page:
        response = marnie_user_client.get(
            reverse("jobs:job_list") + f"?agent={bob_agent_user.username}",
        )
        page_text = response.content.decode()

        # Then use BeautifulSoup to find the table in the page:
        soup = BeautifulSoup(page_text, "html.parser")
        table = soup.find("table")

        # Confirm the header row in the table has the expected columns:
        header_row = table.find("tr")
        assert header_row
        header_cells = header_row.find_all("th")
        header_cells_text_list = [cell.text for cell in header_cells]
        assert header_cells_text_list == [
            "Number",
            "Next Actions",
            "Date",
            "Address Details",
            "GPS Link",
            "Quote Request Details",
            "Date of Inspection",
            "Quote",
            "Accept or Reject A/R",
            "Deposit POP",
            "Job Date",
            "Photos",
            "Invoice",
            "Comments on the job",
            "Job Complete",
            "Final Payment POP",
        ]

        # Grab the first row, it contains our Job details:
        first_row = table.find_all("tr")[1]

        # Grab the text from the cells in the row:
        first_row_text_list = [cell.text.strip() for cell in first_row.find_all("td")]

        # Confirm the expected text in the first row:
        expected_row_text_list = [
            "1",
            "Marnie needs to inspect the site and then upload a quote",  # Next Actions
            "2022-01-01",
            "1234 Main St, Springfield, IL",
            "GPS",
            "Replace the kitchen sink",
            "",  # Date of Inspection
            "",  # Quote
            "",  # Accept or Reject A/R
            "",  # Deposit POP
            "",  # Job Date
            "",  # Photos
            "",  # Invoice
            "",  # Comments
            "No",  # Job Complete
            "",  # Final Payment POP
        ]
        assert first_row_text_list == expected_row_text_list

        # Confirm the first cell in the row is a link:
        first_cell = first_row.find_all("td")[0]
        assert first_cell.find("a") is not None

        # Get the actual link:
        link = first_cell.find("a")

        # And check that it has the expected value:
        assert link["href"] == reverse(
            "jobs:job_detail",
            kwargs={"pk": job_created_by_bob.pk},
        )


class TestSuperUserAccessingJobListView:
    """Test superusers access to the job list view with different agent parameters."""

    def test_without_agent_username_url_param_returns_all_jobs(
        self,
        superuser_client: Client,
        job_created_by_bob: Job,
        job_created_by_alice: Job,
    ) -> None:
        """Ensure a superuser sees all jobs when no agent username is provided.

        Args:
            superuser_client (Client): A test client with superuser permissions.
            job_created_by_bob (Job): A job created by Bob
            job_created_by_alice (Job): A job created by Alice
        """
        response = superuser_client.get(reverse("jobs:job_list"))
        assert response.status_code == status.HTTP_200_OK
        assert job_created_by_bob in response.context["job_list"]
        assert job_created_by_alice in response.context["job_list"]

    def test_with_good_agent_username_url_param_returns_just_the_agents_jobs(
        self,
        superuser_client: Client,
        job_created_by_bob: Job,
        job_created_by_alice: Job,
    ) -> None:
        """Test superuser sees only the specified agent's jobs.

        Args:
            superuser_client (Client): A superuser client used to view jobs.
            job_created_by_bob (Job): A job created by Bob
            job_created_by_alice (Job): A job created by Alice
        """
        response = superuser_client.get(
            reverse("jobs:job_list") + f"?agent={job_created_by_bob.agent.username}",
        )
        assert response.status_code == status.HTTP_200_OK
        assert job_created_by_bob in response.context["job_list"]
        assert job_created_by_alice not in response.context["job_list"]

    def test_with_nonexistent_agent_username_url_param_returns_bad_request(
        self,
        superuser_client: Client,
    ) -> None:
        """Test response when a superuser uses a non-existent agent username.

        Args:
            superuser_client (Client): A test client with superuser permissions.
        """
        response = superuser_client.get(reverse("jobs:job_list") + "?agent=nonexistent")
        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.content.decode() == "Agent username not found"


def test_job_list_view_contains_basic_usage_advice(
    superuser_client: Client,
    bob_job_completed_by_marnie: Job,
) -> None:
    """Ensure the job list view contains basic usage advice.

    Args:
        superuser_client (Client): A test client with superuser permissions.
        bob_job_completed_by_marnie (Job): A job created by Marnie.
    """
    response = superuser_client.get(reverse("jobs:job_list"))
    assert response.status_code == status.HTTP_200_OK
    assert (
        "Click on the number in each row to go to the Job details."
        in response.content.decode()
    )


class TestTipShownForMarnieIfThereAreNoJobsListed:
    """Test the message shown to Marnie when no jobs are listed."""

    MESSAGE_TEMPLATE = (
        "There are no Maintenance Jobs for {agent_username}. "
        "{agent_username} needs to log in and create a new "
        "Maintenance Job before anything will appear here."
    )

    def test_msg_not_shown_if_not_marnie(self, bob_agent_user_client: Client) -> None:
        """Ensure the correct message is not shown for Bob when no jobs exist.

        Args:
            bob_agent_user_client (Client): A test client used by Bob.
        """
        response = bob_agent_user_client.get(reverse("jobs:job_list"))
        assert response.status_code == status.HTTP_200_OK
        msg = self.MESSAGE_TEMPLATE.format(agent_username="bob")
        page_text = response.content.decode()
        assert msg not in page_text

    def test_msg_not_shown_if_marnie_and_jobs_exist(
        self,
        marnie_user_client: Client,
        job_created_by_bob: Job,
    ) -> None:
        """Ensure the correct message is not shown for Marnie when jobs exist.

        Args:
            marnie_user_client (Client): A test client used by Marnie.
            job_created_by_bob (Job): A job created by Bob.
        """
        agent_username = job_created_by_bob.agent.username
        msg, page_text = self.get_job_list_for_agent_and_verify_response(
            marnie_user_client,
            agent_username,
        )
        assert msg not in page_text

    def get_job_list_for_agent_and_verify_response(
        self,
        client: Client,
        agent_username: str,
    ) -> tuple[str, str]:
        """Get the job list for an agent and verify the response.

        Args:
            client (Client): A test client.
            agent_username (str): The username of the agent.

        Returns:
            tuple[str, str]: A tuple containing the message and page text.
        """
        response = client.get(
            reverse("jobs:job_list") + f"?agent={agent_username}",
        )
        assert response.status_code == status.HTTP_200_OK
        page_text = response.content.decode()
        msg = self.MESSAGE_TEMPLATE.format(agent_username=agent_username)
        return msg, page_text

    def test_msg_shown_if_marnie_and_no_jobs_exist(
        self,
        marnie_user_client: Client,
        bob_agent_user: User,
    ) -> None:
        """Ensure the correct message is shown for Bob, the agent with no jobs.

        Args:
            marnie_user_client (Client): A test client used by Marnie.
            bob_agent_user (User): The agent user Bob.
        """
        agent_username = bob_agent_user.username
        response = marnie_user_client.get(
            reverse("jobs:job_list") + f"?agent={agent_username}",
        )
        assert response.status_code == status.HTTP_200_OK
        msg = self.MESSAGE_TEMPLATE.format(agent_username=agent_username)
        page_text = response.content.decode()
        assert msg in page_text

    def test_alice_msg_shown_for_alice_agent(
        self,
        marnie_user_client: Client,
        alice_agent_user: User,
    ) -> None:
        """Ensure the correct message is shown for Alice, the other agent.

        Args:
            marnie_user_client (Client): A test client used by Marnie.
            alice_agent_user (User): The agent user Alice.
        """
        agent_username = alice_agent_user.username
        msg, page_text = self.get_job_list_for_agent_and_verify_response(
            marnie_user_client,
            agent_username,
        )
        assert msg in page_text


def test_download_link_is_present_when_final_payment_pop_is_set(
    marnie_user_client: Client,
    bob_job_with_final_payment_pop: Job,
    bob_agent_user: User,
) -> None:
    """Ensure download link is present with final payment proof.

    Args:
        marnie_user_client (Client): A test client used by Marnie.
        bob_job_with_final_payment_pop (Job): A job created by Bob with the final
            payment proof of payment set.
        bob_agent_user (User): The agent user Bob.
    """
    response, _ = get_job_list_response(
        marnie_user_client,
        bob_agent_user.username,
    )
    assert bob_job_with_final_payment_pop.final_payment_pop
    expected_html = HTML_FOR_FINAL_PAYMENT_POP_DOWNLOAD_TEMPLATE.format(
        url=bob_job_with_final_payment_pop.final_payment_pop.url,
    )
    assert expected_html in response.content.decode()


def get_job_list_response(
    client: Client,
    agent_username: str,
) -> tuple[TemplateResponse, QuerySet[Job]]:
    """Get the job list response for an agent.

    Args:
        client (Client): The test client used to make the request.
        agent_username (str): The username of the agent whose job list is requested.

    Returns:
        tuple[TemplateResponse, QuerySet[Job]]: The response object and the job list
            from the response context.
    """
    response = client.get(reverse("jobs:job_list") + f"?agent={agent_username}")
    assert response.status_code == status.HTTP_200_OK
    job_list = response.context["job_list"]
    retval = (response, job_list)
    return cast(tuple[TemplateResponse, QuerySet[Job]], retval)


def test_download_link_is_not_present_when_final_payment_pop_is_not_set(
    marnie_user_client: Client,
    bob_job_completed_by_marnie: Job,
    bob_agent_user: User,
) -> None:
    """Ensure no download link without final payment proof.

    Args:
        marnie_user_client (Client): A test client used by Marnie.
        bob_job_completed_by_marnie (Job): A job created by Bob with the final payment
            proof of payment not set.
        bob_agent_user (User): The agent user Bob.
    """
    response, job_list = get_job_list_response(
        marnie_user_client,
        bob_agent_user.username,
    )
    assert bob_job_completed_by_marnie in job_list
    assert not bob_job_completed_by_marnie.final_payment_pop
    assert (
        HTML_FOR_FINAL_PAYMENT_POP_DOWNLOAD_TEMPLATE_END
        not in response.content.decode()
    )


class TestTipShownForAllUsersIfThereAreAnyJobsListed:
    """Test the message shown to all users when jobs are listed."""

    TIP = "Click on the number in each row to go to the Job details."

    def test_msg_shown_if_there_is_at_least_one_job(
        self,
        marnie_user_client: Client,
        bob_job_completed_by_marnie: Job,
        bob_agent_user: User,
    ) -> None:
        """Ensure the correct message is shown if there is at least one job.

        Args:
            marnie_user_client (Client): A test client used by Marnie.
            bob_job_completed_by_marnie (Job): A job created by Bob and completed by
                Marnie.
            bob_agent_user (User): The agent user Bob.
        """
        response, job_list = get_job_list_response(
            marnie_user_client,
            bob_agent_user.username,
        )
        assert len(job_list) == 1

        page_text = response.content.decode()

        # Check that the tip is there:
        assert self.TIP in page_text

    def test_msg_not_shown_if_there_are_no_jobs(
        self,
        marnie_user_client: Client,
        bob_agent_user: User,
    ) -> None:
        """Ensure the correct message is not shown if there are no jobs.

        Args:
            marnie_user_client (Client): A test client used by Marnie.
            bob_agent_user (User): The agent user Bob.
        """
        response, job_list = get_job_list_response(
            marnie_user_client,
            bob_agent_user.username,
        )
        assert len(job_list) == 0

        page_text = response.content.decode()

        # Check that the tip is there:
        assert self.TIP not in page_text
