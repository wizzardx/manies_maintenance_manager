"""Tests for the "Deposit POP Update" view of the "jobs" app."""

# pylint: disable=magic-value-comparison

from typing import Any

import pytest
from django.contrib.auth.models import AnonymousUser
from django.core import mail
from django.core.exceptions import PermissionDenied
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.test import Client
from django.test import RequestFactory
from django.urls import reverse
from rest_framework import status
from typeguard import check_type

from marnies_maintenance_manager.jobs import constants
from marnies_maintenance_manager.jobs.models import Job
from marnies_maintenance_manager.jobs.tests.conftest import BASIC_TEST_PDF_FILE
from marnies_maintenance_manager.jobs.views.deposit_pop_update_view import (
    DepositPOPUpdateView,
)
from marnies_maintenance_manager.users.models import User

from .utils import assert_email_contains_job_details
from .utils import check_basic_page_html_structure


def test_view_has_correct_basic_structure(
    job_accepted_by_bob: Job,
    bob_agent_user_client: Client,
) -> None:
    """Ensure that the "Deposit POP Update" view has the correct basic structure.

    Args:
        job_accepted_by_bob (Job): A Job instance created by Bob, with an accepted
            quote.
        bob_agent_user_client (Client): The Django test client for Bob.
    """
    check_basic_page_html_structure(
        client=bob_agent_user_client,
        url=reverse("jobs:deposit_pop_update", kwargs={"pk": job_accepted_by_bob.pk}),
        expected_title="Submit Deposit POP",
        expected_template_name="jobs/deposit_pop_update.html",
        expected_h1_text="Submit Deposit POP",
        expected_func_name="view",
        expected_url_name="deposit_pop_update",
        expected_view_class=DepositPOPUpdateView,
    )


def test_anonymous_user_cannot_access_the_view(job_accepted_by_bob: Job) -> None:
    """Ensure that an anonymous user cannot access the "Deposit POP Update" view.

    Args:
        job_accepted_by_bob (Job): Job instance created by Bob, with an accepted quote.
    """
    pk = job_accepted_by_bob.pk
    url = reverse("jobs:deposit_pop_update", kwargs={"pk": pk})
    request = RequestFactory().get(url)
    request.user = AnonymousUser()
    response = check_type(
        DepositPOPUpdateView.as_view()(request, pk=pk),
        HttpResponseRedirect,
    )
    assert response.status_code == status.HTTP_302_FOUND
    assert response.url == f"/accounts/login/?next={url}"


def test_marnie_user_cannot_access_the_view(
    job_accepted_by_bob: Job,
    marnie_user: User,
) -> None:
    """Ensure that Marnie cannot access the "Deposit POP Update" view.

    Args:
        job_accepted_by_bob (Job): Job instance created by Bob, with an accepted quote.
        marnie_user (User): Marnie's user account.
    """
    pk = job_accepted_by_bob.pk
    url = reverse("jobs:deposit_pop_update", kwargs={"pk": pk})
    request = RequestFactory().get(url)
    request.user = marnie_user
    with pytest.raises(PermissionDenied):
        DepositPOPUpdateView.as_view()(request, pk=pk)


def test_agent_who_did_not_create_the_job_cannot_access_the_view(
    job_accepted_by_bob: Job,
    alice_agent_user: User,
) -> None:
    """Ensure agent who didn't create job can't access "Deposit POP Update" view.

    Args:
        job_accepted_by_bob (Job): Job instance created by Bob, with an accepted quote.
        alice_agent_user (User): Alice's user account.
    """
    pk = job_accepted_by_bob.pk
    url = reverse("jobs:deposit_pop_update", kwargs={"pk": pk})
    request = RequestFactory().get(url)
    request.user = alice_agent_user
    with pytest.raises(PermissionDenied):
        DepositPOPUpdateView.as_view()(request, pk=pk)


def test_agent_who_created_the_job_can_access_the_view(
    job_accepted_by_bob: Job,
    bob_agent_user: User,
) -> None:
    """Ensure the agent who created the job can access the "Deposit POP Update" view.

    Args:
        job_accepted_by_bob (Job): Job instance created by Bob, with an accepted quote.
        bob_agent_user (User): Bob's user account.
    """
    access_view_and_assert_status(bob_agent_user, job_accepted_by_bob)


def access_view_and_assert_status(user: User, job: Job) -> None:
    """Access the "Deposit POP Update" view and assert the response status code.

    Args:
        user (User): The user accessing the view.
        job (Job): The job instance.
    """
    pk = job.pk
    url = reverse("jobs:deposit_pop_update", kwargs={"pk": pk})
    request = RequestFactory().get(url)
    request.user = user
    response = DepositPOPUpdateView.as_view()(request, pk=pk)
    assert response.status_code == status.HTTP_200_OK


def test_admin_user_can_access_the_view(
    job_accepted_by_bob: Job,
    admin_user: User,
) -> None:
    """Ensure that an admin user can access the "Deposit POP Update" view.

    Args:
        job_accepted_by_bob (Job): Job instance created by Bob, with an accepted quote.
        admin_user (User): Admin user account.
    """
    access_view_and_assert_status(admin_user, job_accepted_by_bob)


def test_view_has_deposit_proof_of_payment_field(
    job_accepted_by_bob: Job,
    bob_agent_user_client: Client,
) -> None:
    """Ensure that the "Deposit POP Update" view has the deposit_proof_of_payment field.

    Args:
        job_accepted_by_bob (Job): Job instance created by Bob, with an accepted quote.
        bob_agent_user_client (Client): The Django test client for Bob.
    """
    response = check_type(
        bob_agent_user_client.get(
            reverse("jobs:deposit_pop_update", kwargs={"pk": job_accepted_by_bob.pk}),
        ),
        TemplateResponse,
    )
    context_data = check_type(response.context_data, dict[str, Any])
    assert "deposit_proof_of_payment" in context_data["form"].fields


def test_view_has_form_html(
    job_accepted_by_bob: Job,
    bob_agent_user_client: Client,
) -> None:
    """Ensure that the "Deposit POP Update" view has the form HTML.

    Args:
        job_accepted_by_bob (Job): Job instance created by Bob, with an accepted quote.
        bob_agent_user_client (Client): The Django test client for Bob.
    """
    response = bob_agent_user_client.get(
        reverse("jobs:deposit_pop_update", kwargs={"pk": job_accepted_by_bob.pk}),
    )

    form_html = response.content.decode()

    # Ensure that the form HTML contains the necessary elements.
    assert 'id="id_deposit_proof_of_payment"' in form_html
    assert 'name="deposit_proof_of_payment"' in form_html
    assert 'type="file"' in form_html
    assert 'class="form-control"' in form_html

    # Make sure that the form uses the 'POST' method, and that the form will work
    # correctly with a submitted PDF file.
    assert 'method="post"' in form_html
    assert 'enctype="multipart/form-data"' in form_html

    # Check for a "submit" button (not an input control).
    assert "<button" in form_html
    assert 'type="submit"' in form_html
    assert 'class="btn btn-primary"' in form_html
    assert "Submit" in form_html


def test_posting_without_a_file_fails(
    job_accepted_by_bob: Job,
    bob_agent_user_client: Client,
) -> None:
    """Ensure that posting the form without a file fails.

    Args:
        job_accepted_by_bob (Job): Job instance created by Bob, with an accepted quote.
        bob_agent_user_client (Client): The Django test client for Bob.
    """
    response = check_type(
        bob_agent_user_client.post(
            reverse("jobs:deposit_pop_update", kwargs={"pk": job_accepted_by_bob.pk}),
            data={},
        ),
        TemplateResponse,
    )
    assert response.status_code == status.HTTP_200_OK
    context_data = check_type(response.context_data, dict[str, Any])
    assert context_data["form"].errors == {
        "deposit_proof_of_payment": ["This field is required."],
    }


def test_uploading_a_pdf_updates_the_model(
    job_accepted_by_bob: Job,
    bob_agent_user_client: Client,
    test_pdf: SimpleUploadedFile,
) -> None:
    """Ensure that uploading a PDF file updates the Job model.

    Args:
        job_accepted_by_bob (Job): Job instance created by Bob, with an accepted quote.
        bob_agent_user_client (Client): The Django test client for Bob.
        test_pdf (SimpleUploadedFile): A test PDF file.
    """
    # Check that uploading a pdf file, causes the Job model's deposit_proof_of_payment
    # field to be updated.

    # Confirm that the field is not yet populated:
    job = job_accepted_by_bob
    assert job.deposit_proof_of_payment.name == ""

    # Upload the PDF:
    upload_deposit_pop_and_assert_redirect(
        bob_agent_user_client,
        job,
        test_pdf,
    )

    # Fetch the job from the database:
    job.refresh_from_db()

    # Check that the deposit_proof_of_payment field is now set:
    assert job.deposit_proof_of_payment.name == "deposit_pops/test.pdf"

    job.deposit_proof_of_payment.seek(0)
    test_pdf.seek(0)
    assert job.deposit_proof_of_payment.read() == test_pdf.read()


def upload_deposit_pop_and_assert_redirect(
    bob_agent_user_client: Client,
    job_accepted_by_bob: Job,
    test_pdf: SimpleUploadedFile,
) -> None:
    """Upload a Deposit Proof of Payment and assert that the view redirects.

    Args:
        bob_agent_user_client: The Django test client for Bob.
        job_accepted_by_bob: Job instance created by Bob, with an accepted quote.
        test_pdf: A test PDF file.
    """
    test_pdf.seek(0)
    response = check_type(
        bob_agent_user_client.post(
            reverse("jobs:deposit_pop_update", kwargs={"pk": job_accepted_by_bob.pk}),
            data={"deposit_proof_of_payment": test_pdf},
        ),
        HttpResponseRedirect,
    )
    # Check that the response is a redirect:
    assert response.status_code == status.HTTP_302_FOUND
    assert response.url == reverse(
        "jobs:job_detail",
        kwargs={"pk": job_accepted_by_bob.pk},
    )


def test_uploading_a_pdf_with_none_pdf_contents_fails(
    job_accepted_by_bob: Job,
    bob_agent_user_client: Client,
) -> None:
    """Ensure that uploading a PDF file with non-PDF contents fails.

    Args:
        job_accepted_by_bob (Job): Job instance created by Bob, with an accepted quote.
        bob_agent_user_client (Client): The Django test client for Bob.
    """
    test_file = SimpleUploadedFile("test.pdf", b"not a pdf file")
    response = check_type(
        bob_agent_user_client.post(
            reverse("jobs:deposit_pop_update", kwargs={"pk": job_accepted_by_bob.pk}),
            data={"deposit_proof_of_payment": test_file},
        ),
        TemplateResponse,
    )

    assert response.status_code == status.HTTP_200_OK
    context_data = check_type(response.context_data, dict[str, Any])
    assert context_data["form"].errors == {
        "deposit_proof_of_payment": ["This is not a valid PDF file"],
    }


def test_uploading_a_non_pdf_file_with_pdf_contents_fails(
    job_accepted_by_bob: Job,
    bob_agent_user_client: Client,
    test_pdf: SimpleUploadedFile,
) -> None:
    """Ensure that uploading a non-PDF file with PDF contents fails.

    Args:
        job_accepted_by_bob (Job): Job instance created by Bob, with an accepted quote.
        bob_agent_user_client (Client): The Django test client for Bob.
        test_pdf (SimpleUploadedFile): A test PDF file.
    """
    test_pdf.seek(0)
    pdf_data = test_pdf.read()

    test_pdf_2 = SimpleUploadedFile("test.txt", pdf_data)

    # Test this upload - where the contents are pdf, but the file extension is txt
    response = check_type(
        bob_agent_user_client.post(
            reverse("jobs:deposit_pop_update", kwargs={"pk": job_accepted_by_bob.pk}),
            data={"deposit_proof_of_payment": test_pdf_2},
        ),
        TemplateResponse,
    )

    assert response.status_code == status.HTTP_200_OK
    context_data = check_type(response.context_data, dict[str, Any])
    assert context_data["form"].errors == {
        "deposit_proof_of_payment": [
            "File extension “txt” is not allowed. Allowed extensions are: pdf.",
        ],
    }


def test_sends_an_email(
    job_accepted_by_bob: Job,
    bob_agent_user_client: Client,
    test_pdf: SimpleUploadedFile,
    marnie_user: User,
    bob_agent_user: User,
) -> None:
    """Ensure that an email is sent when the form is submitted.

    Args:
        job_accepted_by_bob (Job): Job instance created by Bob, with an accepted quote.
        bob_agent_user_client (Client): The Django test client for Bob.
        test_pdf (SimpleUploadedFile): A test PDF file.
        marnie_user (User): Marnie's user account.
        bob_agent_user (User): Bob's user account.
    """
    # Clear records of any already-sent emails:
    mail.outbox.clear()

    # Submit the form:
    upload_deposit_pop_and_assert_redirect(
        bob_agent_user_client,
        job_accepted_by_bob,
        test_pdf,
    )

    # There should be one mail sent now;
    assert len(mail.outbox) == 1

    # Grab the mail:
    email = mail.outbox[0]

    # Check mail metadata:
    assert email.subject == "Agent bob added a Deposit POP to the maintenance request"
    assert marnie_user.email in email.to
    assert bob_agent_user.email in email.cc
    assert constants.DEFAULT_FROM_EMAIL in email.from_email

    # Check mail contents:
    assert (
        "Agent bob added a Deposit POP to the maintenance request. The POP "
        "is attached to this email." in email.body
    )

    # There should now be exactly one job in the database. Fetch it so that we can
    # use it to check the email body.
    attach_name, attachment = assert_email_contains_job_details(email)
    assert attach_name.startswith("deposit_pops/test"), attach_name
    assert attach_name.endswith(".pdf")
    assert attachment[1] == BASIC_TEST_PDF_FILE.read_bytes()
    assert attachment[2] == "application/pdf"


def test_sends_a_success_flash_message(
    job_accepted_by_bob: Job,
    bob_agent_user_client: Client,
    test_pdf: SimpleUploadedFile,
) -> None:
    """Ensure that a success flash message is sent when the form is submitted.

    Args:
        job_accepted_by_bob (Job): Job instance created by Bob, with an accepted quote.
        bob_agent_user_client (Client): The Django test client for Bob.
        test_pdf (SimpleUploadedFile): A test PDF file.
    """
    # Submit the form:
    test_pdf.seek(0)
    response = bob_agent_user_client.post(
        reverse("jobs:deposit_pop_update", kwargs={"pk": job_accepted_by_bob.pk}),
        data={"deposit_proof_of_payment": test_pdf},
        follow=True,
    )
    assert response.status_code == status.HTTP_200_OK

    messages = response.context["messages"]
    assert len(messages) == 1
    message = next(iter(messages))
    assert message.message == (
        "Your Deposit Proof of Payment has been uploaded. An email has been sent "
        "to Marnie."
    )
    assert message.tags == "success"


def test_changes_job_state_to_deposit_pop_uploaded(
    job_accepted_by_bob: Job,
    bob_agent_user_client: Client,
    test_pdf: SimpleUploadedFile,
) -> None:
    """Ensure the job state changes to DEPOSIT_POP_UPLOADED upon form submission.

    Args:
        job_accepted_by_bob (Job): Job instance created by Bob, with an accepted quote.
        bob_agent_user_client (Client): The Django test client for Bob.
        test_pdf (SimpleUploadedFile): A test PDF file.
    """
    # Submit the form:
    test_pdf.seek(0)
    job = job_accepted_by_bob
    response = bob_agent_user_client.post(
        reverse("jobs:deposit_pop_update", kwargs={"pk": job.pk}),
        data={"deposit_proof_of_payment": test_pdf},
        follow=True,
    )
    assert response.status_code == status.HTTP_200_OK

    # Fetch the job from the database:
    job.refresh_from_db()

    # Check that the job status was updated correctly:
    assert job.status == Job.Status.DEPOSIT_POP_UPLOADED.value


def assert_permission_denied_if_job_not_in_correct_initial_state(
    job: Job,
    user: User,
    expected_status: str,
) -> None:
    """Ensure PermissionDenied is raised if the job is not in the correct initial state.

    Args:
        job (Job): Job instance with a specific status.
        user (User): User accessing the view.
        expected_status (str): The status that is considered incorrect.
    """
    job.status = expected_status
    job.save()
    request = RequestFactory().get(
        reverse("jobs:deposit_pop_update", kwargs={"pk": job.pk}),
    )
    request.user = user
    with pytest.raises(PermissionDenied):
        DepositPOPUpdateView.as_view()(request, pk=job.pk)


def test_permission_denied_if_the_job_is_not_in_expected_state_at_start(
    job_accepted_by_bob: Job,
    bob_agent_user: User,
) -> None:
    """Ensure PermissionDenied is raised if the job is not in the correct initial state.

    Args:
        job_accepted_by_bob (Job): Job instance created by Bob, with an accepted quote.
        bob_agent_user (User): Bob's user account.
    """
    assert_permission_denied_if_job_not_in_correct_initial_state(
        job_accepted_by_bob,
        bob_agent_user,
        Job.Status.DEPOSIT_POP_UPLOADED.value,
    )


def test_permission_denied_if_pop_field_already_populated_at_start(
    bob_job_with_deposit_pop: Job,
    bob_agent_user: User,
) -> None:
    """Ensure PermissionDenied is raised if deposit_proof_of_payment is filled.

    Args:
        bob_job_with_deposit_pop (Job): Job instance created by Bob, with a deposit
            proof of payment.
        bob_agent_user (User): Bob's user account.
    """
    assert_permission_denied_if_job_not_in_correct_initial_state(
        bob_job_with_deposit_pop,
        bob_agent_user,
        Job.Status.QUOTE_ACCEPTED_BY_AGENT.value,
    )
