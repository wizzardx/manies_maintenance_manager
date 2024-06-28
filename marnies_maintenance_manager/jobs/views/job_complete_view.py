"""View for completing a Maintenance Job."""

from typing import TYPE_CHECKING

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpResponse
from django.views.generic import UpdateView
from typeguard import check_type

from marnies_maintenance_manager.jobs.forms import JobCompleteForm
from marnies_maintenance_manager.jobs.models import Job
from marnies_maintenance_manager.jobs.views.mixins import JobSuccessUrlMixin
from marnies_maintenance_manager.jobs.views.utils import prepare_and_send_email
from marnies_maintenance_manager.users.models import User

if TYPE_CHECKING:  # pylint: disable=consider-ternary-expression
    TypedUpdateView = UpdateView[  # pragma: no cover
        Job,
        JobCompleteForm,
    ]
else:
    TypedUpdateView = UpdateView


class JobCompleteView(
    LoginRequiredMixin,
    UserPassesTestMixin,
    JobSuccessUrlMixin,
    TypedUpdateView,
):
    """Complete a Maintenance Job."""

    model = Job
    form_class = JobCompleteForm  # fields = ["job_date", "invoice", "comments"]
    template_name = "jobs/job_complete.html"

    def test_func(self) -> bool:
        """Check if the user can access this view.

        Returns:
            bool: True if the user can access this view, False otherwise.
        """
        # Only Marnie and Admin users can reach this view, and only if the job has
        # not yet been completed by Marnie.
        user = check_type(self.request.user, User)

        job = self.get_object()
        return (job.status == Job.Status.DEPOSIT_POP_UPLOADED.value) and (
            user.is_superuser or user.is_marnie
        )

    def form_valid(self, form: JobCompleteForm) -> HttpResponse:
        """Save the form.

        Args:
            form (JobCompleteForm): The form instance.

        Returns:
            HttpResponse: The HTTP response.
        """
        # This method is called when valid form data has been POSTed. It's responsible
        # for doing things before and after performing the actual save of the form.
        # (to the database).

        # Update the Job's state to "marnie completed"
        job = form.save(commit=False)
        job.status = Job.Status.MARNIE_COMPLETED.value
        job.complete = True
        job.save()

        # Call validations/etc on parent classes
        # noinspection PyUnresolvedReferences
        response = super().form_valid(form)

        # Email the agent.
        email_subject = "Marnie completed a maintenance job."

        email_body = (
            f"Marnie completed the maintenance work on {job.job_date} and has "
            "invoiced you. The invoice is attached to this email.\n\n"
            "Details of your original request:\n\n"
            "-----\n\n"
            f"Subject: New maintenance request by {job.agent.username}\n\n"
        )

        request = self.request
        prepare_and_send_email(email_subject, email_body, job, request)

        # Send a success flash message to the user:
        agent = job.agent
        msg = f"The job has been completed. An email has been sent to {agent.username}."
        messages.success(self.request, msg)

        # Return response back to the caller:
        return response
