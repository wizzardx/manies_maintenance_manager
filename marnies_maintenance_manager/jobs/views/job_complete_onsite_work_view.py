"""View for completing a Maintenance Job."""

from typing import TYPE_CHECKING

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpResponse
from django.views.generic import UpdateView
from typeguard import check_type

from marnies_maintenance_manager.jobs.forms import JobCompleteOnsiteWorkForm
from marnies_maintenance_manager.jobs.models import Job
from marnies_maintenance_manager.jobs.views.mixins import JobSuccessUrlMixin
from marnies_maintenance_manager.jobs.views.utils import AttachmentType
from marnies_maintenance_manager.jobs.views.utils import prepare_and_send_email
from marnies_maintenance_manager.users.models import User

if TYPE_CHECKING:  # pylint: disable=consider-ternary-expression
    TypedUpdateView = UpdateView[  # pragma: no cover
        Job,
        JobCompleteOnsiteWorkForm,
    ]
else:
    TypedUpdateView = UpdateView


class JobCompleteOnsiteWorkView(
    LoginRequiredMixin,
    UserPassesTestMixin,
    JobSuccessUrlMixin,
    TypedUpdateView,
):
    """Complete a Maintenance Job."""

    model = Job
    form_class = (
        JobCompleteOnsiteWorkForm  # fields = ["job_onsite_work_completion_date"]
    )
    template_name = "jobs/job_complete_onsite_work.html"

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

    def form_valid(self, form: JobCompleteOnsiteWorkForm) -> HttpResponse:
        """Save the form.

        Args:
            form (JobCompleteOnsiteWorkForm): The form instance.

        Returns:
            HttpResponse: The HTTP response.
        """
        job = form.save(commit=False)

        # Update the Job's state to "marnie completed onsite work"
        job.status = Job.Status.MARNIE_COMPLETED_ONSITE_WORK.value
        job.save()

        # Call validations/etc on parent classes
        # noinspection PyUnresolvedReferences
        response = super().form_valid(form)

        # Email the agent.
        email_subject = "Marnie completed onsite work on a maintenance job"

        email_body = (
            "Marnie completed the onsite maintenance work on "
            f"{job.job_onsite_work_completion_date}. "
            "An email with further documentation will be sent later.\n\n"
            "Details of your original request:\n\n"
            "-----\n\n"
            f"Subject: New maintenance request by {job.agent.username}\n\n"
        )

        request = self.request
        prepare_and_send_email(
            email_subject,
            email_body,
            job,
            request,
            AttachmentType.NONE,
        )

        # Send a success flash message to the user:
        agent = job.agent
        msg = (
            "Onsite work has been flagged as completed. "
            f"An email has been sent to {agent.username}."
        )
        messages.success(self.request, msg)

        # Return response back to the caller:
        return response
