"""Tests for the "Upload Final Payment Proof of Payment" view."""

# pylint: disable=magic-value-comparison

from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpResponseForbidden
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.test import Client
from django.urls import reverse
from rest_framework import status
from typeguard import check_type

from marnies_maintenance_manager.jobs import constants
from marnies_maintenance_manager.jobs.models import Job
from marnies_maintenance_manager.jobs.tests.conftest import BASIC_TEST_PDF_FILE
from marnies_maintenance_manager.jobs.utils import safe_read
from marnies_maintenance_manager.jobs.views.final_payment_pop_update_view import (
    FinalPaymentPOPUpdateView,
)
from marnies_maintenance_manager.users.models import User

from .utils import assert_email_contains_job_details
from .utils import check_basic_page_html_structure


def test_view_has_correct_basic_structure(
    bob_job_completed_by_marnie: Job,
    bob_agent_user_client: Client,
) -> None:
    """Ensure that the "Download Deposit POP" view has the correct basic structure.

    Args:
        bob_job_completed_by_marnie (Job): A Job instance completed by Marnie.
        bob_agent_user_client (Client): The Django test client for Bob.
    """
    check_basic_page_html_structure(
        client=bob_agent_user_client,
        url=reverse(
            "jobs:final_payment_pop_update",
            kwargs={"pk": bob_job_completed_by_marnie.pk},
        ),
        expected_title="Upload Final Payment Proof of Payment",
        expected_template_name="jobs/final_payment_pop_update.html",
        expected_h1_text="Upload Final Payment Proof of Payment",
        expected_func_name="view",
        expected_url_name="final_payment_pop_update",
        expected_view_class=FinalPaymentPOPUpdateView,
    )


def test_anonymous_user_cannot_access_view(
    job_accepted_by_bob: Job,
    client: Client,
) -> None:
    """Ensure that an anonymous user cannot access the "Upload Final Payment POP" view.

    Args:
        job_accepted_by_bob (Job): A Job instance created by Bob, with an accepted
            quote.
        client (Client): The Django test client.
    """
    response = check_type(
        client.get(
            reverse(
                "jobs:final_payment_pop_update",
                kwargs={"pk": job_accepted_by_bob.pk},
            ),
        ),
        HttpResponseRedirect,
    )
    assert response.status_code == status.HTTP_302_FOUND
    assert (
        response.url == f"/accounts/login/?next=/jobs/{job_accepted_by_bob.pk}/"
        "final-payment-pop/update/"
    )


def test_marnie_user_cannot_access_view(
    job_accepted_by_bob: Job,
    marnie_user_client: Client,
) -> None:
    """Ensure Marnie cannot access the "Upload Final Payment POP" view.

    Args:
        job_accepted_by_bob (Job): A Job instance created by Bob, with an accepted
            quote.
        marnie_user_client (Client): The Django test client for Marnie.
    """
    response = check_type(
        marnie_user_client.get(
            reverse(
                "jobs:final_payment_pop_update",
                kwargs={"pk": job_accepted_by_bob.pk},
            ),
        ),
        HttpResponseRedirect | TemplateResponse | HttpResponseForbidden,
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_superuser_can_access_view(
    bob_job_completed_by_marnie: Job,
    superuser_client: Client,
) -> None:
    """Ensure a superuser can access the "Upload Final Payment POP" view.

    Args:
        bob_job_completed_by_marnie (Job): A Job instance completed by Marnie.
        superuser_client (Client): The Django test client for the superuser.
    """
    response = superuser_client.get(
        reverse(
            "jobs:final_payment_pop_update",
            kwargs={"pk": bob_job_completed_by_marnie.pk},
        ),
    )
    assert response.status_code == status.HTTP_200_OK


def test_agent_who_created_job_can_access_view(
    bob_job_completed_by_marnie: Job,
    bob_agent_user_client: Client,
) -> None:
    """Deny access to agents who did not create the job.

    Args:
        bob_job_completed_by_marnie (Job): A Job instance completed by Marnie.
        bob_agent_user_client (Client): The Django test client for Bob.
    """
    response = bob_agent_user_client.get(
        reverse(
            "jobs:final_payment_pop_update",
            kwargs={"pk": bob_job_completed_by_marnie.pk},
        ),
    )
    assert response.status_code == status.HTTP_200_OK


def test_agent_who_did_not_create_job_cannot_access_view(
    job_accepted_by_bob: Job,
    alice_agent_user_client: Client,
) -> None:
    """Deny access to agents who did not create the job.

    Args:
        job_accepted_by_bob (Job): A Job instance created by Bob, with an accepted
            quote.
        alice_agent_user_client (Client): The Django test client for Alice.
    """
    response = alice_agent_user_client.get(
        reverse("jobs:final_payment_pop_update", kwargs={"pk": job_accepted_by_bob.pk}),
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_view_accessible_if_job_in_marnie_completed_state(
    bob_job_completed_by_marnie: Job,
    bob_agent_user_client: Client,
) -> None:
    """Block view if job isn't in the "Completed by Marnie" state.

    Args:
        bob_job_completed_by_marnie (Job): A Job instance completed by Marnie.
        bob_agent_user_client (Client): The Django test client for agent Bob.
    """
    response = bob_agent_user_client.get(
        reverse(
            "jobs:final_payment_pop_update",
            kwargs={"pk": bob_job_completed_by_marnie.pk},
        ),
    )
    assert response.status_code == status.HTTP_200_OK


def test_view_not_accessible_if_job_not_in_completed_state(
    job_accepted_by_bob: Job,
    bob_agent_user_client: Client,
) -> None:
    """Block view if job isn't in the "Completed by Marnie" state.

    Args:
        job_accepted_by_bob (Job): A Job instance created by Bob, with an accepted
            quote.
        bob_agent_user_client (Client): The Django test client for Bob.
    """
    response = bob_agent_user_client.get(
        reverse("jobs:final_payment_pop_update", kwargs={"pk": job_accepted_by_bob.pk}),
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_view_accessible_if_job_in_completed_state(
    bob_job_completed_by_marnie: Job,
    bob_agent_user_client: Client,
) -> None:
    """Ensure view access if job is in the "Completed" state.

    Args:
        bob_job_completed_by_marnie (Job): A Job instance completed by Marnie.
        bob_agent_user_client (Client): The Django test client for agent Bob.
    """
    job = bob_job_completed_by_marnie
    response = bob_agent_user_client.get(
        reverse("jobs:final_payment_pop_update", kwargs={"pk": job.pk}),
    )
    assert response.status_code == status.HTTP_200_OK


def test_view_not_accessible_if_final_payment_pop_already_uploaded(
    bob_job_completed_by_marnie: Job,
    bob_agent_user_client: Client,
    test_pdf: SimpleUploadedFile,
) -> None:
    """Check if view blocks access when final payment POP is uploaded.

    Args:
        bob_job_completed_by_marnie (Job): A Job instance completed by Marnie
        bob_agent_user_client (Client): The Django test client for agent Bob.
        test_pdf (SimpleUploadedFile): A test PDF file.
    """
    # An update here to help put the job in the correct state
    job = bob_job_completed_by_marnie
    job.final_payment_pop = test_pdf
    with safe_read(test_pdf):
        bob_job_completed_by_marnie.save()

    response = bob_agent_user_client.get(
        reverse("jobs:final_payment_pop_update", kwargs={"pk": job.pk}),
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_changes_state_to_final_payment_pop_uploaded(
    bob_job_completed_by_marnie: Job,
    bob_agent_user_client: Client,
    test_pdf: SimpleUploadedFile,
) -> None:
    """Ensure job's state changes to "Final Payment POP Uploaded" after upload.

    Args:
        bob_job_completed_by_marnie (Job): A Job instance completed by Marnie.
        bob_agent_user_client (Client): The Django test client for Bob.
        test_pdf (SimpleUploadedFile): A test PDF file.
    """
    job = bob_job_completed_by_marnie
    upload_final_payment_pop(bob_agent_user_client, job, test_pdf)

    job.refresh_from_db()
    assert job.status == Job.Status.FINAL_PAYMENT_POP_UPLOADED.value


def upload_final_payment_pop(
    client: Client,
    job: Job,
    test_pdf: SimpleUploadedFile,
) -> TemplateResponse:
    """Upload the final payment POP and return the response.

    Args:
        client (Client): The Django test client.
        job (Job): The Job instance.
        test_pdf (SimpleUploadedFile): The test PDF file.

    Returns:
        TemplateResponse: The HTTP response.
    """
    with safe_read(test_pdf):
        response = client.post(
            reverse("jobs:final_payment_pop_update", kwargs={"pk": job.pk}),
            data={"final_payment_pop": test_pdf},
            follow=True,
        )
    assert response.status_code == status.HTTP_200_OK
    assert response.redirect_chain == [(job.get_absolute_url(), status.HTTP_302_FOUND)]
    return check_type(response, TemplateResponse)


def test_sends_an_email(
    bob_job_completed_by_marnie: Job,
    bob_agent_user_client: Client,
    test_pdf: SimpleUploadedFile,
    marnie_user: User,
    bob_agent_user: User,
) -> None:
    """Ensure that an email is sent when the form is submitted.

    Args:
        bob_job_completed_by_marnie (Job): A Job instance completed by Marnie.
        bob_agent_user_client (Client): The Django test client for Bob.
        test_pdf (SimpleUploadedFile): A test PDF file.
        marnie_user (User): Marnie's user account.
        bob_agent_user (User): Bob's user account.
    """
    job = bob_job_completed_by_marnie
    # Clear records of any already-sent emails:
    mail.outbox.clear()

    upload_final_payment_pop(bob_agent_user_client, job, test_pdf)

    # There should be one mail sent now:
    assert len(mail.outbox) == 1

    # Grab the mail:
    email = mail.outbox[0]

    # Check mail metadata:
    assert (
        email.subject
        == "Agent bob added a Final Payment POP to the maintenance request"
    )
    assert marnie_user.email in email.to
    assert bob_agent_user.email in email.cc
    assert constants.DEFAULT_FROM_EMAIL in email.from_email

    # Check mail contents:
    assert (
        "Agent bob added a Final Payment POP to the maintenance request. The POP "
        "is attached to this email." in email.body
    )

    # There should now be exactly one job in the database. Fetch it so that we can
    # use it to check the email body.
    attach_name, attachment = assert_email_contains_job_details(email)
    assert attach_name.startswith("final_payment_pops/test"), attach_name
    assert attach_name.endswith(".pdf")
    assert attachment[1] == BASIC_TEST_PDF_FILE.read_bytes()
    assert attachment[2] == "application/pdf"


def test_sends_a_success_flash_message(
    bob_job_completed_by_marnie: Job,
    bob_agent_user_client: Client,
    test_pdf: SimpleUploadedFile,
) -> None:
    """Ensure that a success flash message is sent when the form is submitted.

    Args:
        bob_job_completed_by_marnie (Job): A Job instance completed by Marnie.
        bob_agent_user_client (Client): The Django test client for Bob.
        test_pdf (SimpleUploadedFile): A test PDF file.
    """
    # Submit the form:
    job = bob_job_completed_by_marnie
    response = upload_final_payment_pop(bob_agent_user_client, job, test_pdf)

    messages = response.context["messages"]
    assert len(messages) == 1
    message = next(iter(messages))
    assert message.message == (
        "Your Final Payment Proof of Payment has been uploaded. An email has been sent "
        "to Marnie."
    )
    assert message.tags == "success"
