"""Tests for the "Deposit POP Update" view of the "jobs" app."""

# pylint: disable=magic-value-comparison

from typing import Any

import pytest
from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import PermissionDenied
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.test import Client
from django.test import RequestFactory
from django.urls import reverse
from rest_framework import status
from typeguard import check_type

from marnies_maintenance_manager.jobs.models import Job
from marnies_maintenance_manager.jobs.views.deposit_pop_update_view import (
    DepositPOPUpdateView,
)
from marnies_maintenance_manager.users.models import User

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
    peter_agent_user: User,
) -> None:
    """Ensure agent who didn't create job can't access "Deposit POP Update" view.

    Args:
        job_accepted_by_bob (Job): Job instance created by Bob, with an accepted quote.
        peter_agent_user (User): Peter's user account.
    """
    pk = job_accepted_by_bob.pk
    url = reverse("jobs:deposit_pop_update", kwargs={"pk": pk})
    request = RequestFactory().get(url)
    request.user = peter_agent_user
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
