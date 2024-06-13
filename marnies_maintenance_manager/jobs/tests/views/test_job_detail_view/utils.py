"""Utility functions for the job detail view tests."""

from bs4 import BeautifulSoup
from django.test import Client
from django.urls import reverse
from rest_framework import status

from marnies_maintenance_manager.jobs.models import Job


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
