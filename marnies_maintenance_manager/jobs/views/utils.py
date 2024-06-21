"""Utility functions for the "jobs" app views."""

# ruff: noqa: PLR0913
# pylint: disable=too-many-arguments

from django.core.mail import EmailMessage
from django.db.models.fields.files import FieldFile
from django.http import HttpRequest

from marnies_maintenance_manager.jobs.constants import DEFAULT_FROM_EMAIL
from marnies_maintenance_manager.jobs.models import Job
from marnies_maintenance_manager.jobs.utils import generate_email_body
from marnies_maintenance_manager.jobs.utils import get_marnie_email
from marnies_maintenance_manager.jobs.utils import safe_read


def send_quote_update_email(
    request: HttpRequest,
    email_body: str,
    email_subject: str,
    job: Job,
) -> str:
    """Email the agent when Marnie updates the quote for a Maintenance Job.

    Args:
        request (HttpRequest): The request object.
        email_body (str): The email body.
        email_subject (str): The email subject.
        job (Job): The Job instance.

    Returns:
        str: The username of the Agent who originally created the Maintenance Job.
    """
    prepare_and_send_email(email_subject, email_body, job, request)

    # Get username associated with the Agent who originally created the Maintenance
    # Job:
    return job.agent.username


def prepare_and_send_email(
    email_subject: str,
    email_body: str,
    job: Job,
    request: HttpRequest,
) -> None:
    """Prepare and send an email with the quote update for a Maintenance Job.

    Args:
        email_subject (str): The email subject.
        email_body (str): The email body.
        job (Job): The Job instance.
        request (HttpRequest): The request object.
    """
    email_body += generate_email_body(job, request)
    email_from = DEFAULT_FROM_EMAIL
    email_to = job.agent.email
    email_cc = get_marnie_email()
    uploaded_file = job.quote

    # Create the email message:
    send_job_email_with_attachment(
        email_subject,
        email_body,
        email_from,
        email_to,
        email_cc,
        uploaded_file,
    )


def send_job_email_with_attachment(
    email_subject: str,
    email_body: str,
    email_from: str,
    email_to: str,
    email_cc: str,
    uploaded_file: FieldFile,
) -> None:
    """Prepare and send an email with an attachment for a Maintenance Job.

    Args:
        email_subject (str): The email subject.
        email_body (str): The email body.
        email_from (str): The email from address.
        email_to (str): The email to address.
        email_cc (str): The email cc address.
        uploaded_file: The file to be attached to the email.
    """
    email = EmailMessage(
        subject=email_subject,
        body=email_body,
        from_email=email_from,
        to=[email_to],
        cc=[email_cc],
    )

    with safe_read(uploaded_file):
        email.attach(uploaded_file.name, uploaded_file.read(), "application/pdf")

    email.send()
