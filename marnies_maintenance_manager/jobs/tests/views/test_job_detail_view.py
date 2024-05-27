"""Tests for the job detail view."""

# pylint: disable=no-self-use

import pytest
from bs4 import BeautifulSoup
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

    def test_agent_users_can_access_detail_view_for_job_they_created(
        self,
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

    def test_agent_users_cannot_access_detail_view_for_jobs_they_did_not_create(
        self,
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


def test_job_detail_view_shows_expected_job_details(
    job_created_by_bob: Job,
    marnie_user_client: Client,
) -> None:
    """Ensure that the job detail view shows the expected job details.

    Args:
        job_created_by_bob (Job): The job created by Bob.
        marnie_user_client (Client): The Django test client for Marnie.
    """
    response = marnie_user_client.get(
        reverse("jobs:job_detail", kwargs={"pk": job_created_by_bob.pk}),
    )
    page = response.content.decode("utf-8")
    job = job_created_by_bob

    # We search for a more complete html fragment for job number, because job number
    # is just going to be the numeric "1" at this point in the test, so we want
    # something more unique to search for.
    assert f"<strong>Number:</strong> {job.number}" in page
    assert job.date.strftime("%Y-%m-%d") in page
    assert job.address_details in page
    assert job.gps_link in page
    assert job.quote_request_details in page


def test_page_has_update_link_going_to_update_view(
    job_created_by_bob: Job,
    marnie_user_client: Client,
) -> None:
    """Ensure that the job detail page has a link to the update view.

    Args:
        job_created_by_bob (Job): The job created by Bob.
        marnie_user_client (Client): The Django test client for Marnie.
    """
    response = marnie_user_client.get(
        reverse("jobs:job_detail", kwargs={"pk": job_created_by_bob.pk}),
    )
    assert response.status_code == status.HTTP_200_OK
    page = response.content.decode("utf-8")

    # Use Python BeautifulSoup to parse the HTML and find the link
    # to the job update view.
    soup = BeautifulSoup(page, "html.parser")

    # Get the link with the text "Update", using BeautifulSoup.
    link = soup.find("a", string="Update")
    assert link is not None

    # Confirm that the link goes to the correct URL.
    expected_url = reverse("jobs:job_update", kwargs={"pk": job_created_by_bob.pk})
    assert link["href"] == expected_url


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


@pytest.fixture()
def bob_job_with_initial_marnie_inspection(
    job_created_by_bob,
    marnie_user_client,
    bob_job_update_url,
    test_pdf,
) -> Job:
    """Create a job with the initial inspection done by Marnie.

    Args:
        job_created_by_bob (Job): The job created by Bob.
        marnie_user_client (Client): The Django test client for Marnie.
        bob_job_update_url (str): The URL for the job update view for the job created
            by Bob.
        test_pdf (SimpleUploadedFile): The test PDF file.

    """
    job = job_created_by_bob

    # Check that the Job is in the correct initial state:
    assert job.status == Job.Status.PENDING_INSPECTION.value

    response = marnie_user_client.post(
        bob_job_update_url,
        {
            "date_of_inspection": "2001-02-05",
            "quote": test_pdf,
        },
        follow=True,
    )
    # Assert the response status code is 200
    assert response.status_code == status.HTTP_200_OK

    # Check that the job is in the correct state after inspection:
    job = Job.objects.get(pk=job.pk)
    assert job.status == Job.Status.INSPECTION_COMPLETED.value

    # Return the Job where Marnie has now inspected the site.
    return job


def test_update_link_is_not_visible_to_marnie_after_he_has_done_initial_inspection(
    bob_job_with_initial_marnie_inspection: Job,
    marnie_user_client: Client,
) -> None:
    """Ensure Marnie can't see the update link after completing initial inspection.

    Args:
        bob_job_with_initial_marnie_inspection (Job): The job created by Bob with the
            initial inspection done by Marnie.
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
    assert link is None, "The link to update the job should not be visible to Marnie."
