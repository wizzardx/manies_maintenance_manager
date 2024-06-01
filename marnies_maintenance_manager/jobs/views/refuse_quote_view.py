"""View for refusing a quote for a Maintenance Job."""

from typing import cast
from uuid import UUID

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.mail import EmailMessage
from django.http import HttpRequest
from django.http import HttpResponse
from django.http import HttpResponseRedirect
from django.http import JsonResponse
from django.shortcuts import get_object_or_404
from rest_framework import status

from marnies_maintenance_manager.jobs.constants import DEFAULT_FROM_EMAIL
from marnies_maintenance_manager.jobs.models import Job
from marnies_maintenance_manager.jobs.utils import get_marnie_email
from marnies_maintenance_manager.jobs.views.job_create_view import generate_email_body
from marnies_maintenance_manager.users.models import User

POST_METHOD_NAME = "POST"


@login_required
def refuse_quote(request: HttpRequest, pk: UUID) -> HttpResponse:
    """Refuse the quote for a specific Maintenance Job.

    Args:
        request (HttpRequest): The HTTP request.
        pk (UUID): The primary key of the Job instance.

    Returns:
        HttpResponse: The HTTP response.
    """
    # Fail for none-POST methods
    if request.method != POST_METHOD_NAME:
        return HttpResponse(
            "Method not allowed",
            status=status.HTTP_405_METHOD_NOT_ALLOWED,
        )

    # Return a permission error if the user is not an agent.
    user = cast(User, request.user)

    job = get_object_or_404(Job, pk=pk)

    # Only the agent who created the quote may refuse it.
    # Besides them, admin users can always refuse quotes.
    if not (user.is_superuser or (user.is_agent and user == job.agent)):
        return HttpResponse(status=status.HTTP_403_FORBIDDEN)

    # Return an error if the job is not in the correct state.
    if job.status not in {
        Job.Status.INSPECTION_COMPLETED.value,
        Job.Status.QUOTE_REFUSED_BY_AGENT.value,
    }:
        data = {"error": "Job is not in the correct state for refusing a quote."}
        return JsonResponse(data=data, status=status.HTTP_412_PRECONDITION_FAILED)

    # Change job state to 'refused by agent'
    job.status = Job.Status.QUOTE_REFUSED_BY_AGENT.value
    job.accepted_or_rejected = Job.AcceptedOrRejected.REJECTED.value
    job.save()

    # Send an email to Marnie telling him that his quote was refused by the agent
    email_subject = f"Quote refused by {job.agent.username}"
    email_body = (
        f"Agent {job.agent.username} has refused the quote for your maintenance "
        "request.\n\n"
        "Details of the original request:\n\n"
        "-----\n\n"
        "Subject: Quote for your maintenance request\n\n"
        "-----\n\n"
        f"Subject: New maintenance request by {job.agent.username}\n\n"
        f"Marnie performed the inspection on {job.date_of_inspection} and has "
        "quoted you.\n\n"
    )

    # Call the email body-generation logic used previously, to help us populate
    # the rest of this email body:
    email_body += generate_email_body(job)

    email_from = DEFAULT_FROM_EMAIL
    email_to = get_marnie_email()
    email_cc = job.agent.email

    # Create the email message:
    email = EmailMessage(
        subject=email_subject,
        body=email_body,
        from_email=email_from,
        to=[email_to],
        cc=[email_cc],
    )

    # Send the mail:
    email.send()

    # Send a success flash message to the user:
    messages.success(request, "Quote refused. An email has been sent to Marnie.")

    # Redirect to the detail view for this job.
    return HttpResponseRedirect(job.get_absolute_url())
