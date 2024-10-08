"""View for updating a quote for a Maintenance Job."""

from typing import TYPE_CHECKING

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpResponse
from django.views.generic import UpdateView
from typeguard import check_type

from manies_maintenance_manager.jobs.forms import QuoteUpdateForm
from manies_maintenance_manager.jobs.models import Job
from manies_maintenance_manager.jobs.views.utils import send_quote_update_email
from manies_maintenance_manager.users.models import User

if TYPE_CHECKING:  # pylint: disable=consider-ternary-expression
    TypedUpdateView = UpdateView[  # pragma: no cover
        Job,
        QuoteUpdateForm,
    ]
else:
    TypedUpdateView = UpdateView


class QuoteUpdateView(
    LoginRequiredMixin,
    UserPassesTestMixin,
    TypedUpdateView,
):
    """Update a quote for a Maintenance Job."""

    model = Job
    form_class = QuoteUpdateForm
    template_name = "jobs/quote_update.html"

    def test_func(self) -> bool:
        """Check if the user can access this view.

        Returns:
            bool: True if the user can access this view, False otherwise.

        """
        # Only Manie and Admin can access this view, and only when the
        # Job is in the "quote was rejected" state.
        user = check_type(self.request.user, User)
        job = self.get_object()
        return job.status == Job.Status.QUOTE_REJECTED_BY_AGENT.value and check_type(
            user.is_manie or user.is_superuser,
            bool,
        )

    def form_valid(self, form: QuoteUpdateForm) -> HttpResponse:
        """Save the form.

        Args:
            form (QuoteUpdateForm): The form instance.

        Returns:
            HttpResponse: The HTTP response.
        """
        # This method is called when valid form data has been POSTed. It's responsible
        # for doing things before and after performing the actual save of the form.
        # (to the database).

        # We don't have anything to do before saving the form, so we just save it:
        instance = form.save()

        # In this part, we email the agent, notifying him that Manie has updated the
        # quote.
        email_subject = "Manie uploaded an updated quote for your job"
        email_body = (
            "Manie uploaded a new quote for a maintenance job. "
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
            "Your updated quote has been uploaded. "
            f"An email has been sent to {agent_username}.",
        )

        # Do any final logic/etc. on parent classes, and return the result of that
        # (an HTTP response) to our caller:
        # noinspection PyUnresolvedReferences
        return super().form_valid(form)
