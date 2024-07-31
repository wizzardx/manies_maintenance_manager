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

HTML_FOR_FINAL_PAYMENT_POP_DOWNLOAD_TEMPLATE_START = (
    '<strong>Final Payment POP:</strong> <a href="'
)
HTML_FOR_FINAL_PAYMENT_POP_DOWNLOAD_TEMPLATE_END = '">Download Final Payment POP</a>'

HTML_FOR_FINAL_PAYMENT_POP_DOWNLOAD_TEMPLATE = (
    HTML_FOR_FINAL_PAYMENT_POP_DOWNLOAD_TEMPLATE_START
    + "{url}"
    + HTML_FOR_FINAL_PAYMENT_POP_DOWNLOAD_TEMPLATE_END
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


def test_fields_only_shown_when_job_complete(
    bob_job_completed_by_marnie: Job,
    marnie_user_client: Client,
) -> None:
    """Ensure that the "completed"-exclusive fields are shown when the job is complete.

    Args:
        bob_job_completed_by_marnie (Job): The job created by Bob, with a quote added by
            Marnie that was also accepted by Bob, and marked as complete.
        marnie_user_client (Client): The Django test client for Marnie.
    """
    job = bob_job_completed_by_marnie

    response = marnie_user_client.get(
        reverse("jobs:job_detail", kwargs={"pk": job.pk}),
    )
    page = response.content.decode("utf-8")

    # Make sure that job date is in the page
    assert '<span class="job-date">2022-01-01</span>' in page

    # Make sure that the invoice is in the page:
    assert job.invoice.url in page

    # Make sure that job comments are in the page:
    assert job.comments in page

    # Make sure that the "Job complete" flag is in the page:
    assert "<strong>Job complete:</strong> Yes" in page


def test_complete_only_fields_not_shown_when_not_complete(
    bob_job_completed_by_marnie: Job,
    marnie_user_client: Client,
) -> None:
    """Ensure "completed"-exclusive fields are not shown when the job is not complete.

    Args:
        bob_job_completed_by_marnie (Job): The job created by Bob, with a quote added by
            Marnie that was also accepted by Bob, and marked as complete.
        marnie_user_client (Client): The Django test client for Marnie.
    """
    job = bob_job_completed_by_marnie

    # Reset the "complete" flag so that the job is not complete, and the
    # "completed"-exclusive fields should not be shown.
    job.complete = False
    job.save()

    # Get the page.
    response = marnie_user_client.get(
        reverse("jobs:job_detail", kwargs={"pk": job.pk}),
    )
    page = response.content.decode("utf-8")

    # Make sure that job date is not in the page
    assert '<span class="job-date">2022-01-01</span>' not in page

    # Make sure that the invoice is in the page:
    assert job.invoice.url not in page

    # Make sure that job comments are in the page:
    assert job.comments not in page

    # Make sure that the "Job complete" flag is in the page:
    assert "<strong>Job complete:</strong> Yes" not in page


def test_final_payment_pop_upload_link_missing_when_agent_submitted_final_pop(
    bob_job_with_final_payment_pop: Job,
    bob_agent_user_client: Client,
) -> None:
    """Ensure the link to update the Final Payment Proof of Payment is not visible.

    Args:
        bob_job_with_final_payment_pop (Job): The job created by Bob with the final
            payment pop uploaded.
        bob_agent_user_client (Client): The Django test client for Bob.
    """
    job = bob_job_with_final_payment_pop
    page = get_job_detail_page(bob_agent_user_client, job)

    # Make sure that the link to update the Final Payment POP is not in the page:
    assert "Upload Final Payment POP" not in page


def get_job_detail_page(client: Client, job: Job) -> str:
    """Get the job detail page HTML content.

    Args:
        client (Client): The Django test client.
        job (Job): The job instance.

    Returns:
        str: The HTML content of the job detail page.
    """
    response = client.get(reverse("jobs:job_detail", kwargs={"pk": job.pk}))
    return response.content.decode("utf-8")


def test_final_payment_pop_upload_link_present_when_marnie_completed_job(
    bob_job_completed_by_marnie: Job,
    bob_agent_user_client: Client,
) -> None:
    """Ensure the link to update the Final Payment Proof of Payment is visible.

    Args:
        bob_job_completed_by_marnie (Job): The job created by Bob, with a quote added by
            Marnie that was also accepted by Bob, and marked as complete.
        bob_agent_user_client (Client): The Django test client for Bob.
    """
    job = bob_job_completed_by_marnie
    page = get_job_detail_page(bob_agent_user_client, job)

    # Make sure that the link to update the Final Payment POP is in the page:
    assert "Upload Final Payment POP" in page


def test_final_payment_pop_download_link_present_when_agent_submitted_final_pop(
    bob_job_with_final_payment_pop: Job,
    bob_agent_user_client: Client,
) -> None:
    """Ensure the link to download the Final Payment Proof of Payment is visible.

    Args:
        bob_job_with_final_payment_pop (Job): The job created by Bob with the final
            payment pop uploaded.
        bob_agent_user_client (Client): The Django test client for Bob.
    """
    job = bob_job_with_final_payment_pop
    page = get_job_detail_page(bob_agent_user_client, job)

    # Make sure that the link to update the Final Payment POP is in the page:
    expected_html = HTML_FOR_FINAL_PAYMENT_POP_DOWNLOAD_TEMPLATE.format(
        url=job.final_payment_pop.url,
    )
    assert expected_html in page


def test_final_payment_pop_download_link_missing_when_not_yet_submitted(
    bob_job_completed_by_marnie: Job,
    bob_agent_user_client: Client,
) -> None:
    """Ensure the link to download the Final Payment Proof of Payment is not visible.

    Args:
        bob_job_completed_by_marnie (Job): The job created by Bob, with a quote added by
            Marnie that was also accepted by Bob, and marked as complete.
        bob_agent_user_client (Client): The Django test client for Bob.
    """
    job = bob_job_completed_by_marnie
    page = get_job_detail_page(bob_agent_user_client, job)

    # Make sure that the link to update the Final Payment POP is not in the page:
    assert HTML_FOR_FINAL_PAYMENT_POP_DOWNLOAD_TEMPLATE_START not in page
