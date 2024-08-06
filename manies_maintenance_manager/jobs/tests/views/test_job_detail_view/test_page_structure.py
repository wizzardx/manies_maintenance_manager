"""Tests for the basic structure and content of the job detail view.

This module contains tests to verify that the job detail view has the correct
HTML structure and displays the expected job details.
"""

# pylint: disable=magic-value-comparison

import datetime

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client
from django.urls import reverse

from manies_maintenance_manager.jobs.models import Job
from manies_maintenance_manager.jobs.tests.views.conftest import (
    BOB_JOB_COMPLETED_BY_MANIE_NUM_PHOTOS,
)
from manies_maintenance_manager.jobs.tests.views.utils import (
    check_basic_page_html_structure,
)
from manies_maintenance_manager.jobs.utils import safe_read

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
    manie_user_client: Client,
) -> None:
    """Ensure that the job detail view has the correct basic structure.

    Args:
        job_created_by_bob (Job): The job created by Bob.
        manie_user_client (Client): The Django test client for Manie.
    """
    check_basic_page_html_structure(
        client=manie_user_client,
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
    manie_user_client: Client,
) -> None:
    """Ensure that the job detail view shows the expected job details.

    Args:
        job_accepted_by_bob (Job): The job created by Bob, with a quote added by Manie
            that was also accepted by Bob.
        manie_user_client (Client): The Django test client for Manie.
    """
    job = job_accepted_by_bob
    response = manie_user_client.get(
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


def test_manie_final_doc_upload_fields_only_shown_when_populated_by_user(
    job_created_by_bob: Job,
    manie_user_client: Client,
    test_pdf: SimpleUploadedFile,
    test_image: SimpleUploadedFile,
) -> None:
    """Ensure that the "completed"-exclusive fields are shown when the job is complete.

    Args:
        job_created_by_bob (Job): The job created by Bob.
        manie_user_client (Client): The Django test client for Manie.
        test_pdf (SimpleUploadedFile): A test PDF file.
        test_image (SimpleUploadedFile): A test image file.

    """
    job = job_created_by_bob

    # Manually populate the relevant fields, to check that they always display when
    # populated, regardless of the current status of the Job.
    job.job_onsite_work_completion_date = datetime.date(2022, 1, 1)
    job.invoice = test_pdf
    job.comments = "This is my comment for the job."
    job.final_payment_pop = test_pdf
    job.status = Job.Status.FINAL_PAYMENT_POP_UPLOADED.value

    # Add two photos to the completed job.
    for _ in range(BOB_JOB_COMPLETED_BY_MANIE_NUM_PHOTOS):
        with safe_read(test_image):
            job.job_completion_photos.create(photo=test_image)

    with safe_read(test_pdf):
        job.save()

    response = manie_user_client.get(
        reverse("jobs:job_detail", kwargs={"pk": job.pk}),
    )
    page = response.content.decode("utf-8")

    # Make sure that job date is in the page
    assert '<span class="job-date">2022-01-01</span>' in page

    # Make sure that the invoice is in the page:
    assert job.invoice.url in page  # type: ignore[attr-defined]
    assert "<strong>Invoice:</strong" in page

    # Make sure that job comments are in the page:
    assert job.comments in page
    assert "<strong>Comments:</strong>" in page

    # Check for the photos
    assert '.jpg">Download Photo 1</a>' in page

    # Make sure that the "Job complete" flag is in the page:
    assert "<strong>Job complete:</strong> Yes" in page


def test_complete_only_fields_not_shown_when_not_populated_by_manie(
    bob_job_with_final_payment_pop: Job,
    manie_user_client: Client,
) -> None:
    """Ensure "manie final doc"-exclusive fields are not incorrectly shown.

    Args:
        bob_job_with_final_payment_pop (Job): The job with final POP uploaded by
            the agent.
        manie_user_client (Client): The Django test client for Manie.
    """
    job = bob_job_with_final_payment_pop

    # Reset some "manie has populated things in the web ui" fields, to ensure that
    # they are not shown when they are not populated.
    job.job_onsite_work_completion_date = None
    job.invoice = None
    job.comments = ""
    for photo in job.job_completion_photos.all():
        photo.delete()
    job.status = Job.Status.MANIE_SUBMITTED_DOCUMENTATION.value
    job.save()

    # Get the page.
    response = manie_user_client.get(
        reverse("jobs:job_detail", kwargs={"pk": job.pk}),
    )
    page = response.content.decode("utf-8")

    # Make sure that job date is not in the page
    assert '<span class="job-date">2022-01-01</span>' not in page

    # Make sure that the invoice is in the page:
    assert "<strong>Invoice:</strong" not in page

    # Make sure that job comments are in the page:
    assert "<strong>Comments:</strong>" not in page

    # Check for the photos
    assert '.jpg">Download Photo 1</a>' not in page

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


def test_final_payment_pop_upload_link_present_when_manie_uploaded_final_docs(
    bob_job_with_manie_final_documentation: Job,
    bob_agent_user_client: Client,
) -> None:
    """Ensure the link to update the Final Payment Proof of Payment is visible.

    Args:
        bob_job_with_manie_final_documentation (Job): The job created by Bob, with
            the final documentation uploaded by Manie.
        bob_agent_user_client (Client): The Django test client for Bob.
    """
    job = bob_job_with_manie_final_documentation
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
    bob_job_with_manie_final_documentation: Job,
    bob_agent_user_client: Client,
) -> None:
    """Ensure the link to download the Final Payment Proof of Payment is not visible.

    Args:
        bob_job_with_manie_final_documentation (Job): The job created by Bob, with
            the final documentation uploaded by Manie.
        bob_agent_user_client (Client): The Django test client for Bob.
    """
    job = bob_job_with_manie_final_documentation
    page = get_job_detail_page(bob_agent_user_client, job)

    # Make sure that the link to update the Final Payment POP is not in the page:
    assert HTML_FOR_FINAL_PAYMENT_POP_DOWNLOAD_TEMPLATE_START not in page


def test_job_complete_field_appears_when_final_payment_pop_uploaded(
    bob_job_with_final_payment_pop: Job,
    bob_agent_user_client: Client,
) -> None:
    """Ensure the "Job complete" field appears when the final payment pop is uploaded.

    Args:
        bob_job_with_final_payment_pop (Job): The job created by Bob with the final
            payment pop uploaded.
        bob_agent_user_client (Client): The Django test client for Bob.
    """
    job = bob_job_with_final_payment_pop
    page = get_job_detail_page(bob_agent_user_client, job)

    # Make sure that the "Job complete" flag is in the page:
    assert "<strong>Job complete:</strong> Yes" in page


def test_job_complete_field_not_appears_when_final_payment_pop_not_uploaded(
    bob_job_with_manie_final_documentation: Job,
    bob_agent_user_client: Client,
) -> None:
    """Ensure the "Job complete" field does not appear final pop is not uploaded.

    Args:
        bob_job_with_manie_final_documentation (Job): The job created by Bob, with
            the final documentation uploaded by Manie.
        bob_agent_user_client (Client): The Django test client for Bob.
    """
    job = bob_job_with_manie_final_documentation
    page = get_job_detail_page(bob_agent_user_client, job)

    # Make sure that the "Job complete" flag is not in the page:
    assert "<strong>Job complete:</strong> Yes" not in page
