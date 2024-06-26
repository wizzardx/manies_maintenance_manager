"""Tests for the QuoteUpdateView view."""

# pylint: disable=magic-value-comparison

from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpResponseRedirect
from django.test import Client
from django.urls import reverse
from rest_framework import status

from marnies_maintenance_manager.jobs import constants
from marnies_maintenance_manager.jobs.models import Job
from marnies_maintenance_manager.jobs.tests.conftest import BASIC_TEST_PDF_FILE_2
from marnies_maintenance_manager.jobs.utils import safe_read
from marnies_maintenance_manager.jobs.views.quote_update_view import QuoteUpdateView
from marnies_maintenance_manager.users.models import User

from .utils import assert_email_contains_job_details
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
        url=reverse("jobs:quote_update", kwargs={"pk": job_rejected_by_bob.pk}),
        expected_title="Update Quote",
        expected_template_name="jobs/quote_update.html",
        expected_h1_text="Update Quote",
        expected_func_name="view",
        expected_url_name="quote_update",
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
        reverse("jobs:quote_update", kwargs={"pk": job_rejected_by_bob.pk}),
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
        reverse("jobs:quote_update", kwargs={"pk": job_rejected_by_bob.pk}),
    )
    assert response.status_code == status.HTTP_302_FOUND
    assert isinstance(response, HttpResponseRedirect)
    assert (
        response.url
        == f"/accounts/login/?next=/jobs/{job_rejected_by_bob.pk}/quote/update/"
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
    with safe_read(job_rejected_by_bob.quote, test_pdf):
        assert job_rejected_by_bob.quote.read() == test_pdf.read()

    submit_quote_update_and_check_redirect(
        job_rejected_by_bob,
        marnie_user_client,
        test_pdf_2,
    )

    job_rejected_by_bob.refresh_from_db()

    with safe_read(job_rejected_by_bob.quote, test_pdf_2):
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
        reverse("jobs:quote_update", kwargs={"pk": job_rejected_by_bob.pk}),
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
    with safe_read(job_rejected_by_bob.quote, test_pdf):
        assert job_rejected_by_bob.quote.read() == test_pdf.read()

    # Attempt to re-upload the same PDF file:
    with safe_read(test_pdf):
        response = superuser_client.post(
            reverse("jobs:quote_update", kwargs={"pk": job_rejected_by_bob.pk}),
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
    submit_quote_update_and_check_redirect(
        job_rejected_by_bob,
        marnie_user_client,
        test_pdf_2,
    )


def submit_quote_update_and_check_redirect(
    job: Job,
    client: Client,
    attachment: SimpleUploadedFile,
) -> None:
    """Submit a quote update and check that the view redirects to the job detail view.

    Args:
        job (Job): A Job instance.
        client (Client): A Django test client.
        attachment (SimpleUploadedFile): A test PDF file.
    """
    with safe_read(attachment):
        response = client.post(
            reverse("jobs:quote_update", kwargs={"pk": job.pk}),
            data={"quote": attachment},
        )

    assert response.status_code == status.HTTP_302_FOUND
    assert isinstance(response, HttpResponseRedirect)
    assert response.url == reverse(
        "jobs:job_detail",
        kwargs={"pk": job.pk},
    )


def submit_quote_update(
    client: Client,
    job: Job,
    attachment: SimpleUploadedFile,
    expected_status_code: int,
) -> None:
    """Submit a quote update and assert the response status code.

    Args:
        client (Client): A Django test client.
        job (Job): A Job instance.
        attachment (SimpleUploadedFile): A test PDF file.
        expected_status_code (int): The expected HTTP status code.
    """
    with safe_read(attachment):
        response = client.post(
            reverse("jobs:quote_update", kwargs={"pk": job.pk}),
            data={"quote": attachment},
        )

    assert response.status_code == expected_status_code


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
        bob_agent_user (User): The agent user created by Bob.
        marnie_user (User): The Marnie user.
    """
    # Clear mails before we run our logic under test:
    mail.outbox.clear()

    # As Marnie, upload a new quote.
    submit_quote_update(
        marnie_user_client,
        job_rejected_by_bob,
        test_pdf_2,
        status.HTTP_302_FOUND,
    )

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
    attach_name, attachment = assert_email_contains_job_details(email)
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
    with safe_read(test_pdf_2):
        response = marnie_user_client.post(
            reverse("jobs:quote_update", kwargs={"pk": job_rejected_by_bob.pk}),
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


def test_does_not_work_if_not_in_quote_rejected_state(
    bob_job_with_initial_marnie_inspection: Job,
    marnie_user_client: Client,
    test_pdf_2: SimpleUploadedFile,
) -> None:
    """Test that the view does not work if the job is not in the "quote rejected" state.

    Args:
        bob_job_with_initial_marnie_inspection (Job): A Job instance created by Bob,
            with an initial Marnie inspection.
        marnie_user_client (Client): The Django test client for Marnie.
        test_pdf_2 (SimpleUploadedFile): A test PDF file.
    """
    submit_quote_update(
        marnie_user_client,
        bob_job_with_initial_marnie_inspection,
        test_pdf_2,
        status.HTTP_403_FORBIDDEN,
    )


def test_quote_field_is_required(
    job_rejected_by_bob: Job,
    marnie_user_client: Client,
) -> None:
    """Test that the quote field is required.

    Args:
        job_rejected_by_bob (Job): A Job instance created by Bob, with a rejected quote.
        marnie_user_client (Client): The Django test client for Marnie.
    """
    # The quote field is provided by default (this is technically an "UpdateView"-
    # descended view, where - by business logic we've already ensured there is a quote).
    # So we need to make sure we remove any already-uploaded quote from the job.
    job_rejected_by_bob.quote.delete(save=True)

    response = marnie_user_client.post(
        reverse("jobs:quote_update", kwargs={"pk": job_rejected_by_bob.pk}),
        data={},
    )

    assert response.status_code == status.HTTP_200_OK
    assert response.context["form"].errors == {
        "quote": ["This field is required."],
    }
