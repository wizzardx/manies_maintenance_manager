"""Utility functions for the "jobs" app views."""

# ruff: noqa: PLR0913
# pylint: disable=too-many-arguments

import logging
import mimetypes
from enum import Enum

import environ
from django.core.mail import EmailMessage
from django.db.models.fields.files import FieldFile
from django.http import HttpRequest
from typeguard import check_type

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
    INVOICE_AND_PHOTOS = "invoice_and_photos"
    NONE = "none"


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
            attachments = [job.quote]
        case AttachmentType.NONE:
            attachments = []
        case AttachmentType.INVOICE_AND_PHOTOS:
            attachments = [job.invoice] + [
                photo.photo for photo in job.job_completion_photos.all()
            ]
        case _:
            msg = f"Invalid value for 'what_to_attach': {what_to_attach!r}"
            raise ValueError(msg)

    # Create the email message:
    send_job_email_with_attachments(
        email_subject,
        email_body,
        email_from,
        email_to,
        email_cc,
        attachments,
    )


def get_content_type(attachment: FieldFile) -> str:
    """Get the content type of the attachment.

    Args:
        attachment (FieldFile): The attachment.

    Returns:
        str: The content type of the attachment.
    """
    file_path = attachment.path
    mime_type, _ = mimetypes.guess_type(file_path)
    return check_type(mime_type, str)


def send_job_email_with_attachments(
    email_subject: str,
    email_body: str,
    email_from: str,
    email_to: str,
    email_cc: str,
    attachments: list[FieldFile],
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
        attachments (list[FieldFile]): The files to be attached to the email.
        skip_email_send (bool): Flag to indicate if the email should not be sent.
    """
    email = EmailMessage(
        subject=email_subject,
        body=email_body,
        from_email=email_from,
        to=[email_to],
        cc=[email_cc],
    )

    for attachment in attachments:
        content_type = get_content_type(attachment)
        with safe_read(attachment):
            email.attach(attachment.name, attachment.read(), content_type)

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
