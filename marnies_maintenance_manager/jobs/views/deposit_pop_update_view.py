"""Provide a view to update the Proof of Payment for a Maintenance Job."""

from typing import TYPE_CHECKING

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.mail import EmailMessage
from django.http import HttpResponse
from django.views.generic.edit import UpdateView
from typeguard import check_type

from marnies_maintenance_manager.jobs.constants import DEFAULT_FROM_EMAIL
from marnies_maintenance_manager.jobs.forms import DepositPOPUpdateForm
from marnies_maintenance_manager.jobs.models import Job
from marnies_maintenance_manager.jobs.utils import generate_email_body
from marnies_maintenance_manager.jobs.utils import get_marnie_email
from marnies_maintenance_manager.users.models import User

if TYPE_CHECKING:  # pragma: no cover # pylint: disable=consider-ternary-expression
    UpdateViewTyped = UpdateView[Job, DepositPOPUpdateForm]
else:
    UpdateViewTyped = UpdateView


class DepositPOPUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateViewTyped):
    """Provide a view to update the Proof of Payment for a Maintenance Job."""

    model = Job
    form_class = DepositPOPUpdateForm
    template_name = "jobs/deposit_pop_update.html"

    def test_func(self) -> bool:
        """Check if the user is allowed to update the deposit POP for the job.

        Returns:
            bool: True if the user can update the deposit POP, False otherwise.
        """
        job = self.get_object()
        user = check_type(self.request.user, User)

        # Not allowed to access this view if the job is not in the correct state
        if job.status != Job.Status.QUOTE_ACCEPTED_BY_AGENT.value:
            return False

        # Not allowed if the deposit POP has already been uploaded
        if job.deposit_proof_of_payment.name != "":
            return False

        # Only superuser or the agent who created the job can update the deposit POP
        if not (user.is_superuser or (user.is_agent and user == job.agent)):
            return False
        return True

    def form_valid(self, form: DepositPOPUpdateForm) -> HttpResponse:
        """Save the form.

        Args:
            form (DepositPOPUpdateForm): The form instance.

        Returns:
            HttpResponse: The HTTP response.
        """
        # This method is called when valid form data has been POSTed. It's responsible
        # for doing things before and after performing the actual save of the form.
        # (to the database).

        # We don't have anything to do before saving the form, so we just save it:
        instance = form.save(commit=False)
        instance.status = Job.Status.DEPOSIT_POP_UPLOADED.value
        instance.save()

        email_subject = (
            f"Agent {instance.agent.username} added a Deposit POP to the "
            "maintenance request"
        )
        email_body = (
            f"Agent {instance.agent.username} added a Deposit POP to the "
            "maintenance request. The POP is attached to this email.\n\n"
        )

        # Call the email body-generation logic used previously, to help us populate
        # the rest of this email body:
        email_body += "Details of your original request:\n\n"
        email_body += "-----\n\n"
        email_body += (
            f"Subject: New maintenance request by {instance.agent.username}\n\n"
        )
        email_body += generate_email_body(instance, self.request)

        email_from = DEFAULT_FROM_EMAIL
        email_to = get_marnie_email()
        email_cc = instance.agent.email

        email = EmailMessage(
            subject=email_subject,
            body=email_body,
            from_email=email_from,
            to=[email_to],
            cc=[email_cc],
        )

        # Get the quote PDF file from the object instance:
        uploaded_file = instance.deposit_proof_of_payment
        # Attach that to the email:
        email.attach(uploaded_file.name, uploaded_file.read(), "application/pdf")

        # Send the mail:
        email.send()

        # Send a success flash message to the user:
        messages.success(
            self.request,
            "Your Deposit Proof of Payment has been uploaded. "
            "An email has been sent to Marnie.",
        )

        # Do any final logic/etc. on parent classes, and return the result of that
        # (an HTTP response) to our caller:
        # noinspection PyUnresolvedReferences
        return super().form_valid(form)
