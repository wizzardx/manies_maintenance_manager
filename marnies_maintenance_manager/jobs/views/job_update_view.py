"""View for updating a Maintenance Job."""

from typing import cast

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.core.mail import EmailMessage
from django.http import HttpResponse
from django.urls import reverse_lazy
from django.views.generic import UpdateView

from marnies_maintenance_manager.jobs.constants import DEFAULT_FROM_EMAIL
from marnies_maintenance_manager.jobs.forms import JobUpdateForm
from marnies_maintenance_manager.jobs.models import Job
from marnies_maintenance_manager.jobs.utils import get_marnie_email
from marnies_maintenance_manager.jobs.views.job_create_view import generate_email_body
from marnies_maintenance_manager.users.models import User


class JobUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):  # type: ignore[type-arg]
    """Update a Maintenance Job."""

    model = Job
    form_class = JobUpdateForm
    template_name = "jobs/job_update.html"

    def test_func(self) -> bool:
        """Check if the user can access this view.

        Returns:
            bool: True if the user can access this view, False otherwise.
        """
        # Only Marnie and Admin users can reach this view. Marnie can only reach
        # this view if he has not yet completed the inspection. Admin user can
        # always reach this view.
        user = cast(User, self.request.user)
        obj = self.get_object()
        return user.is_superuser or (
            user.is_marnie and obj.status == Job.Status.PENDING_INSPECTION.value
        )

    def form_valid(self, form: JobUpdateForm) -> HttpResponse:
        """Set the status of the job to "inspection_completed" before saving the form.

        Args:
            form (JobUpdateForm): The form instance.

        Returns:
            HttpResponse: The HTTP response.
        """
        instance = cast(Job, form.save(commit=False))
        instance.status = Job.Status.INSPECTION_COMPLETED.value
        instance.save()

        # Call validations/etc on parent classes
        response = super().form_valid(form)

        # In this part, we email the agent, notifying him of the completion of
        # the inspection by Marnie.

        email_subject = "Quote for your maintenance request"
        email_body = (
            f"Marnie performed the inspection on {instance.date_of_inspection} and "
            "has quoted you. The quote is attached to this email.\n\n"
            "Details of your original request:\n\n"
            "-----\n\n"
            f"Subject: New maintenance request by {instance.agent.username}\n\n"
        )

        # Call the email body-generation logic used previously, to help us populate
        # the rest of this email body:
        email_body += generate_email_body(instance)

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
            f"An email has been sent to {agent_username}.",
        )

        # Return response back to the caller:
        return response

    def get_success_url(self) -> str:
        """Return the URL to redirect to after valid form submission.

        Returns:
            str: The URL to redirect to after valid form submission.

        Raises:
            NotImplementedError: If we reach some logic that should not be reached.
        """
        # We want to redirect to the job-listing page.

        # If we're the Marnie user, then we also need to include an agent
        # username to be able to reach that listing correctly.

        # Who is the user behind the request?
        user = cast(User, self.request.user)

        # Special logic if the user is Marnie:
        if user.is_marnie:
            # If the user is Marnie, then we need to include the agent's
            # username in the URL.
            agent_username = self.get_object().agent.username
            return cast(str, reverse_lazy("jobs:job_list") + f"?agent={agent_username}")

        # Check if we're another user, but we still reach this point.
        # It shouldn't happen in the current iteration of the code, but it will
        # happen later during dev. For now, raise a NotImplementedError.
        msg = "This logic should not be reached"  # pragma: no cover
        raise NotImplementedError(msg)  # pragma: no cover
