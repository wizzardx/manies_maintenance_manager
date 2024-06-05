"""Tests for the QuoteUpdateView view."""

from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpResponseRedirect
from django.test import Client
from django.urls import reverse
from rest_framework import status

from marnies_maintenance_manager.jobs import constants
from marnies_maintenance_manager.jobs.models import Job
from marnies_maintenance_manager.jobs.tests.conftest import BASIC_TEST_PDF_FILE_2
from marnies_maintenance_manager.jobs.views.update_quote_view import QuoteUpdateView
from marnies_maintenance_manager.users.models import User

from .utils import check_basic_page_html_structure


def test_view_has_correct_basic_structure(
    job_rejected_by_bob: Job,
    marnie_user_client: Client,
) -> None:
    """Ensure that the quote update view has the correct basic structure.

    Args:
        job_rejected_by_bob (Job): A Job instance created by Bob, with a rejected quote.
        marnie_user_client (Client): The Django test client for Marnie.
    """
    check_basic_page_html_structure(
        client=marnie_user_client,
        url=reverse("jobs:update_quote", kwargs={"pk": job_rejected_by_bob.pk}),
        expected_title="Update Quote",
        expected_template_name="jobs/update_quote.html",
        expected_h1_text="Update Quote",
        expected_func_name="view",
        expected_url_name="update_quote",
        expected_view_class=QuoteUpdateView,
    )


def test_agent_cannot_use_the_view(
    job_rejected_by_bob: Job,
    bob_agent_user_client: Client,
) -> None:
    """Test that Bob cannot access the quote update view.

    Args:
        job_rejected_by_bob (Job): A Job instance created by Bob, with a rejected quote.
        bob_agent_user_client (Client): The Django test client for Bob.
    """
    response = bob_agent_user_client.get(
        reverse("jobs:update_quote", kwargs={"pk": job_rejected_by_bob.pk}),
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_must_be_logged_in_to_use_the_view(
    job_rejected_by_bob: Job,
    client: Client,
) -> None:
    """Test that a user must be logged in to access the quote update view.

    Args:
        job_rejected_by_bob (Job): A Job instance created by Bob, with a rejected quote.
        client (Client): The Django test client.
    """
    response = client.get(
        reverse("jobs:update_quote", kwargs={"pk": job_rejected_by_bob.pk}),
    )
    assert response.status_code == status.HTTP_302_FOUND
    assert isinstance(response, HttpResponseRedirect)
    assert (
        response.url
        == f"/accounts/login/?next=/jobs/{job_rejected_by_bob.pk}/update-quote/"
    )


def test_view_updates_the_quote_field_on_the_job(
    job_rejected_by_bob: Job,
    marnie_user_client: Client,
    test_pdf: SimpleUploadedFile,
    test_pdf_2: SimpleUploadedFile,
) -> None:
    """Test that the view updates the quote field on the job.

    Args:
        job_rejected_by_bob (Job): A Job instance created by Bob, with a rejected quote.
        marnie_user_client (Client): The Django test client for Marnie.
        test_pdf (SimpleUploadedFile): A test PDF file.
        test_pdf_2 (SimpleUploadedFile): A test PDF file.
    """
    # Check before our test, that Job.quote (a FileField), has the same contents as the
    # original testing PDF file.
    test_pdf.seek(0)
    assert job_rejected_by_bob.quote.read() == test_pdf.read()

    response = marnie_user_client.post(
        reverse("jobs:update_quote", kwargs={"pk": job_rejected_by_bob.pk}),
        data={"quote": test_pdf_2},
    )

    assert response.status_code == status.HTTP_302_FOUND
    assert isinstance(response, HttpResponseRedirect)
    assert response.url == reverse(
        "jobs:job_detail",
        kwargs={"pk": job_rejected_by_bob.pk},
    )
    job_rejected_by_bob.refresh_from_db()

    test_pdf_2.seek(0)
    assert job_rejected_by_bob.quote.read() == test_pdf_2.read()


def test_admin_can_use_the_view(
    job_rejected_by_bob: Job,
    superuser_client: Client,
) -> None:
    """Test that an admin user can access the quote update view.

    Args:
        job_rejected_by_bob (Job): A Job instance created by Bob, with a rejected quote.
        superuser_client (Client): The Django test client for the superuser.
    """
    response = superuser_client.get(
        reverse("jobs:update_quote", kwargs={"pk": job_rejected_by_bob.pk}),
    )
    assert response.status_code == status.HTTP_200_OK


def test_cannot_resubmit_the_same_quote(
    job_rejected_by_bob: Job,
    superuser_client: Client,
    test_pdf: SimpleUploadedFile,
) -> None:
    """Test that a user cannot resubmit the same quote.

    Args:
        job_rejected_by_bob (Job): A Job instance created by Bob, with a rejected quote.
        superuser_client (Client): The Django test client for the superuser.
        test_pdf (SimpleUploadedFile): A test PDF file.
    """
    # Confirm the PDF file before we attempt to re-upload it:
    test_pdf.seek(0)
    assert job_rejected_by_bob.quote.read() == test_pdf.read()

    # Attempt to re-upload the same PDF file:
    test_pdf.seek(0)
    response = superuser_client.post(
        reverse("jobs:update_quote", kwargs={"pk": job_rejected_by_bob.pk}),
        data={"quote": test_pdf},
    )

    # Confirm that the response is an HTTP 200 status code, and that the form has an
    # error:
    assert response.status_code == status.HTTP_200_OK
    assert response.context["form"].errors == {
        "quote": ["You must provide a new quote"],
    }


def test_on_success_redirects_to_the_detail_view(
    job_rejected_by_bob: Job,
    marnie_user_client: Client,
    test_pdf_2: SimpleUploadedFile,
) -> None:
    """Test that the view redirects to the job detail view on success.

    Args:
        job_rejected_by_bob (Job): A Job instance created by Bob, with a rejected quote.
        marnie_user_client (Client): The Django test client for Marnie.
        test_pdf_2 (SimpleUploadedFile): A test PDF file.
    """
    response = marnie_user_client.post(
        reverse("jobs:update_quote", kwargs={"pk": job_rejected_by_bob.pk}),
        data={"quote": test_pdf_2},
    )
    assert response.status_code == status.HTTP_302_FOUND
    assert isinstance(response, HttpResponseRedirect)
    assert response.url == reverse(
        "jobs:job_detail",
        kwargs={"pk": job_rejected_by_bob.pk},
    )


def test_on_success_sends_an_email_to_the_agent(
    job_rejected_by_bob: Job,
    marnie_user_client: Client,
    test_pdf_2: SimpleUploadedFile,
    bob_agent_user: User,
    marnie_user: User,
) -> None:
    """Test that the view sends an email to the agent on success.

    Args:
        job_rejected_by_bob (Job): A Job instance created by Bob, with a rejected quote.
        marnie_user_client (Client): The Django test client for Marnie.
        test_pdf_2 (SimpleUploadedFile): A test PDF file.
    """
    # Clear mails before we run our logic under test:
    mail.outbox.clear()

    # As Marnie, upload a new quote.
    response = marnie_user_client.post(
        reverse("jobs:update_quote", kwargs={"pk": job_rejected_by_bob.pk}),
        data={"quote": test_pdf_2},
    )
    assert response.status_code == status.HTTP_302_FOUND

    # Check that the appropriate email was sent:
    assert len(mail.outbox) == 1
    email = mail.outbox[0]

    # Check mail metadata:
    assert email.subject == "Marnie uploaded an updated quote for your job"
    assert bob_agent_user.email in email.to
    assert marnie_user.email in email.cc
    assert constants.DEFAULT_FROM_EMAIL in email.from_email

    # Check mail contents:
    assert (
        "Marnie uploaded a new quote for a maintenance job. The quote "
        "is attached to this email." in email.body
    )

    # There should now be exactly one job in the database. Fetch it so that we can
    # use it to check the email body.
    job = Job.objects.get()

    # Check that there's a link to the job detail view in the email body:
    job_id = str(job.id)
    assert (
        f"Details of the job can be found at: http://testserver/jobs/{job_id}/"
        in email.body
    )

    assert "Details of your original request:" in email.body

    # A separator line:
    assert "-----" in email.body

    # The original mail subject line, as a line in the body:
    assert "Subject: New maintenance request by bob" in email.body

    # And all the original body lines, too, as per our previous test where the
    # agent user had just created a new job:

    assert "bob has made a new maintenance request." in email.body
    assert "Number: 1" in email.body
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

    # Attachment name can be something like one of these:
    # - quotes/test_2_r8TJrLv.pdf
    # - quotes/test_2.pdf
    attach_name = attachment[0]
    assert attach_name.startswith("quotes/test_2"), attach_name
    assert attach_name.endswith(".pdf")
    assert attachment[1] == BASIC_TEST_PDF_FILE_2.read_bytes()
    assert attachment[2] == "application/pdf"


def test_on_success_sends_flash_message(
    job_rejected_by_bob: Job,
    marnie_user_client: Client,
    test_pdf_2: SimpleUploadedFile,
) -> None:
    """Test that the view sends a flash message on success.

    Args:
        job_rejected_by_bob (Job): A Job instance created by Bob, with a rejected quote.
        marnie_user_client (Client): The Django test client for Marnie.
        test_pdf_2 (SimpleUploadedFile): A test PDF file.
    """
    response = marnie_user_client.post(
        reverse("jobs:update_quote", kwargs={"pk": job_rejected_by_bob.pk}),
        data={"quote": test_pdf_2},
        follow=True,
    )
    assert response.status_code == status.HTTP_200_OK

    messages = response.context["messages"]
    assert len(messages) == 1
    message = next(iter(messages))
    assert (
        message.message
        == "Your updated quote has been uploaded. An email has been sent to bob."
    )
    assert message.tags == "success"
