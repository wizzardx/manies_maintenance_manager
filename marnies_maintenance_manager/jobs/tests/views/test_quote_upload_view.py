"""Tests for the job "upload quote" view."""

# pylint: disable=redefined-outer-name,unused-argument,magic-value-comparison

import pytest
from django.contrib.messages.storage.base import Message
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template.response import TemplateResponse
from django.test import Client
from rest_framework import status
from typeguard import check_type

from marnies_maintenance_manager.jobs import constants
from marnies_maintenance_manager.jobs.models import Job
from marnies_maintenance_manager.jobs.tests.conftest import BASIC_TEST_PDF_FILE
from marnies_maintenance_manager.jobs.tests.utils import (
    suppress_fastdev_strict_if_deprecation_warning,
)
from marnies_maintenance_manager.jobs.utils import safe_read
from marnies_maintenance_manager.jobs.views.quote_upload_view import QuoteUploadView
from marnies_maintenance_manager.users.models import User

from .utils import check_basic_page_html_structure
from .utils import post_update_request_and_check_errors
from .utils import verify_email_attachment


def test_anonymous_user_cannot_access_the_view(
    client: Client,
    bob_job_upload_quote_url: str,
) -> None:
    """Test that the anonymous user cannot access the "upload quote" view.

    Args:
        client (Client): The Django test client.
        bob_job_upload_quote_url (str): The URL for Bobs jobs "upload quote" view.
    """
    with suppress_fastdev_strict_if_deprecation_warning():
        response = client.get(bob_job_upload_quote_url, follow=True)

    # This should be a redirect to a login page:
    assert response.status_code == status.HTTP_200_OK

    expected_redirect_chain = [
        (
            f"/accounts/login/?next={bob_job_upload_quote_url}",
            status.HTTP_302_FOUND,
        ),
    ]
    assert response.redirect_chain == expected_redirect_chain


def test_agent_user_cannot_access_the_view(
    bob_agent_user_client: Client,
    bob_job_upload_quote_url: str,
) -> None:
    """Test that the agent user cannot access the "upload quote" view.

    Args:
        bob_agent_user_client (Client): The Django test client for Bob.
        bob_job_upload_quote_url (str): The URL for the view where Marnie can
            upload a quote for the job created by Bob.
    """
    response = bob_agent_user_client.get(bob_job_upload_quote_url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_admin_user_can_access_the_view(
    superuser_client: Client,
    bob_job_upload_quote_url: str,
) -> None:
    """Test that the admin user can access the "upload quote" view.

    Args:
        superuser_client (Client): The Django test client for the superuser.
        bob_job_upload_quote_url (str): The URL for the view where the superuser can
            upload a quote for the job created by Bob.
    """
    response = superuser_client.get(bob_job_upload_quote_url)
    assert response.status_code == status.HTTP_200_OK


def test_marnie_user_can_access_the_view(
    marnie_user_client: Client,
    bob_job_upload_quote_url: str,
) -> None:
    """Test that the Marnie user can access the "upload quote" view.

    Args:
        marnie_user_client (Client): The Django test client for Marnie.
        bob_job_upload_quote_url (str): The URL for the view where Marnie can upload a
            quote for the job created by Bob.
    """
    response = marnie_user_client.get(bob_job_upload_quote_url)
    assert response.status_code == status.HTTP_200_OK


def test_page_has_basic_correct_structure(
    marnie_user_client: Client,
    bob_job_upload_quote_url: str,
) -> None:
    """Test that the "upload quote" page has the correct basic structure.

    Args:
        marnie_user_client (Client): The Django test client for Marnie.
        bob_job_upload_quote_url (str): The URL for the view where Marnie can upload a
            quote for the job created by Bob.
    """
    check_basic_page_html_structure(
        client=marnie_user_client,
        url=bob_job_upload_quote_url,
        expected_title="Upload Quote",
        expected_template_name="jobs/quote_upload.html",
        expected_h1_text="Upload Quote",
        expected_func_name="view",
        expected_url_name="quote_upload",
        expected_view_class=QuoteUploadView,
    )


def post_job_update_and_check_response(
    marnie_user_client: Client,
    bob_job_update_url: str,
    test_pdf: SimpleUploadedFile,
    job: Job,
) -> None:
    """Post "upload quote" and check the response.

    Args:
        marnie_user_client (Client): The Django test client for Marnie.
        bob_job_update_url (str): The URL for Bob's "upload quote" view.
        test_pdf (SimpleUploadedFile): The test PDF file.
        job (Job): The related job to update.
    """
    with safe_read(test_pdf):
        response = marnie_user_client.post(
            bob_job_update_url,
            {
                "quote": test_pdf,
            },
            follow=True,
        )

    # Assert the response status code is 200
    assert response.status_code == status.HTTP_200_OK

    # Check the redirect chain that leads things up to here:
    assert response.redirect_chain == [
        ("/jobs/?agent=bob", status.HTTP_302_FOUND),
    ]

    # Refresh the Maintenance Job from the database:
    job.refresh_from_db()


def test_view_has_quote_field(
    bob_job_with_initial_marnie_inspection: Job,
    marnie_user_client: Client,
    bob_job_upload_quote_url: str,
    test_pdf: SimpleUploadedFile,
) -> None:
    """Test that the "upload quote" page has the 'quote' field.

    Args:
        bob_job_with_initial_marnie_inspection (Job): The job created by Bob with the
            initial inspection done by Marnie.
        marnie_user_client (Client): The Django test client for Marnie.
        bob_job_upload_quote_url (str): The URL for the view where Marnie can upload a
            quote for the job created by Bob.
        test_pdf (SimpleUploadedFile): The test PDF file.
    """
    # POST request to upload new PDF
    post_job_update_and_check_response(
        marnie_user_client,
        bob_job_upload_quote_url,
        test_pdf,
        bob_job_with_initial_marnie_inspection,
    )

    # And confirm that the PDF file has been updated
    quote_name = bob_job_with_initial_marnie_inspection.quote.name
    # Can be something like one of these:
    # - quotes/test.pdf
    # - quotes/test_qKAGkkh.pdf
    assert quote_name.startswith("quotes/test"), quote_name
    assert quote_name.endswith(".pdf")


def test_quote_field_is_required(
    bob_job_with_initial_marnie_inspection: Job,
    marnie_user_client: Client,
    bob_job_upload_quote_url: str,
) -> None:
    """Test that the 'quote' field is required.

    Args:
        bob_job_with_initial_marnie_inspection (Job): The job created by Bob with the
            initial inspection done by Marnie.
        marnie_user_client (Client): The Django test client for Marnie.
        bob_job_upload_quote_url (str): The URL for the view where Marnie can upload a
            quote for the job created by Bob.
    """
    post_update_request_and_check_errors(
        client=marnie_user_client,
        url=bob_job_upload_quote_url,
        data={},
        field_name="quote",
        expected_error="This field is required.",
    )


def test_updating_job_changes_status_to_quote_uploaded(
    bob_job_with_initial_marnie_inspection: Job,
    marnie_user_client: Client,
    bob_job_upload_quote_url: str,
    test_pdf: SimpleUploadedFile,
) -> None:
    """Test that updating the job changes the status to 'Quote Uploaded'.

    Args:
        bob_job_with_initial_marnie_inspection (Job): The job created by Bob with the
            initial inspection done by Marnie.
        marnie_user_client (Client): The Django test client for Marnie.
        bob_job_upload_quote_url (str): The URL for the view where Marnie can upload a
            quote for the job created by Bob.
        test_pdf (SimpleUploadedFile): The test PDF file.
    """
    # POST request to upload new details:
    post_job_update_and_check_response(
        marnie_user_client,
        bob_job_upload_quote_url,
        test_pdf,
        bob_job_with_initial_marnie_inspection,
    )

    # Check that the status changed as expected
    bob_job_with_initial_marnie_inspection.refresh_from_db()
    assert (
        bob_job_with_initial_marnie_inspection.status == Job.Status.QUOTE_UPLOADED.value
    )


def test_should_not_allow_txt_extension_file_for_quote(
    bob_job_with_initial_marnie_inspection: Job,
    marnie_user_client: Client,
    bob_job_upload_quote_url: str,
) -> None:
    """Test that the view should not allow a .txt file extension for the 'quote' field.

    Args:
        bob_job_with_initial_marnie_inspection (Job): The job created by Bob with the
            initial inspection done by Marnie.
        marnie_user_client (Client): The Django test client for Marnie.
        bob_job_upload_quote_url (str): The URL for the view where Marnie can upload a
            quote for the job created by Bob.
    """
    # New TXT file to upload
    test_txt = SimpleUploadedFile(
        "test.txt",
        BASIC_TEST_PDF_FILE.read_bytes(),
        content_type="application/pdf",
    )

    with safe_read(test_txt):
        post_update_request_and_check_errors(
            client=marnie_user_client,
            url=bob_job_upload_quote_url,
            data={
                "quote": test_txt,
            },
            field_name="quote",
            expected_error="File extension “txt” is not allowed. "
            "Allowed extensions are: pdf.",
        )


def test_validates_pdf_contents(
    bob_job_with_initial_marnie_inspection: Job,
    marnie_user_client: Client,
    bob_job_upload_quote_url: str,
) -> None:
    """Test that the view should validate the contents of the PDF file.

    Args:
        bob_job_with_initial_marnie_inspection (Job): The job created by Bob with the
            initial inspection done by Marnie.
        marnie_user_client (Client): The Django test client for Marnie.
        bob_job_upload_quote_url (str): The URL for the view where Marnie can upload a
            quote for the job created by Bob.
    """
    # New PDF file to upload
    new_pdf = SimpleUploadedFile(
        "new.pdf",
        b"invalid_file_content",
        content_type="application/pdf",
    )

    with safe_read(new_pdf):
        post_update_request_and_check_errors(
            client=marnie_user_client,
            url=bob_job_upload_quote_url,
            data={
                "quote": new_pdf,
            },
            field_name="quote",
            expected_error="This is not a valid PDF file",
        )


def test_marnie_cannot_access_view_after_quote_already_uploaded(
    bob_job_with_quote: Job,
    marnie_user_client: Client,
    bob_job_upload_quote_url: str,
) -> None:
    """Ensure Marnie can't access the update view after completing initial inspection.

    Args:
        bob_job_with_quote (Job): The job created by Bob with a quote uploaded by
            Marnie.
        marnie_user_client (Client): The Django test client for Marnie.
        bob_job_upload_quote_url (str): The URL for the view where Marnie can upload a
            quote for the job created by Bob.
    """
    response = marnie_user_client.get(bob_job_upload_quote_url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_superuser_cannot_access_view_after_quote_already_uploaded(
    bob_job_with_quote: Job,
    superuser_client: Client,
    bob_job_upload_quote_url: str,
) -> None:
    """Ensure the superuser can't access the view after Marnie already uploaded a quote.

    Args:
        bob_job_with_quote (Job): The job created by Bob with a quote uploaded by
            Marnie.
        superuser_client (Client): The Django test client for the superuser.
        bob_job_upload_quote_url (str): The URL for the view where Marnie can upload a
            quote for the job created by Bob.
    """
    response = superuser_client.get(bob_job_upload_quote_url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_clicking_save_redirects_to_job_listing_page(
    job_created_by_bob: Job,
    marnie_user_client: Client,
    bob_job_upload_quote_url: str,
    test_pdf: SimpleUploadedFile,
) -> None:
    """Test that clicking 'Save' redirects to the job listing page.

    Args:
        job_created_by_bob (Job): The job created by Bob.
        marnie_user_client (Client): The Django test client for Marnie.
        bob_job_upload_quote_url (str): The URL for the view where Marnie can
            upload a quote for the job created by Bob.
        test_pdf (SimpleUploadedFile): The test PDF file.
    """
    post_job_update_and_check_response(
        marnie_user_client,
        bob_job_upload_quote_url,
        test_pdf,
        job_created_by_bob,
    )


@pytest.fixture()
def http_response_to_marnie_uploading_a_quote(
    bob_job_with_initial_marnie_inspection: Job,
    bob_job_upload_quote_url: str,
    marnie_user_client: Client,
    test_pdf: SimpleUploadedFile,
) -> TemplateResponse:
    """Get the HTTP response after Marnie uploads an Invoice to Bob's job.

    Args:
        bob_job_with_initial_marnie_inspection (Job): The job created by Bob with the
            initial inspection done by Marnie.
        bob_job_upload_quote_url (str): The URL for the view where Marnie can upload a
            quote for the job created by Bob.
        marnie_user_client (Client): The Django test client for Marnie.
        test_pdf (SimpleUploadedFile): The test PDF file.

    Returns:
        TemplateResponse: The HTTP response after Marnie uploads an Invoice to Bob's
            job.
    """
    with safe_read(test_pdf):
        response = check_type(
            marnie_user_client.post(
                bob_job_upload_quote_url,
                {
                    "quote": test_pdf,
                },
                follow=True,
            ),
            TemplateResponse,
        )

    # Assert the response status code is 200
    assert response.status_code == status.HTTP_200_OK

    # Check the redirect chain that leads things up to here:
    expected_chain = [("/jobs/?agent=bob", status.HTTP_302_FOUND)]
    assert response.redirect_chain == expected_chain  # type: ignore[attr-defined]

    # Return the response to the caller
    return response


@pytest.fixture()
def flashed_message_after_uploading_a_quote(
    http_response_to_marnie_uploading_a_quote: TemplateResponse,
) -> Message:
    """Retrieve the flashed message after Marnie uploads a quote.

    Args:
        http_response_to_marnie_uploading_a_quote (TemplateResponse): The
            HTTP response after Marnie uploads a quote.

    Returns:
        Message: The flashed message after Marnie uploads a quote.
    """
    # Check the messages:
    response = http_response_to_marnie_uploading_a_quote
    messages = list(response.context["messages"])
    assert len(messages) == 1

    # Return the retrieved message to the caller
    return check_type(messages[0], Message)


def test_a_flash_message_is_displayed_when_marnie_clicks_save(
    flashed_message_after_uploading_a_quote: Message,
) -> None:
    """Test that a flash message is displayed when Marnie clicks 'Save'.

    Args:
        flashed_message_after_uploading_a_quote (Message): The flashed message after
            Marnie uploads a quote.
    """
    # Marnie should see a "Maintenance Update email has been sent to <agent username>"
    # flash message when she clicks the "Save" button.
    flashed_message = flashed_message_after_uploading_a_quote
    assert flashed_message.message == (
        "Your quote has been uploaded. An email has been sent to bob."
    )
    assert flashed_message.level_tag == "success"


def test_marnie_clicking_save_sends_an_email_to_agent(
    http_response_to_marnie_uploading_a_quote: TemplateResponse,
    bob_agent_user: User,
    marnie_user: User,
) -> None:
    """Test that Marnie clicking 'Save' sends an email to the agent.

    Args:
        http_response_to_marnie_uploading_a_quote (TemplateResponse): The HTTP response
            after Marnie uploads a quote.
        bob_agent_user (User): The agent user Bob.
        marnie_user (User): The user Marnie.
    """
    # For the earlier part of our fixtures (job creation by agent), we built the model
    # instance directly, rather than going through the view-based logic, so an email
    # wouldn't have been sent there.

    # But for the most recent part of the fixtures (Marnie inspecting the site and
    # updating thew website, then later uploading an invoice), we did go through
    # various view-based logic, so some emails should have been sent there.
    num_mails_sent = len(mail.outbox)
    expected_num_emails_by_this_point = 2
    assert num_mails_sent == expected_num_emails_by_this_point

    # Grab the most recent mails:
    email = mail.outbox[-1]

    # Check various details of the mail here.

    # Check mail metadata:
    assert email.subject == "Marnie uploaded a quote for your maintenance request"
    assert bob_agent_user.email in email.to
    assert marnie_user.email in email.cc
    assert constants.DEFAULT_FROM_EMAIL in email.from_email

    # Check mail contents:
    assert (
        "Marnie uploaded a quote for a maintenance job. "
        "The quote is attached to this email." in email.body
    )

    # There should now be exactly one job in the database. Fetch it so that we can
    # use it to check the email body.
    verify_email_attachment(
        email,
        expected_prefix="quotes/test",
        expected_suffix=".pdf",
        expected_content=BASIC_TEST_PDF_FILE.read_bytes(),
        expected_mime_type="application/pdf",
    )


def test_marnie_clicking_save_sets_state_to_quote_uploaded(
    bob_job_with_initial_marnie_inspection: Job,
    marnie_user_client: Client,
    bob_job_upload_quote_url: str,
    test_pdf: SimpleUploadedFile,
) -> None:
    """Test that Marnie clicking 'Save' sets the state to 'Quote Uploaded'.

    Args:
        bob_job_with_initial_marnie_inspection (Job): The job created by Bob with the
            initial inspection done by Marnie.
        marnie_user_client (Client): The Django test client for Marnie.
        bob_job_upload_quote_url (str): The URL for the view where Marnie can upload a
            quote for the job created by Bob.
        test_pdf (SimpleUploadedFile): The test PDF file.
    """
    # POST request to upload new details:
    post_job_update_and_check_response(
        marnie_user_client,
        bob_job_upload_quote_url,
        test_pdf,
        bob_job_with_initial_marnie_inspection,
    )

    # Check that the status changed as expected
    assert (
        bob_job_with_initial_marnie_inspection.status == Job.Status.QUOTE_UPLOADED.value
    )
