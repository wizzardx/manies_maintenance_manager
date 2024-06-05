"""View for updating a quote for a Maintenance Job."""

from typing import TYPE_CHECKING

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.mail import EmailMessage
from django.views.generic import UpdateView
from typeguard import check_type

from marnies_maintenance_manager.jobs.constants import DEFAULT_FROM_EMAIL
from marnies_maintenance_manager.jobs.forms import QuoteUpdateForm
from marnies_maintenance_manager.jobs.models import Job
from marnies_maintenance_manager.jobs.utils import get_marnie_email
from marnies_maintenance_manager.jobs.views.job_create_view import generate_email_body
from marnies_maintenance_manager.users.models import User

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

    model: type[Job] = Job
    form_class: type[QuoteUpdateForm] = QuoteUpdateForm
    template_name: str = "jobs/update_quote.html"

    def test_func(self) -> bool:
        """Check if the user can access this view.

        Returns:
            bool: True if the user can access this view, False otherwise.

        """
        # Only Marnie and Admin can access this view:
        user = check_type(self.request.user, User)
        return check_type(user.is_marnie or user.is_superuser, bool)

    def form_valid(self, form: QuoteUpdateForm) -> None:
        """Save the form.

        Args:
            form (QuoteUpdateForm): The form instance.

        """
        # This method is called when valid form data has been POSTed. It's responsible
        # for doing things before and after performing the actual save of the form.
        # (to the database).

        # We don't have anything to do before saving the form, so we just save it:
        instance = form.save()

        # In this part, we email the agent, notifying him that Marnie has updated the
        # quote.
        email_subject = "Marnie uploaded an updated quote for your job"
        email_body = (
            "Marnie uploaded a new quote for a maintenance job. "
            "The quote is attached to this email.\n\n"
            "Details of your original request:\n\n"
            "-----\n\n"
            f"Subject: New maintenance request by {instance.agent.username}\n\n"
        )

        # Call the email body-generation logic used previously, to help us populate
        # the rest of this email body:
        email_body += generate_email_body(instance, self.request)

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
        agent_username = instance.agent.username

        # Send a success flash message to the user:
        messages.success(
            self.request,
            "Your updated quote has been uploaded. "
            f"An email has been sent to {agent_username}.",
        )

        # Do any final logic/etc. on parent classes, and return the result of that
        # (an HTTP response) to our caller:
        return super().form_valid(form)
