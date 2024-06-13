"""Provide a view to create a new Maintenance Job."""

from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import DetailView
from typeguard import check_type

from marnies_maintenance_manager.jobs.models import Job
from marnies_maintenance_manager.users.models import User


class JobDetailView(LoginRequiredMixin, UserPassesTestMixin, DetailView):  # type: ignore[type-arg]
    """Display details of a specific Maintenance Job."""

    model = Job

    def test_func(self) -> bool:
        """Check the user can access this view.

        Returns:
            bool: True if the user can access this view, False otherwise.
        """
        user = check_type(self.request.user, User)
        obj = self.get_object()
        return user.is_marnie or user == obj.agent or user.is_superuser

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Add additional context data to the template.

        Args:
            **kwargs: Additional keyword arguments.

        Returns:
            dict: The context data.
        """
        # Only Marnie and Admin can see the Update link, and only when the current Job
        # status allows for it.
        user = check_type(self.request.user, User)
        job = self.get_object()
        update_link_present = (
            user.is_marnie or user.is_superuser
        ) and job.status == Job.Status.PENDING_INSPECTION.value

        # The "Reject Quote" button may only be seen when the Job is a correct status,
        # and the user is Admin or an Agent. If the user is an Agent, then we also check
        # if it's the same agent who created the Job, even though technically that's
        # not needed (since the user doesn't have permission to see other agents' jobs
        # anyway).
        reject_quote_button_present = (
            job.status == Job.Status.INSPECTION_COMPLETED.value
            and ((user.is_agent and user == job.agent) or user.is_superuser)
        )

        # The "Accept Quote" button has almost the same conditions for when it should be
        # displayed, except that it should also be displayed when the quote has been
        # rejected by the Agent.
        accept_quote_button_present = job.status in {
            Job.Status.INSPECTION_COMPLETED.value,
            Job.Status.QUOTE_REJECTED_BY_AGENT.value,
        } and ((user.is_agent and user == job.agent) or user.is_superuser)

        # The "Update Quote" link is something that Marnie can use - when the Agent
        # rejected his previously submitted quote, to upload a new one.
        update_quote_link_present = (
            user.is_marnie or user.is_superuser
        ) and job.status == Job.Status.QUOTE_REJECTED_BY_AGENT.value

        # The "Submit Deposit POP link" is only visible if the quote has been accepted
        # by the agent. It is visible to superusers (admins) and to the agent who
        # originally created the job.
        submit_deposit_proof_of_payment_link_present = (
            job.status == Job.Status.QUOTE_ACCEPTED_BY_AGENT.value
            and (user.is_superuser or (user.is_agent and user == job.agent))
        )

        # There's a second "Update" link present, used by Marnie when completing
        # the job. This link only shows up when the agent has uploaded a proof of
        # payment for the deposit.
        update_link_2_present = (
            job.status == Job.Status.DEPOSIT_POP_UPLOADED.value
            and user.is_marnie
            or user.is_superuser
        )

        context = super().get_context_data(**kwargs)
        context["update_link_present"] = update_link_present
        context["reject_quote_button_present"] = reject_quote_button_present
        context["accept_quote_button_present"] = accept_quote_button_present
        context["update_quote_link_present"] = update_quote_link_present
        context["submit_deposit_proof_of_payment_link_present"] = (
            submit_deposit_proof_of_payment_link_present
        )
        context["update_link_2_present"] = update_link_2_present
        return context
