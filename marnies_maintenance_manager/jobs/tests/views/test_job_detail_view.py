"""Tests for the job detail view."""

# pylint: disable=no-self-use
import datetime
from typing import cast

from bs4 import BeautifulSoup
from django.http import HttpResponseRedirect
from django.test import Client
from django.urls import reverse
from rest_framework import status

from marnies_maintenance_manager.jobs.models import Job

from .utils import check_basic_page_html_structure


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
        job_created_by_peter: Job,
    ) -> None:
        """Ensure Bob cannot access the job detail view for the job Peter created.

        Args:
            bob_agent_user_client (Client): The Django test client for Bob.
            job_created_by_peter (Job): The job created by Peter.
        """
        response = bob_agent_user_client.get(
            reverse("jobs:job_detail", kwargs={"pk": job_created_by_peter.pk}),
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


def test_job_detail_view_shows_expected_job_details(
    bob_job_with_initial_marnie_inspection: Job,
    marnie_user_client: Client,
) -> None:
    """Ensure that the job detail view shows the expected job details.

    Args:
        bob_job_with_initial_marnie_inspection (Job): The job created by Bob with the
            initial inspection done by Marnie.
        marnie_user_client (Client): The Django test client for Marnie.
    """
    job = bob_job_with_initial_marnie_inspection
    response = marnie_user_client.get(
        reverse("jobs:job_detail", kwargs={"pk": job.pk}),
    )
    page = response.content.decode("utf-8")

    # We search for a more complete html fragment for job number, because job number
    # is just going to be the numeric "1" at this point in the test, so we want
    # something more unique to search for.
    assert f"<strong>Number:</strong> {job.number}" in page
    assert job.date.strftime("%Y-%m-%d") in page
    assert job.address_details in page
    assert job.gps_link in page
    assert job.quote_request_details in page

    inspect_date = job.date_of_inspection
    assert isinstance(inspect_date, datetime.date)
    assert inspect_date.isoformat() in page

    assert job.get_quote_download_url() in page


def _get_update_link_or_none(job: Job, user_client: Client) -> BeautifulSoup | None:
    """Get the link to the job update view, or None if it couldn't be found.

    Args:
        job (Job): The job to get the update link for.
        user_client (Client): The Django test client for the user.

    Returns:
        BeautifulSoup | None: The link to the job update view, or None if it couldn't
    """
    response = user_client.get(
        reverse("jobs:job_detail", kwargs={"pk": job.pk}),
    )
    assert response.status_code == status.HTTP_200_OK
    page = response.content.decode("utf-8")

    # Use Python BeautifulSoup to parse the HTML and find the link
    # to the job update view.
    soup = BeautifulSoup(page, "html.parser")

    # Get the link with the text "Update", using BeautifulSoup (or None, if it
    # couldn't be found), and return that.
    return soup.find("a", string="Update")


class TestUpdateLinkVisibility:
    """Tests to ensure that the update link is visible to the correct users."""

    @staticmethod
    def test_page_has_update_link_going_to_update_view(
        job_created_by_bob: Job,
        marnie_user_client: Client,
    ) -> None:
        """Ensure that the job detail page has a link to the update view.

        Args:
            job_created_by_bob (Job): The job created by Bob.
            marnie_user_client (Client): The Django test client for Marnie.
        """
        link = _get_update_link_or_none(job_created_by_bob, marnie_user_client)
        assert link is not None

        # Confirm that the link goes to the correct URL.
        expected_url = reverse("jobs:job_update", kwargs={"pk": job_created_by_bob.pk})
        assert link["href"] == expected_url

    @staticmethod
    def test_update_link_is_visible_for_admin(
        job_created_by_bob: Job,
        admin_client: Client,
    ) -> None:
        """Ensure that the job detail page shows the update link to the admin user.

        Args:
            job_created_by_bob (Job): The job created by Bob.
            admin_client (Client): The Django test client for the admin user.
        """
        link = _get_update_link_or_none(job_created_by_bob, admin_client)
        assert link is not None

    @staticmethod
    def test_update_link_is_not_visible_for_agent(
        job_created_by_bob: Job,
        bob_agent_user_client: Client,
    ) -> None:
        """Ensure that the job detail page does not show the update link to agents.

        Args:
            job_created_by_bob (Job): The job created by Bob.
            bob_agent_user_client (Client): The Django test client for Bob.
        """
        response = bob_agent_user_client.get(
            reverse("jobs:job_detail", kwargs={"pk": job_created_by_bob.pk}),
        )
        assert response.status_code == status.HTTP_200_OK
        page = response.content.decode("utf-8")

        # Use Python BeautifulSoup to parse the HTML and find the link
        # to the job update view.
        soup = BeautifulSoup(page, "html.parser")

        # Check with BeautifulSoup that the link is not present.
        link = soup.find("a", string="Update")
        assert link is None

    @staticmethod
    def test_update_link_is_not_visible_to_marnie_after_he_has_done_initial_inspection(
        bob_job_with_initial_marnie_inspection: Job,
        marnie_user_client: Client,
    ) -> None:
        """Ensure Marnie can't see the update link after completing initial inspection.

        Args:
            bob_job_with_initial_marnie_inspection (Job): The job created by Bob with
                the initial inspection done by Marnie.
            marnie_user_client (Client): The Django test client for Marnie.
        """
        response = marnie_user_client.get(
            reverse(
                "jobs:job_detail",
                kwargs={"pk": bob_job_with_initial_marnie_inspection.pk},
            ),
        )
        assert response.status_code == status.HTTP_200_OK
        page = response.content.decode("utf-8")

        # Use Python BeautifulSoup to parse the HTML and find the link with the text
        # "Update"
        soup = BeautifulSoup(page, "html.parser")
        link = soup.find("a", string="Update")

        # Confirm that we couldn't find it:
        assert (
            link is None
        ), "The link to update the job should not be visible to Marnie."


def _ensure_can_see_link(user_client: Client, job: Job) -> None:
    """Ensure that the quote download link is visible to the user.

    Args:
        user_client (Client): The Django test client for the user.
        job (Job): The job to check for the quote download link.
    """
    response = user_client.get(
        reverse(
            "jobs:job_detail",
            kwargs={"pk": job.pk},
        ),
    )
    assert response.status_code == status.HTTP_200_OK
    page = response.content.decode("utf-8")

    # Use Python BeautifulSoup to parse the HTML and find the link
    # to download the quote.
    soup = BeautifulSoup(page, "html.parser")
    link = soup.find("a", string="Download Quote")
    assert link is not None

    # Confirm that the link goes to the correct URL.
    expected_url = reverse(
        "jobs:download_quote",
        kwargs={"pk": job.pk},
    )
    assert link["href"] == expected_url


class TestQuoteDownloadLinkVisibility:
    """Tests to ensure that the quote download link is visible to the correct users."""

    @staticmethod
    def test_marnie_can_see_link(
        bob_job_with_initial_marnie_inspection: Job,
        marnie_user_client: Client,
    ) -> None:
        """Ensure that Marnie can see the quote download link.

        Args:
            bob_job_with_initial_marnie_inspection (Job): The job created by Bob with
                the initial inspection done by Marnie.
            marnie_user_client (Client): The Django test client for Marnie.
        """
        _ensure_can_see_link(marnie_user_client, bob_job_with_initial_marnie_inspection)

    @staticmethod
    def test_admin_can_see_link(
        bob_job_with_initial_marnie_inspection: Job,
        admin_client: Client,
    ) -> None:
        """Ensure that the admin user can see the quote download link.

        Args:
            bob_job_with_initial_marnie_inspection (Job): The job created by Bob.
            admin_client (Client): The Django test client for the admin user.
        """
        _ensure_can_see_link(admin_client, bob_job_with_initial_marnie_inspection)

    @staticmethod
    def test_agent_who_created_job_can_see_link(
        bob_job_with_initial_marnie_inspection: Job,
        bob_agent_user_client: Client,
    ) -> None:
        """Ensure that the agent who created the job can see the quote download link.

        Args:
            bob_job_with_initial_marnie_inspection (Job): The job created by Bob.
            bob_agent_user_client (Client): The Django test client for Bob.
        """
        _ensure_can_see_link(
            bob_agent_user_client,
            bob_job_with_initial_marnie_inspection,
        )

    @staticmethod
    def test_agent_who_did_not_create_job_cannot_reach_page_to_see_link(
        bob_job_with_initial_marnie_inspection: Job,
        peter_agent_user_client: Client,
    ) -> None:
        """Ensure agents who didn't create the job can't see the quote link.

        Args:
            bob_job_with_initial_marnie_inspection (Job): The job created by Bob.
            peter_agent_user_client (Client): The Django test client for Peter.
        """
        response = peter_agent_user_client.get(
            reverse(
                "jobs:job_detail",
                kwargs={"pk": bob_job_with_initial_marnie_inspection.pk},
            ),
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    @staticmethod
    def test_anonymous_user_cannot_reach_page_to_see_link(
        bob_job_with_initial_marnie_inspection: Job,
        client: Client,
    ) -> None:
        """Ensure that an anonymous user cannot access the job detail view.

        Args:
            bob_job_with_initial_marnie_inspection (Job): The job created by Bob.
            client (Client): The Django test client.
        """
        response = client.get(
            reverse(
                "jobs:job_detail",
                kwargs={"pk": bob_job_with_initial_marnie_inspection.pk},
            ),
        )
        assert response.status_code == status.HTTP_302_FOUND

        # Check that the user is redirected to the login page.
        response2 = cast(HttpResponseRedirect, response)
        assert (
            response2.url == "/accounts/login/?next=/jobs/"
            f"{bob_job_with_initial_marnie_inspection.pk}/"
        )


def _get_refuse_quote_button_or_none(
    job: Job,
    user_client: Client,
) -> BeautifulSoup | None:
    """Get the refuse quote button, or None if it couldn't be found.

    Args:
        job (Job): The job to get the refuse quote button for.
        user_client (Client): The Django test client for the user.

    Returns:
        BeautifulSoup | None: The refuse quote button, or None if it couldn't be found.
    """
    response = user_client.get(
        reverse("jobs:job_detail", kwargs={"pk": job.pk}),
    )
    assert response.status_code == status.HTTP_200_OK
    page = response.content.decode("utf-8")

    # Use Python BeautifulSoup to parse the HTML and find the button
    # to refuse the quote.
    soup = BeautifulSoup(page, "html.parser")
    return soup.find("button", string="Refuse Quote")


class TestRefuseQuoteButtonVisibility:
    """Tests to ensure that the refuse quote button is visible to the correct users."""

    @staticmethod
    def test_agent_can_see_refuse_quote_button_when_marnie_has_done_initial_inspection(
        bob_job_with_initial_marnie_inspection: Job,
        bob_agent_user_client: Client,
    ) -> None:
        """Ensure agent sees refuse quote button when Marnie has done the inspection.

        Args:
            bob_job_with_initial_marnie_inspection (Job): The job created by Bob with
                the initial inspection done by Marnie.
            bob_agent_user_client (Client): The Django test client for Bob.
        """
        button = _get_refuse_quote_button_or_none(
            bob_job_with_initial_marnie_inspection,
            bob_agent_user_client,
        )
        assert button is not None

    def test_button_not_visible_when_marnie_has_not_done_initial_inspection(
        self,
        job_created_by_bob: Job,
        bob_agent_user_client: Client,
    ) -> None:
        """Ensure the refuse quote button is hidden if Marnie hasn't done inspection.

        Args:
            job_created_by_bob (Job): The job created by Bob.
            bob_agent_user_client (Client): The Django test client for Bob.
        """
        button = _get_refuse_quote_button_or_none(
            job_created_by_bob,
            bob_agent_user_client,
        )
        assert button is None

    def test_marnie_cannot_see_refuse_quote_button_after_doing_initial_inspection(
        self,
        bob_job_with_initial_marnie_inspection: Job,
        marnie_user_client: Client,
    ) -> None:
        """Ensure Marnie can't see the refuse quote button after the initial inspection.

        Args:
            bob_job_with_initial_marnie_inspection (Job): The job created by Bob with
                the initial inspection done by Marnie.
            marnie_user_client (Client): The Django test client for Marnie.
        """
        button = _get_refuse_quote_button_or_none(
            bob_job_with_initial_marnie_inspection,
            marnie_user_client,
        )
        assert button is None

    def test_another_agent_cannot_reach_page_to_see_quote_button(
        self,
        bob_job_with_initial_marnie_inspection: Job,
        peter_agent_user_client: Client,
    ) -> None:
        """Ensure agents who didn't create the job can't access the detail page.

        Args:
            bob_job_with_initial_marnie_inspection (Job): The job created by Bob with
                the initial inspection done by Marnie.
            peter_agent_user_client (Client): The Django test client for Peter.
        """
        response = peter_agent_user_client.get(
            reverse(
                "jobs:job_detail",
                kwargs={"pk": bob_job_with_initial_marnie_inspection.pk},
            ),
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_see_refuse_quote_button(
        self,
        bob_job_with_initial_marnie_inspection: Job,
        admin_client: Client,
    ) -> None:
        """Ensure that the admin user can see the refuse quote button.

        Args:
            bob_job_with_initial_marnie_inspection (Job): The job created by Bob with
                the initial inspection done by Marnie.
            admin_client (Client): The Django test client for the admin user.
        """
        button = _get_refuse_quote_button_or_none(
            bob_job_with_initial_marnie_inspection,
            admin_client,
        )
        assert button is not None

    def test_anonymous_user_is_redirected_to_login_page(
        self,
        bob_job_with_initial_marnie_inspection: Job,
        client: Client,
    ) -> None:
        """Ensure that an anonymous user cannot access the job detail view.

        Args:
            bob_job_with_initial_marnie_inspection (Job): The job created by Bob with
                the initial inspection done by Marnie.
            client (Client): The Django test client.
        """
        response = client.get(
            reverse(
                "jobs:job_detail",
                kwargs={"pk": bob_job_with_initial_marnie_inspection.pk},
            ),
        )
        assert response.status_code == status.HTTP_302_FOUND

        # Check that the user is redirected to the login page.
        response2 = cast(HttpResponseRedirect, response)
        assert (
            response2.url == "/accounts/login/?next=/jobs/"
            f"{bob_job_with_initial_marnie_inspection.pk}/"
        )

    def test_visible_when_quote_refused_by_agent(
        self,
        job_refused_by_bob: Job,
        bob_agent_user_client: Client,
    ) -> None:
        """Ensure the refuse quote button is visible when the agent refuses the quote.

        Args:
            job_refused_by_bob (Job): The job created by Bob with the quote refused by
                the agent.
            bob_agent_user_client (Client): The Django test client for Bob.
        """
        button = _get_refuse_quote_button_or_none(
            job_refused_by_bob,
            bob_agent_user_client,
        )
        assert button is not None


class TestAcceptQuoteButtonVisibility:
    """Tests to ensure that the accept quote button is visible to the correct users."""

    def test_agent_can_see_accept_quote_button_when_marnie_has_done_initial_inspection(
        self,
        bob_job_with_initial_marnie_inspection: Job,
        bob_agent_user_client: Client,
    ) -> None:
        """Ensure agent sees accept quote button when Marnie has done the inspection.

        Args:
            bob_job_with_initial_marnie_inspection (Job): The job created by Bob with
                the initial inspection done by Marnie.
            bob_agent_user_client (Client): The Django test client for Bob.
        """
        button = _get_accept_quote_button_or_none(
            bob_job_with_initial_marnie_inspection,
            bob_agent_user_client,
        )
        assert button is not None

    def test_button_not_visible_when_marnie_has_not_done_initial_inspection(
        self,
        job_created_by_bob: Job,
        bob_agent_user_client: Client,
    ) -> None:
        """Ensure the accept quote button is hidden if Marnie hasn't done inspection.

        Args:
            job_created_by_bob (Job): The job created by Bob.
            bob_agent_user_client (Client): The Django test client for Bob.
        """
        button = _get_accept_quote_button_or_none(
            job_created_by_bob,
            bob_agent_user_client,
        )
        assert button is None

    def test_marnie_cannot_see_accept_quote_button_after_doing_initial_inspection(
        self,
        bob_job_with_initial_marnie_inspection: Job,
        marnie_user_client: Client,
    ) -> None:
        """Ensure Marnie can't see the accept quote button after the initial inspection.

        Args:
            bob_job_with_initial_marnie_inspection (Job): The job created by Bob with
                the initial inspection done by Marnie.
            marnie_user_client (Client): The Django test client for Marnie.
        """
        button = _get_accept_quote_button_or_none(
            bob_job_with_initial_marnie_inspection,
            marnie_user_client,
        )
        assert button is None

    def test_another_agent_cannot_reach_page_to_see_quote_button(
        self,
        bob_job_with_initial_marnie_inspection: Job,
        peter_agent_user_client: Client,
    ) -> None:
        """Ensure agents who didn't create the job can't access the detail page.

        Args:
            bob_job_with_initial_marnie_inspection (Job): The job created by Bob with
                the initial inspection done by Marnie.
            peter_agent_user_client (Client): The Django test client for Peter.
        """
        response = peter_agent_user_client.get(
            reverse(
                "jobs:job_detail",
                kwargs={"pk": bob_job_with_initial_marnie_inspection.pk},
            ),
        )
        assert response.status_code == status.HTTP_403_FORBIDDEN

    def test_admin_can_see_accept_quote_button(
        self,
        bob_job_with_initial_marnie_inspection: Job,
        admin_client: Client,
    ) -> None:
        """Ensure that the admin user can see the accept quote button.

        Args:
            bob_job_with_initial_marnie_inspection (Job): The job created by Bob with
                the initial inspection done by Marnie.
            admin_client (Client): The Django test client for the admin user.
        """
        button = _get_accept_quote_button_or_none(
            bob_job_with_initial_marnie_inspection,
            admin_client,
        )
        assert button is not None

    def test_anonymous_user_is_redirected_to_login_page(
        self,
        bob_job_with_initial_marnie_inspection: Job,
        client: Client,
    ) -> None:
        """Ensure that an anonymous user cannot access the job detail view.

        Args:
            bob_job_with_initial_marnie_inspection (Job): The job created by Bob with
                the initial inspection done by Marnie.
            client (Client): The Django test client.
        """
        response = client.get(
            reverse(
                "jobs:job_detail",
                kwargs={"pk": bob_job_with_initial_marnie_inspection.pk},
            ),
        )
        assert response.status_code == status.HTTP_302_FOUND

        # Check that the user is redirected to the login page.
        response2 = cast(HttpResponseRedirect, response)
        assert (
            response2.url == "/accounts/login/?next=/jobs/"
            f"{bob_job_with_initial_marnie_inspection.pk}/"
        )


def _get_accept_quote_button_or_none(
    job: Job,
    user_client: Client,
) -> BeautifulSoup | None:
    """Get the accept quote button, or None if it couldn't be found.

    Args:
        job (Job): The job to get the accept quote button for.
        user_client (Client): The Django test client for the user.

    Returns:
        BeautifulSoup | None: The accept quote button, or None if it couldn't be found.
    """
    response = user_client.get(
        reverse("jobs:job_detail", kwargs={"pk": job.pk}),
    )
    assert response.status_code == status.HTTP_200_OK
    page = response.content.decode("utf-8")

    # Use Python BeautifulSoup to parse the HTML and find the button
    # to accept the quote.
    soup = BeautifulSoup(page, "html.parser")
    return soup.find("button", string="Accept Quote")
