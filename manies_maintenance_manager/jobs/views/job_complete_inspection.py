"""View for updating a Maintenance Job."""

import logging
from typing import TYPE_CHECKING

import environ
from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.mail import EmailMessage
from django.http import HttpResponse
from django.views.generic import UpdateView
from typeguard import check_type

from manies_maintenance_manager.jobs.constants import DEFAULT_FROM_EMAIL
from manies_maintenance_manager.jobs.forms import JobCompleteInspectionForm
from manies_maintenance_manager.jobs.models import Job
from manies_maintenance_manager.jobs.utils import generate_email_body
from manies_maintenance_manager.jobs.utils import get_manie_email
from manies_maintenance_manager.jobs.views.mixins import JobSuccessUrlMixin
from manies_maintenance_manager.users.models import User

env = environ.Env()
SKIP_EMAIL_SEND = env.bool("SKIP_EMAIL_SEND", default=False)


if TYPE_CHECKING:  # pylint: disable=consider-ternary-expression
    TypedUpdateView = UpdateView[  # pragma: no cover
        Job,
        JobCompleteInspectionForm,
    ]
else:
    TypedUpdateView = UpdateView

logger = logging.getLogger(__name__)


class JobCompleteInspectionView(
    LoginRequiredMixin,
    UserPassesTestMixin,
    JobSuccessUrlMixin,
    TypedUpdateView,
):
    """Update a Maintenance Job."""

    model = Job
    form_class = JobCompleteInspectionForm
    template_name = "jobs/job_complete_inspection.html"

    def test_func(self) -> bool:
        """Check if the user can access this view.

        Returns:
            bool: True if the user can access this view, False otherwise.
        """
        # Only Manie and Admin users can reach this view. The view can only be reached
        # if Manie has not yet completed the inspection.
        user = check_type(self.request.user, User)
        job = self.get_object()
        return (job.status == Job.Status.PENDING_INSPECTION.value) and (
            user.is_superuser or user.is_manie
        )

    # noinspection PyUnresolvedReferences
    def form_valid(self, form: JobCompleteInspectionForm) -> HttpResponse:
        """Set the status of the job to "inspection_completed" before saving the form.

        Args:
            form (JobCompleteInspectionForm): The form instance.

        Returns:
            HttpResponse: The HTTP response.
        """
        job = form.save(commit=False)
        job.status = Job.Status.INSPECTION_COMPLETED.value
        job.save()

        # Call validations/etc on parent classes
        # noinspection PyUnresolvedReferences
        response = super().form_valid(form)

        # In this part, we email the agent, notifying him of the completion of
        # the inspection by Manie.

        email_subject = "Manie completed an inspection for your maintenance request"
        email_body = (
            f"Manie performed the inspection on {job.date_of_inspection}. An email "
            "with the quote will be sent later.\n\n"
            "Details of your original request:\n\n"
            "-----\n\n"
            f"Subject: New maintenance request by {job.agent.username}\n\n"
        )

        # Email the agent, and cc Manie:
        request = self.request
        email_body += generate_email_body(job, request)
        email_from = DEFAULT_FROM_EMAIL
        email_to = job.agent.email
        email_cc = get_manie_email()

        email = EmailMessage(
            subject=email_subject,
            body=email_body,
            from_email=email_from,
            to=[email_to],
            cc=[email_cc],
        )

        if not SKIP_EMAIL_SEND:
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

        # Send a success flash message to the user:
        agent_username = job.agent.username
        messages.success(
            self.request,
            f"An email has been sent to {agent_username}.",
        )

        # Return response back to the caller:
        return response
