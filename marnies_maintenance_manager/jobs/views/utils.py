"""Utility functions for the "jobs" app views."""

from django.core.mail import EmailMessage
from django.http import HttpRequest

from marnies_maintenance_manager.jobs.constants import DEFAULT_FROM_EMAIL
from marnies_maintenance_manager.jobs.models import Job
from marnies_maintenance_manager.jobs.utils import get_marnie_email
from marnies_maintenance_manager.jobs.views.job_create_view import generate_email_body


def send_quote_update_email(
    request: HttpRequest,
    email_body: str,
    email_subject: str,
    instance: Job,
) -> str:
    """Email the agent when Marnie updates the quote for a Maintenance Job.

    Args:
        request (HttpRequest): The request object.
        email_body (str): The email body.
        email_subject (str): The email subject.
        instance (Job): The Job instance.

    Returns:
        str: The username of the Agent who originally created the Maintenance Job.
    """
    email_body += generate_email_body(instance, request)
    email_from = DEFAULT_FROM_EMAIL
    email_to = instance.agent.email
    email_cc = get_marnie_email()
    # Create the email message:
    email = EmailMessage(
        subject=email_subject,
        body=email_body,
        from_email=email_from,
        to=[email_to],
        cc=[email_cc],
    )
    # Get the quote PDF file from the object instance:
    uploaded_file = instance.quote
    # Attach that to the email:
    email.attach(uploaded_file.name, uploaded_file.read(), "application/pdf")
    # Send the mail:
    email.send()
    # Get username associated with the Agent who originally created the Maintenance
    # Job:
    return instance.agent.username
