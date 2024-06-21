"""Tests for the basic structure and content of the job detail view.

This module contains tests to verify that the job detail view has the correct
HTML structure and displays the expected job details.
"""

# pylint: disable=magic-value-comparison

import datetime

from django.test import Client
from django.urls import reverse

from marnies_maintenance_manager.jobs.models import Job
from marnies_maintenance_manager.jobs.tests.views.utils import (
    check_basic_page_html_structure,
)


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
    job_accepted_by_bob: Job,
    marnie_user_client: Client,
) -> None:
    """Ensure that the job detail view shows the expected job details.

    Args:
        job_accepted_by_bob (Job): The job created by Bob, with a quote added by Marnie
            that was also accepted by Bob.
        marnie_user_client (Client): The Django test client for Marnie.
    """
    job = job_accepted_by_bob
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

    assert job.quote.url in page

    # Search for the Job accepted/rejected HTML:
    assert "<strong>Accepted or Rejected (A/R):</strong> A" in page

    # Search for comments
    assert job.comments in page
