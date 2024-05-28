"""Tests for the job update view."""

# pylint: disable=redefined-outer-name,unused-argument,magic-value-comparison

import datetime
from typing import cast

import pytest
from django.contrib.messages.storage.base import Message
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.template.response import TemplateResponse
from django.test import Client
from rest_framework import status

from marnies_maintenance_manager.jobs import constants
from marnies_maintenance_manager.jobs.models import Job
from marnies_maintenance_manager.jobs.views import JobUpdateView
from marnies_maintenance_manager.users.models import User

from .conftest import BASIC_TEST_PDF_FILE
from .utils import check_basic_page_html_structure


def post_update_request_and_check_errors(
    client: Client,
    url: str,
    data: dict[str, str | SimpleUploadedFile],
    field_name: str,
    expected_error: str,
) -> None:
    """Post an update request and check for errors.

    Args:
        client (Client): The Django test client.
        url (str): The URL to post the request to.
        data (dict): The data to post.
        field_name (str): The field name to check for errors.
        expected_error (str): The expected error message.
    """
    response = client.post(url, data, follow=True)
    # Assert the response status code is 200
    assert response.status_code == status.HTTP_200_OK

    # Check the redirect chain that leads things up to here:
    assert response.redirect_chain == []

    # Check that the expected error is present.
    form_errors = response.context["form"].errors
    assert field_name in form_errors
    assert form_errors[field_name] == [expected_error]


def test_anonymous_user_cannot_access_the_view(
    client: Client,
    bob_job_update_url: str,
) -> None:
    """Test that the anonymous user cannot access the job update view.

    Args:
        client (Client): The Django test client.
        bob_job_update_url (str): The URL for Bobs job update view.
    """
    # Note: Django-FastDev causes a DeprecationWarning to be logged when using the
    # {% if %} template tag. This is somewhere deep within the Django-Allauth package,
    # while handling a GET request to the /accounts/login/ URL. We can ignore this
    # for our testing.
    with pytest.warns(
        DeprecationWarning,
        match="set FASTDEV_STRICT_IF in settings, and use {% ifexists %} instead of "
        "{% if %}",
    ):
        response = client.get(bob_job_update_url, follow=True)

    # This should be a redirect to a login page:
    assert response.status_code == status.HTTP_200_OK

    expected_redirect_chain = [
        (
            f"/accounts/login/?next=/jobs/{bob_job_update_url.split('/')[-3]}/update/",
            status.HTTP_302_FOUND,
        ),
    ]
    assert response.redirect_chain == expected_redirect_chain


def test_agent_user_cannot_access_the_view(
    bob_agent_user_client: Client,
    bob_job_update_url: str,
) -> None:
    """Test that the agent user cannot access the job update view.

    Args:
        bob_agent_user_client (Client): The Django test client for Bob.
        bob_job_update_url (str): The URL for Bobs job update view.
    """
    response = bob_agent_user_client.get(bob_job_update_url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_admin_user_can_access_the_view(
    superuser_client: Client,
    bob_job_update_url: str,
) -> None:
    """Test that the admin user can access the job update view.

    Args:
        superuser_client (Client): The Django test client for the superuser.
        bob_job_update_url (str): The URL for Bobs job update view.
    """
    response = superuser_client.get(bob_job_update_url)
    assert response.status_code == status.HTTP_200_OK


def test_marnie_user_can_access_the_view(
    marnie_user_client: Client,
    bob_job_update_url: str,
) -> None:
    """Test that the Marnie user can access the job update view.

    Args:
        marnie_user_client (Client): The Django test client for Marnie.
        bob_job_update_url (str): The URL for Bobs job update view.
    """
    response = marnie_user_client.get(bob_job_update_url)
    assert response.status_code == status.HTTP_200_OK


def test_page_has_basic_correct_structure(
    marnie_user_client: Client,
    bob_job_update_url: str,
) -> None:
    """Test that the job update page has the correct basic structure.

    Args:
        marnie_user_client (Client): The Django test client for Marnie.
        bob_job_update_url (str): The URL for Bobs job update view.
    """
    check_basic_page_html_structure(
        client=marnie_user_client,
        url=bob_job_update_url,
        expected_title="Update Maintenance Job",
        expected_template_name="jobs/job_update.html",
        expected_h1_text="Update Maintenance Job",
        expected_func_name="view",
        expected_url_name="job_update",
        expected_view_class=JobUpdateView,
    )


def test_view_has_date_of_inspection_field(
    job_created_by_bob: Job,
    marnie_user_client: Client,
    bob_job_update_url: str,
    test_pdf: SimpleUploadedFile,
) -> None:
    """Test that the job update page has the 'date_of_inspection' field.

    Args:
        job_created_by_bob (Job): The job created by Bob.
        marnie_user_client (Client): The Django test client for Marnie.
        bob_job_update_url (str): The URL for Bobs job update view.
        test_pdf (SimpleUploadedFile): The test PDF file.
    """
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

    # Check the redirect chain that leads things up to here:
    assert response.redirect_chain == [
        ("/jobs/?agent=bob", status.HTTP_302_FOUND),
    ]

    # Refresh the Maintenance Job from the database, and then check the updated
    # record:
    job_created_by_bob.refresh_from_db()
    assert job_created_by_bob.date_of_inspection == datetime.date(2001, 2, 5)


def test_view_has_quote_field(
    job_created_by_bob: Job,
    marnie_user_client: Client,
    bob_job_update_url: str,
    test_pdf: SimpleUploadedFile,
) -> None:
    """Test that the job update page has the 'quote' field.

    Args:
        job_created_by_bob (Job): The job created by Bob.
        marnie_user_client (Client): The Django test client for Marnie.
        bob_job_update_url (str): The URL for Bobs job update view.
        test_pdf (SimpleUploadedFile): The test PDF file.
    """
    # POST request to upload new PDF
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

    # Check the redirect chain that leads things up to here:
    assert response.redirect_chain == [
        ("/jobs/?agent=bob", status.HTTP_302_FOUND),
    ]

    # Refresh the Maintenance Job from the database
    job_created_by_bob.refresh_from_db()

    # And confirm that the PDF file has been updated
    assert job_created_by_bob.quote.name.endswith("test.pdf")


def test_date_of_inspection_field_is_required(
    job_created_by_bob: Job,
    marnie_user_client: Client,
    bob_job_update_url: str,
) -> None:
    """Test that the 'date_of_inspection' field is required.

    Args:
        job_created_by_bob (Job): The job created by Bob.
        marnie_user_client (Client): The Django test client for Marnie.
        bob_job_update_url (str): The URL for Bobs job update view.
    """
    post_update_request_and_check_errors(
        client=marnie_user_client,
        url=bob_job_update_url,
        data={},
        field_name="date_of_inspection",
        expected_error="This field is required.",
    )


def test_quote_field_is_required(
    job_created_by_bob: Job,
    marnie_user_client: Client,
    bob_job_update_url: str,
) -> None:
    """Test that the 'quote' field is required.

    Args:
        job_created_by_bob (Job): The job created by Bob.
        marnie_user_client (Client): The Django test client for Marnie.
        bob_job_update_url (str): The URL for Bobs job update view.
    """
    post_update_request_and_check_errors(
        client=marnie_user_client,
        url=bob_job_update_url,
        data={},
        field_name="quote",
        expected_error="This field is required.",
    )


def test_updating_job_changes_status_to_inspection_completed(
    job_created_by_bob: Job,
    marnie_user_client: Client,
    bob_job_update_url: str,
    test_pdf: SimpleUploadedFile,
) -> None:
    """Test that updating the job changes the status to 'Inspection Completed'.

    Args:
        job_created_by_bob (Job): The job created by Bob.
        marnie_user_client (Client): The Django test client for Marnie.
        bob_job_update_url (str): The URL for Bobs job update view.
        test_pdf (SimpleUploadedFile): The test PDF file.
    """
    # POST request to upload new details:
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

    # Check the redirect chain that leads things up to here:
    assert response.redirect_chain == [
        ("/jobs/?agent=bob", status.HTTP_302_FOUND),
    ]

    # Refresh the Maintenance Job from the database
    job_created_by_bob.refresh_from_db()

    # Check that the status changed as expected
    assert job_created_by_bob.status == Job.Status.INSPECTION_COMPLETED.value


def test_should_not_allow_txt_extension_file_for_quote(
    job_created_by_bob: Job,
    marnie_user_client: Client,
    bob_job_update_url: str,
) -> None:
    """Test that the view should not allow a .txt file extension for the 'quote' field.

    Args:
        job_created_by_bob (Job): The job created by Bob.
        marnie_user_client (Client): The Django test client for Marnie.
        bob_job_update_url (str): The URL for Bobs job update view.
    """
    # New TXT file to upload
    test_txt = SimpleUploadedFile(
        "test.txt",
        BASIC_TEST_PDF_FILE.read_bytes(),
        content_type="application/pdf",
    )

    post_update_request_and_check_errors(
        client=marnie_user_client,
        url=bob_job_update_url,
        data={
            "date_of_inspection": "2001-02-05",
            "quote": test_txt,
        },
        field_name="quote",
        expected_error="File extension “txt” is not allowed. "
        "Allowed extensions are: pdf.",
    )


def test_validates_pdf_contents(
    job_created_by_bob: Job,
    marnie_user_client: Client,
    bob_job_update_url: str,
) -> None:
    """Test that the view should validate the contents of the PDF file.

    Args:
        job_created_by_bob (Job): The job created by Bob.
        marnie_user_client (Client): The Django test client for Marnie.
        bob_job_update_url (str): The URL for Bobs job update view.
    """
    # New PDF file to upload
    new_pdf = SimpleUploadedFile(
        "new.pdf",
        b"invalid_file_content",
        content_type="application/pdf",
    )

    post_update_request_and_check_errors(
        client=marnie_user_client,
        url=bob_job_update_url,
        data={
            "date_of_inspection": "2001-02-05",
            "quote": new_pdf,
        },
        field_name="quote",
        expected_error="This is not a valid PDF file.",
    )


def test_marnie_cannot_access_view_after_initial_site_inspection(
    bob_job_with_initial_marnie_inspection: Job,
    marnie_user_client: Client,
    bob_job_update_url: str,
) -> None:
    """Ensure Marnie can't access the update view after completing initial inspection.

    Args:
        bob_job_with_initial_marnie_inspection (Job): The job created by Bob with the
            initial inspection done by Marnie.
        marnie_user_client (Client): The Django test client for Marnie.
        bob_job_update_url (str): The URL for the job update view for the job created
            by Bob.
    """
    response = marnie_user_client.get(bob_job_update_url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_clicking_save_redirects_to_job_listing_page(
    job_created_by_bob: Job,
    marnie_user_client: Client,
    bob_job_update_url: str,
    test_pdf: SimpleUploadedFile,
) -> None:
    """Test that clicking 'Save' redirects to the job listing page.

    Args:
        job_created_by_bob (Job): The job created by Bob.
        marnie_user_client (Client): The Django test client for Marnie.
        bob_job_update_url (str): The URL for Bobs job update view.
        test_pdf (SimpleUploadedFile): The test PDF file.
    """
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

    # Check the redirect chain that leads things up to here:
    assert response.redirect_chain == [
        ("/jobs/?agent=bob", status.HTTP_302_FOUND),
    ]


@pytest.fixture()
def http_response_to_marnie_inspecting_site_of_job_by_bob(
    job_created_by_bob: Job,
    bob_job_update_url: str,
    marnie_user_client: Client,
    test_pdf: SimpleUploadedFile,
) -> TemplateResponse:
    """Get the HTTP response after Marnie inspects the site of the job created by Bob.

    Args:
        job_created_by_bob (Job): The job created by Bob.
        bob_job_update_url (str): The URL for Bobs job update view.
        marnie_user_client (Client): The Django test client for Marnie.
        test_pdf (SimpleUploadedFile): The test PDF file.

    Returns:
        TemplateResponse: The HTTP response after Marnie inspects the site of the job
    """
    response = cast(
        TemplateResponse,
        marnie_user_client.post(
            bob_job_update_url,
            {
                "date_of_inspection": "2001-02-05",
                "quote": test_pdf,
            },
            follow=True,
        ),
    )

    # Assert the response status code is 200
    assert response.status_code == status.HTTP_200_OK

    # Check the redirect chain that leads things up to here:
    expected_chain = [("/jobs/?agent=bob", status.HTTP_302_FOUND)]
    assert response.redirect_chain == expected_chain  # type: ignore[attr-defined]

    # Return the response to the caller
    return response


@pytest.fixture()
def flashed_message_after_inspecting_a_site(
    http_response_to_marnie_inspecting_site_of_job_by_bob: TemplateResponse,
) -> Message:
    """Retrieve the flashed message after Marnie inspects a site.

    Args:
        http_response_to_marnie_inspecting_site_of_job_by_bob (TemplateResponse): The
            HTTP response after Marnie inspects the site.

    Returns:
        Message: The flashed message after Marnie inspects a site.
    """
    # Check the messages:
    response = http_response_to_marnie_inspecting_site_of_job_by_bob
    messages = list(response.context["messages"])
    assert len(messages) == 1

    # Return the retrieved message to the caller
    return cast(Message, messages[0])


def test_a_flash_message_is_displayed_when_marnie_clicks_save(
    flashed_message_after_inspecting_a_site: Message,
) -> None:
    """Test that a flash message is displayed when Marnie clicks 'Save'.

    Args:
        flashed_message_after_inspecting_a_site (Message): The flashed message after
            Marnie inspects a site.
    """
    # Marnie should see a "Maintenance Update email has been sent to <agent username>"
    # flash message when she clicks the "Save" button.
    flashed_message = flashed_message_after_inspecting_a_site
    assert flashed_message.message == "An email has been sent to bob."
    assert flashed_message.level_tag == "success"


def test_marnie_clicking_save_sends_an_email_to_agent(
    http_response_to_marnie_inspecting_site_of_job_by_bob: TemplateResponse,
    bob_agent_user: User,
    marnie_user: User,
) -> None:
    """Test that Marnie clicking 'Save' sends an email to the agent.

    Args:
        http_response_to_marnie_inspecting_site_of_job_by_bob (TemplateResponse): The
            HTTP response after Marnie inspects the site.
        bob_agent_user (User): The agent user Bob.
        marnie_user (User): The user Marnie.
    """
    # For the earlier part of our fixtures (job creation by agent), we built the model
    # instance directly, rather than going through the view-based logic, so an email
    # wouldn't have been sent there.

    # But for the most recent part of the fixtures (Marnie inspecting the site and
    # updating thew website), we did go through the view-based logic, so an email
    # should have been sent there.
    num_mails_sent = len(mail.outbox)
    assert num_mails_sent == 1

    # Grab the mail:
    email = mail.outbox[0]

    # Check various details of the mail here.

    # Check mail metadata:
    assert email.subject == "Quote for your maintenance request"
    assert bob_agent_user.email in email.to
    assert marnie_user.email in email.cc
    assert constants.DEFAULT_FROM_EMAIL in email.from_email

    assert (
        "Marnie performed the inspection on 2001-02-05 and has quoted you. The quote "
        "is attached to this email." in email.body
    )

    assert "Details of your original request:" in email.body

    # A separator line:
    assert "-----" in email.body

    # The original mail subject line, as a line in the body:
    assert "Subject: New maintenance request by bob" in email.body

    # And all the original body lines, too, as per our previous test where the
    # agent user had just created a new job:

    assert "bob has made a new maintenance request." in email.body
    assert "Date: 2022-01-01" in email.body
    assert "Address Details:\n\n1234 Main St, Springfield, IL" in email.body
    assert "GPS Link:\n\nhttps://www.google.com/maps" in email.body
    assert "Quote Request Details:\n\nReplace the kitchen sink" in email.body
    assert (
        "PS: This mail is sent from an unmonitored email address. "
        "Please do not reply to this email." in email.body
    )

    # Check the mail attachment
    assert len(email.attachments) == 1
    attachment = email.attachments[0]
    assert attachment[0] == "quotes/test.pdf"
    assert attachment[1] == BASIC_TEST_PDF_FILE.read_bytes()
    assert attachment[2] == "application/pdf"
