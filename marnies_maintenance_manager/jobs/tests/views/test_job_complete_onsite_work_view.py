"""Tests for the JobCompleteView view."""

# pylint: disable=magic-value-comparison

import datetime

from django.core import mail
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.test import Client
from django.urls import reverse
from rest_framework import status
from typeguard import check_type

from marnies_maintenance_manager.jobs import constants
from marnies_maintenance_manager.jobs.models import Job
from marnies_maintenance_manager.jobs.tests.views.utils import assert_no_form_errors
from marnies_maintenance_manager.jobs.tests.views.utils import (
    check_basic_page_html_structure,
)
from marnies_maintenance_manager.jobs.views.job_complete_onsite_work_view import (
    JobCompleteOnsiteWorkView,
)
from marnies_maintenance_manager.users.models import User


def test_anonymous_users_are_redirected_to_login_page(
    client: Client,
    bob_job_with_deposit_pop: Job,
) -> None:
    """Ensure anonymous users are redirected to the login page.

    Args:
        client (Client): The Django test client.
        bob_job_with_deposit_pop (Job): The job created by Bob with the deposit POP.
    """
    response = check_type(
        client.get(
            reverse(
                "jobs:job_complete_onsite_work",
                kwargs={"pk": bob_job_with_deposit_pop.pk},
            ),
        ),
        HttpResponseRedirect | TemplateResponse,
    )
    assert response.status_code == status.HTTP_302_FOUND
    assert response.url == (
        f"/accounts/login/?next=/jobs/{bob_job_with_deposit_pop.pk}/"
        "complete_onsite_work/"
    )


def test_view_is_accessible_by_marnie_when_pop_has_been_uploaded(
    bob_job_with_deposit_pop: Job,
    marnie_user_client: Client,
) -> None:
    """Ensure Marnie can access the view after the admin uploaded the POP.

    Args:
        bob_job_with_deposit_pop (Job): The job created by Bob with the deposit POP.
        marnie_user_client (Client): The Django test client for Marnie.
    """
    response = marnie_user_client.get(
        reverse(
            "jobs:job_complete_onsite_work",
            kwargs={"pk": bob_job_with_deposit_pop.pk},
        ),
    )
    assert response.status_code == status.HTTP_200_OK


def test_view_is_inaccessible_by_agents(
    bob_job_with_deposit_pop: Job,
    bob_agent_user_client: Client,
) -> None:
    """Ensure agents cannot access the view.

    Args:
        bob_job_with_deposit_pop (Job): The job created by Bob with the deposit POP.
        bob_agent_user_client (Client): The Django test client for Bob.
    """
    response = bob_agent_user_client.get(
        reverse(
            "jobs:job_complete_onsite_work",
            kwargs={"pk": bob_job_with_deposit_pop.pk},
        ),
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_view_is_accessible_by_admins(
    bob_job_with_deposit_pop: Job,
    admin_client: Client,
) -> None:
    """Ensure admins can access the view.

    Args:
        bob_job_with_deposit_pop (Job): The job created by Bob with the deposit POP.
        admin_client (Client): The Django test client for the admin user.
    """
    response = admin_client.get(
        reverse(
            "jobs:job_complete_onsite_work",
            kwargs={"pk": bob_job_with_deposit_pop.pk},
        ),
    )
    assert response.status_code == status.HTTP_200_OK


def test_page_has_basic_correct_structure(
    marnie_user_client: Client,
    bob_job_with_deposit_pop: Job,
) -> None:
    """Test that the job update page has the correct basic structure.

    Args:
        marnie_user_client (Client): The Django test client for Marnie.
        bob_job_with_deposit_pop (Job): The job created by Bob with the deposit POP.
    """
    url = reverse(
        "jobs:job_complete_onsite_work",
        kwargs={"pk": bob_job_with_deposit_pop.pk},
    )
    check_basic_page_html_structure(
        client=marnie_user_client,
        url=url,
        expected_title="Record Onsite Work Completion",
        expected_template_name="jobs/job_complete_onsite_work.html",
        expected_h1_text="Record Onsite Work Completion",
        expected_func_name="view",
        expected_url_name="job_complete_onsite_work",
        expected_view_class=JobCompleteOnsiteWorkView,
    )


def test_view_has_job_date_field(
    marnie_user_client: Client,
    bob_job_with_deposit_pop: Job,
) -> None:
    """Ensure the view has a field for the job date.

    Args:
        marnie_user_client (Client): The Django test client for Marnie.
        bob_job_with_deposit_pop (Job): The job created by Bob with the deposit POP.
    """
    response = submit_job_completion_form_and_assert_no_errors(
        marnie_user_client,
        bob_job_with_deposit_pop,
    )

    # Check the redirect chain that leads things up to here:
    expected_chain = [("/jobs/?agent=bob", status.HTTP_302_FOUND)]
    assert response.redirect_chain == expected_chain  # type: ignore[attr-defined]

    # Refresh the Maintenance Job from the database, and then check the updated
    # record:
    bob_job_with_deposit_pop.refresh_from_db()
    assert bob_job_with_deposit_pop.job_onsite_work_completion_date == datetime.date(
        2022,
        3,
        4,
    )


def submit_job_completion_form_and_assert_no_errors(
    client: Client,
    job: Job,
) -> TemplateResponse:
    """Submit the job completion form and assert no errors.

    Args:
        client (Client): The Django test client.
        job (Job): The job instance to be updated.

    Returns:
        TemplateResponse: The response object after submitting the form.
    """
    response = check_type(
        client.post(
            reverse(
                "jobs:job_complete_onsite_work",
                kwargs={"pk": job.pk},
            ),
            data={
                "job_onsite_work_completion_date": "2022-03-04",
            },
            follow=True,
        ),
        TemplateResponse,
    )

    # Assert the response status code is 200
    assert response.status_code == status.HTTP_200_OK

    # There shouldn't be any form errors:
    assert_no_form_errors(response)
    return response


# job date field is required
def test_job_date_field_is_required(
    marnie_user_client: Client,
    bob_job_with_deposit_pop: Job,
) -> None:
    """Ensure the job date field is required.

    Args:
        marnie_user_client (Client): The Django test client for Marnie.
        bob_job_with_deposit_pop (Job): The job created by Bob with the deposit POP.
    """
    response = check_type(
        marnie_user_client.post(
            reverse(
                "jobs:job_complete_onsite_work",
                kwargs={"pk": bob_job_with_deposit_pop.pk},
            ),
            data={},
            follow=True,
        ),
        TemplateResponse,
    )

    # Assert the response status code is 200
    assert response.status_code == status.HTTP_200_OK

    # There should be form errors:
    assert response.context["form"].errors == {
        "job_onsite_work_completion_date": ["This field is required."],
    }


def test_updating_job_changes_status_to_completed(
    marnie_user_client: Client,
    bob_job_with_deposit_pop: Job,
) -> None:
    """Ensure updating the job changes the status to complete.

    Args:
        marnie_user_client (Client): The Django test client for Marnie.
        bob_job_with_deposit_pop (Job): The job created by Bob with the deposit POP.
    """
    # Check status before updating
    assert bob_job_with_deposit_pop.status == Job.Status.DEPOSIT_POP_UPLOADED.value
    assert bob_job_with_deposit_pop.complete is False

    # Update the job
    submit_job_completion_form_and_assert_no_errors(
        marnie_user_client,
        bob_job_with_deposit_pop,
    )

    # Refresh the Maintenance Job from the database, and then check the updated
    # record:
    bob_job_with_deposit_pop.refresh_from_db()

    # Check the job status, after the update
    assert (
        bob_job_with_deposit_pop.status == Job.Status.MARNIE_COMPLETED_ONSITE_WORK.value
    )


def test_marnie_cannot_access_view_after_completing_the_job(
    bob_job_with_onsite_work_completed_by_marnie: Job,
    marnie_user_client: Client,
) -> None:
    """Ensure Marnie can't access the update view after completing the job.

    Args:
        bob_job_with_onsite_work_completed_by_marnie (Job): Job that's had the onsite
            work completed by Marnie.
        marnie_user_client (Client): The Django test client for Marnie.
    """
    url = reverse(
        "jobs:job_complete_onsite_work",
        kwargs={"pk": bob_job_with_onsite_work_completed_by_marnie.pk},
    )
    response = marnie_user_client.get(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_admin_cannot_access_view_after_marnie_completes_job(
    bob_job_with_onsite_work_completed_by_marnie: Job,
    admin_client: Client,
) -> None:
    """Ensure admin users can't access the update view after Marnie completes the job.

    Args:
        bob_job_with_onsite_work_completed_by_marnie (Job): Job that's had the onsite
            work completed by Marnie.
        admin_client (Client): The Django test client for the admin user.
    """
    url = reverse(
        "jobs:job_complete_onsite_work",
        kwargs={"pk": bob_job_with_onsite_work_completed_by_marnie.pk},
    )
    response = admin_client.get(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_redirects_to_job_listing_page_after_saving(
    marnie_user_client: Client,
    bob_job_with_deposit_pop: Job,
) -> None:
    """Ensure the view redirects to the job listing page after saving the form.

    Args:
        marnie_user_client (Client): The Django test client for Marnie.
        bob_job_with_deposit_pop (Job): The job created by Bob with the deposit POP.
    """
    response = submit_job_completion_form(
        marnie_user_client,
        bob_job_with_deposit_pop,
        "2022-03-04",
    )

    # Check the redirect chain that leads things up to here:
    expected_chain = [("/jobs/?agent=bob", status.HTTP_302_FOUND)]
    assert response.redirect_chain == expected_chain  # type: ignore[attr-defined]


def submit_job_completion_form(
    client: Client,
    job: Job,
    job_date: str,
) -> TemplateResponse:
    """Submit the job completion form.

    Args:
        client (Client): The Django test client.
        job (Job): The job instance to be updated.
        job_date (str): The date of the job.

    Returns:
        TemplateResponse: The response object after submitting the form.
    """
    response = check_type(
        client.post(
            reverse(
                "jobs:job_complete_onsite_work",
                kwargs={"pk": job.pk},
            ),
            data={
                "job_onsite_work_completion_date": job_date,
            },
            follow=True,
        ),
        TemplateResponse,
    )
    # Assert the response status code is 200
    assert response.status_code == status.HTTP_200_OK
    return response


def test_flash_message_displayed_after_saving(
    marnie_user_client: Client,
    bob_job_with_deposit_pop: Job,
) -> None:
    """Ensure a flash message is displayed after saving the form.

    Args:
        marnie_user_client (Client): The Django test client for Marnie.
        bob_job_with_deposit_pop (Job): The job created by Bob with the deposit POP.
    """
    response = submit_job_completion_form(
        marnie_user_client,
        bob_job_with_deposit_pop,
        "2022-03-04",
    )

    # Check the messages that were displayed:
    messages = list(response.context["messages"])
    assert len(messages) == 1
    assert (
        str(messages[0])
        == "Onsite work has been flagged as completed. An email has been sent to bob."
    )


def test_marnie_clicking_save_sends_an_email_to_agent(
    marnie_user_client: Client,
    bob_job_with_deposit_pop: Job,
    marnie_user: User,
    bob_agent_user: User,
) -> None:
    """Test that Marnie clicking 'Save' sends an email to the agent.

    Args:
        marnie_user_client (Client): The Django test client for Marnie.
        bob_job_with_deposit_pop (Job): The job created by Bob with the deposit POP.
        marnie_user (User): The Marnie user instance.
        bob_agent_user (User): The Bob agent user instance.
    """
    mail.outbox.clear()

    job = bob_job_with_deposit_pop
    response = check_type(
        marnie_user_client.post(
            reverse(
                "jobs:job_complete_onsite_work",
                kwargs={"pk": job.pk},
            ),
            data={
                "job_onsite_work_completion_date": "2022-03-04",
            },
            follow=True,
        ),
        TemplateResponse,
    )

    # Assert the response status code is 200
    assert response.status_code == status.HTTP_200_OK

    # There should be one email in Django's outbox:
    num_mails_sent = len(mail.outbox)
    assert num_mails_sent == 1

    # Grab the mail:
    email = mail.outbox[0]

    # Check various details of the mail here.

    # Check mail metadata:
    assert email.subject == "Marnie completed onsite work on a maintenance job"
    assert bob_agent_user.email in email.to
    assert marnie_user.email in email.cc
    assert constants.DEFAULT_FROM_EMAIL in email.from_email

    # Check mail contents:
    assert (
        "Marnie completed the onsite maintenance work on 2022-03-04. "
        "An email with further documentation will be sent later.\n\n"
    ) in email.body
