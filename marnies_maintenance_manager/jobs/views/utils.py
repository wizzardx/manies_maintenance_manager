"""Utility functions for the "jobs" app views."""

# ruff: noqa: PLR0913
# pylint: disable=too-many-arguments

import logging
from enum import Enum

import environ
from django.core.mail import EmailMessage
from django.db.models.fields.files import FieldFile
from django.http import HttpRequest

from marnies_maintenance_manager.jobs.constants import DEFAULT_FROM_EMAIL
from marnies_maintenance_manager.jobs.models import Job
from marnies_maintenance_manager.jobs.utils import generate_email_body
from marnies_maintenance_manager.jobs.utils import get_marnie_email
from marnies_maintenance_manager.jobs.utils import safe_read

env = environ.Env()
SKIP_EMAIL_SEND = env.bool("SKIP_EMAIL_SEND", default=False)

logger = logging.getLogger(__name__)


class AttachmentType(Enum):
    """Enum for possible attachment types to pass to prepare_and_send_email()."""

    QUOTE = "quote"
    INVOICE = "invoice"


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
    prepare_and_send_email(
        email_subject,
        email_body,
        job,
        request,
        AttachmentType.QUOTE,
    )

    # Get username associated with the Agent who originally created the Maintenance
    # Job:
    return job.agent.username


def prepare_and_send_email(
    email_subject: str,
    email_body: str,
    job: Job,
    request: HttpRequest,
    what_to_attach: AttachmentType,
) -> None:
    """Prepare and send an email with the quote update for a Maintenance Job.

    Args:
        email_subject (str): The email subject.
        email_body (str): The email body.
        job (Job): The Job instance.
        request (HttpRequest): The request object.
        what_to_attach (AttachmentType): The type of attachment to include in the email.

    Raises:
        ValueError: If an invalid value is passed for 'what_to_attach'.
    """
    email_body += generate_email_body(job, request)
    email_from = DEFAULT_FROM_EMAIL
    email_to = job.agent.email
    email_cc = get_marnie_email()
    match what_to_attach:
        case AttachmentType.QUOTE:
            uploaded_file = job.quote
        case AttachmentType.INVOICE:
            uploaded_file = job.invoice
        case _:
            msg = f"Invalid value for 'what_to_attach': {what_to_attach!r}"
            raise ValueError(msg)

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
    *,
    skip_email_send: bool = SKIP_EMAIL_SEND,
) -> None:
    """Prepare and send an email with an attachment for a Maintenance Job.

    Args:
        email_subject (str): The email subject.
        email_body (str): The email body.
        email_from (str): The email from address.
        email_to (str): The email to address.
        email_cc (str): The email cc address.
        uploaded_file (FieldFile): The file to be attached to the email.
        skip_email_send (bool): Flag to indicate if the email should not be sent.
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

    if not skip_email_send:
        email.send()
    else:
        logger.info(
            "Skipping email send. Would have sent the following email:\n\n"
            "Subject: %s\n\n"
            "Body: %s\n\n"
            "From: %s\n\n"
            "To: %s\n\n"
            "CC: %s\n\n",
            email_subject,
            email_body,
            email_from,
            email_to,
            email_cc,
        )
