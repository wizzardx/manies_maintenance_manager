"""View for updating a Maintenance Job."""

from typing import TYPE_CHECKING

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpResponse
from django.views.generic import UpdateView
from typeguard import check_type

from marnies_maintenance_manager.jobs.forms import JobUpdateForm
from marnies_maintenance_manager.jobs.models import Job
from marnies_maintenance_manager.jobs.views.mixins import JobSuccessUrlMixin
from marnies_maintenance_manager.jobs.views.utils import send_quote_update_email
from marnies_maintenance_manager.users.models import User

if TYPE_CHECKING:  # pylint: disable=consider-ternary-expression
    TypedUpdateView = UpdateView[  # pragma: no cover
        Job,
        JobUpdateForm,
    ]
else:
    TypedUpdateView = UpdateView


class JobUpdateView(
    LoginRequiredMixin,
    UserPassesTestMixin,
    JobSuccessUrlMixin,
    TypedUpdateView,
):
    """Update a Maintenance Job."""

    model = Job
    form_class = JobUpdateForm
    template_name = "jobs/job_update.html"

    def test_func(self) -> bool:
        """Check if the user can access this view.

        Returns:
            bool: True if the user can access this view, False otherwise.
        """
        # Only Marnie and Admin users can reach this view. The view can only be reached
        # if Marnie has not yet completed the inspection.
        user = check_type(self.request.user, User)
        job = self.get_object()
        return (job.status == Job.Status.PENDING_INSPECTION.value) and (
            user.is_superuser or user.is_marnie
        )

    # noinspection PyUnresolvedReferences
    def form_valid(self, form: JobUpdateForm) -> HttpResponse:
        """Set the status of the job to "inspection_completed" before saving the form.

        Args:
            form (JobUpdateForm): The form instance.

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
        # the inspection by Marnie.

        email_subject = "Quote for your maintenance request"
        email_body = (
            f"Marnie performed the inspection on {job.date_of_inspection} and "
            "has quoted you. The quote is attached to this email.\n\n"
            "Details of your original request:\n\n"
            "-----\n\n"
            f"Subject: New maintenance request by {job.agent.username}\n\n"
        )

        # Call the email body-generation logic used previously, to help us populate
        # the rest of this email body:
        agent_username = send_quote_update_email(
            self.request,
            email_body,
            email_subject,
            job,
        )

        # Send a success flash message to the user:
        messages.success(
            self.request,
            f"An email has been sent to {agent_username}.",
        )

        # Return response back to the caller:
        return response
