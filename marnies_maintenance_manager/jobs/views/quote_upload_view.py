"""View for uploading a quote for a Maintenance Job."""

from typing import TYPE_CHECKING

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpResponse
from django.urls import reverse
from django.views.generic import UpdateView
from typeguard import check_type

from marnies_maintenance_manager.jobs.forms import QuoteUploadForm
from marnies_maintenance_manager.jobs.models import Job
from marnies_maintenance_manager.jobs.views.utils import send_quote_update_email
from marnies_maintenance_manager.users.models import User

if TYPE_CHECKING:  # pylint: disable=consider-ternary-expression
    TypedUpdateView = UpdateView[  # pragma: no cover
        Job,
        QuoteUploadForm,
    ]
else:
    TypedUpdateView = UpdateView


class QuoteUploadView(
    LoginRequiredMixin,
    UserPassesTestMixin,
    TypedUpdateView,
):
    """Uploads a quote for a Maintenance Job."""

    model = Job
    form_class = QuoteUploadForm
    template_name = "jobs/quote_upload.html"

    def test_func(self) -> bool:
        """Check if the user can access this view.

        Returns:
            bool: True if the user can access this view, False otherwise.

        """
        # Only Marnie and Admin can access this view, and only when the
        # Job is in the "site was inspected" state.
        user = check_type(self.request.user, User)
        job = self.get_object()

        return job.status == Job.Status.INSPECTION_COMPLETED.value and check_type(
            user.is_marnie or user.is_superuser,
            bool,
        )

    def form_valid(self, form: QuoteUploadForm) -> HttpResponse:
        """Save the form.

        Args:
            form (QuoteUploadForm): The form instance.

        Returns:
            HttpResponse: The HTTP response.
        """
        # This method is called when valid form data has been POSTed. It's responsible
        # for doing things before and after performing the actual save of the form.
        # (to the database).

        # Save the form to db, and then get the job instance to work with further:
        instance = form.save(commit=False)

        # Update state to "quote uploaded":
        instance.status = Job.Status.QUOTE_UPLOADED.value
        instance.save()

        # In this part, we email the agent, notifying him that Marnie has uploaded the
        # quote.
        email_subject = "Marnie uploaded a quote for your maintenance request"
        email_body = (
            "Marnie uploaded a quote for a maintenance job. "
            "The quote is attached to this email.\n\n"
            "Details of your original request:\n\n"
            "-----\n\n"
            f"Subject: New maintenance request by {instance.agent.username}\n\n"
        )

        # Call the email body-generation logic used previously, to help us populate
        # the rest of this email body:
        agent_username = send_quote_update_email(
            self.request,
            email_body,
            email_subject,
            instance,
        )

        # Send a success flash message to the user:
        messages.success(
            self.request,
            "Your quote has been uploaded. "
            f"An email has been sent to {agent_username}.",
        )

        # Do any final logic/etc. on parent classes, and return the result of that
        # (an HTTP response) to our caller:
        # noinspection PyUnresolvedReferences
        return super().form_valid(form)

    def get_success_url(self) -> str:
        """Return the URL to redirect to after processing the form.

        Returns:
            str: The URL to redirect to after processing the form.
        """
        # Send the user to the job-listing page for the agent:
        user = self.object.agent
        return reverse("jobs:job_list") + f"?agent={user.username}"
