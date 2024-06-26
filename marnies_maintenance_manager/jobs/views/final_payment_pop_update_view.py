"""Django view for updating final payment proof of payment in maintenance system.

This module defines a Django view for updating the final payment proof of payment in a
maintenance management system.

The module includes:
- Necessary imports from Django and other dependencies
- A custom view class `FinalPaymentPOPUpdateView` that inherits from
  LoginRequiredMixin, UserPassesTestMixin, andUpdateView

Key components:
- FinalPaymentPOPUpdateView: Handles the update of final payment proof of payment for a
  job
    - Restricts access to authorized users (superusers or assigned agents)
    - Validates the job status before allowing updates
    - Processes the form submission, updates the job status, and sends notification
      emails

The view ensures that:
1. Only authenticated users can access the view
2. The job is in the correct state for final payment POP upload
3. The final payment POP hasn't been uploaded before
4. The user is either a superuser or the assigned agent for the job

Upon successful form submission, the view:
1. Updates the job status
2. Generates and sends a notification email with the uploaded POP
3. Displays a success message to the user

Dependencies:
- Django
- typeguard
- Custom utility functions and models from the marnies_maintenance_manager project

Note: This module uses type checking and includes conditional import logic for type
hinting.
"""

from typing import TYPE_CHECKING

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpResponse
from django.views.generic.edit import UpdateView
from typeguard import check_type

from marnies_maintenance_manager.jobs.constants import DEFAULT_FROM_EMAIL
from marnies_maintenance_manager.jobs.forms import FinalPaymentPOPUpdateForm
from marnies_maintenance_manager.jobs.models import Job
from marnies_maintenance_manager.jobs.utils import generate_email_body
from marnies_maintenance_manager.jobs.utils import get_marnie_email
from marnies_maintenance_manager.jobs.views.utils import send_job_email_with_attachment
from marnies_maintenance_manager.users.models import User

if TYPE_CHECKING:  # pragma: no cover # pylint: disable=consider-ternary-expression
    UpdateViewTyped = UpdateView[Job, FinalPaymentPOPUpdateForm]
else:
    UpdateViewTyped = UpdateView


class FinalPaymentPOPUpdateView(
    LoginRequiredMixin,
    UserPassesTestMixin,
    UpdateViewTyped,
):
    """View for updating the final payment proof of payment."""

    model = Job
    form_class = FinalPaymentPOPUpdateForm
    template_name = "jobs/final_payment_pop_update.html"

    def test_func(self) -> bool:
        """Check if the user is allowed to access this view.

        Returns:
            bool: True if the user is allowed to access the view, otherwise False.
        """
        job = self.get_object()
        user = check_type(self.request.user, User)

        # Not allowed to access this view if the job is not in the correct state
        if job.status != Job.Status.MARNIE_COMPLETED.value:
            return False

        # Not allowed to access this view if the final payment POP has already been
        # uploaded
        if job.final_payment_pop.name != "":
            return False

        return user.is_superuser or (user.is_agent and user == job.agent)

    def form_valid(self, form: FinalPaymentPOPUpdateForm) -> HttpResponse:
        """Handle form submission for updating the final payment proof of payment.

        Args:
            form (FinalPaymentPOPUpdateForm): The form instance with the submitted data.

        Returns:
            HttpResponse: The HTTP response after processing the form submission.
        """
        # This method is called when valid form data has been POSTed. It's responsible
        # for doing things before and after performing the actual save of the form.
        # (to the database).

        job = form.save(commit=False)
        job.status = Job.Status.FINAL_PAYMENT_POP_UPLOADED.value
        job.save()

        email_subject = (
            f"Agent {job.agent.username} added a Final Payment POP to the "
            "maintenance request"
        )
        email_body = (
            f"Agent {job.agent.username} added a Final Payment POP to the "
            "maintenance request. The POP is attached to this email.\n\n"
        )

        # Call the email body-generation logic used previously, to help us populate
        # the rest of this email body:
        email_body += "Details of your original request:\n\n"
        email_body += "-----\n\n"
        email_body += f"Subject: New maintenance request by {job.agent.username}\n\n"
        email_body += generate_email_body(job, self.request)

        email_from = DEFAULT_FROM_EMAIL
        email_to = get_marnie_email()
        email_cc = job.agent.email
        uploaded_file = job.final_payment_pop

        send_job_email_with_attachment(
            email_subject,
            email_body,
            email_from,
            email_to,
            email_cc,
            uploaded_file,
        )

        # Send a success flash message to the user:
        messages.success(
            self.request,
            "Your Final Payment Proof of Payment has been uploaded. "
            "An email has been sent to Marnie.",
        )

        # Do any final logic/etc. on parent classes, and return the result of that
        # (an HTTP response) to our caller:
        # noinspection PyUnresolvedReferences
        return super().form_valid(form)
