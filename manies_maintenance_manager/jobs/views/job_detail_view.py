"""Provide a view to create a new Maintenance Job."""

from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import DetailView
from typeguard import check_type

from manies_maintenance_manager.jobs.models import Job
from manies_maintenance_manager.users.models import User


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
        return user.is_manie or user == obj.agent or user.is_superuser

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Add additional context data to the template.

        Args:
            **kwargs: Additional keyword arguments.

        Returns:
            dict: The context data.
        """
        # Only Manie and Admin can see the "Complete Inspection" link, and only when
        # the current Job status allows for it.
        user = check_type(self.request.user, User)
        job = self.get_object()
        complete_inspection_link_present = (
            user.is_manie or user.is_superuser
        ) and job.status == Job.Status.PENDING_INSPECTION.value
        upload_quote_link_present = (
            user.is_manie or user.is_superuser
        ) and job.status in {
            Job.Status.INSPECTION_COMPLETED.value,
            Job.Status.QUOTE_REJECTED_BY_AGENT.value,
        }

        # The "Reject Quote" button may only be seen when the Job is a correct status,
        # and the user is Admin or an Agent. If the user is an Agent, then we also check
        # if it's the same agent who created the Job, even though technically that's
        # not needed (since the user doesn't have permission to see other agents' jobs
        # anyway).
        reject_quote_button_present = (
            job.status == Job.Status.QUOTE_UPLOADED.value
            and ((user.is_agent and user == job.agent) or user.is_superuser)
        )

        # The "Accept Quote" button has almost the same conditions for when it should be
        # displayed, except that it should also be displayed when the quote has been
        # rejected by the Agent.
        accept_quote_button_present = job.status in {
            Job.Status.QUOTE_UPLOADED.value,
            Job.Status.QUOTE_REJECTED_BY_AGENT.value,
        } and ((user.is_agent and user == job.agent) or user.is_superuser)

        # The "Update Quote" link is something that Manie can use - when the Agent
        # rejected his previously submitted quote, to upload a new one.
        update_quote_link_present = (
            user.is_manie or user.is_superuser
        ) and job.status == Job.Status.QUOTE_REJECTED_BY_AGENT.value

        # The "Upload Deposit POP link" is only visible if the quote has been accepted
        # by the agent. It is visible to superusers (admins) and to the agent who
        # originally created the job.
        submit_deposit_proof_of_payment_link_present = (
            job.status == Job.Status.QUOTE_ACCEPTED_BY_AGENT.value
            and (user.is_superuser or (user.is_agent and user == job.agent))
        )

        # There's a "Mark Onsite Work Completed" link present, used by Manie when he's
        # done at the job site. This link only shows up when the agent has uploaded a
        # proof of payment for the deposit.
        complete_onsite_work_link_present = (
            job.status == Job.Status.DEPOSIT_POP_UPLOADED.value
            and user.is_manie
            or user.is_superuser
        )

        submit_job_documentation_link_present = (
            job.status == Job.Status.MANIE_COMPLETED_ONSITE_WORK.value
            and user.is_manie
            or user.is_superuser
        )

        upload_final_payment_pop_link_present = (
            job.status == Job.Status.MANIE_SUBMITTED_DOCUMENTATION.value
            and (user.is_superuser or (user.is_agent and user == job.agent))
        )

        context = super().get_context_data(**kwargs)
        context["complete_inspection_link_present"] = complete_inspection_link_present
        context["upload_quote_link_present"] = upload_quote_link_present
        context["reject_quote_button_present"] = reject_quote_button_present
        context["accept_quote_button_present"] = accept_quote_button_present
        context["update_quote_link_present"] = update_quote_link_present
        context["submit_deposit_proof_of_payment_link_present"] = (
            submit_deposit_proof_of_payment_link_present
        )
        context["complete_onsite_work_link_present"] = complete_onsite_work_link_present
        context["submit_job_documentation_link_present"] = (
            submit_job_documentation_link_present
        )
        context["upload_final_payment_pop_link_present"] = (
            upload_final_payment_pop_link_present
        )
        return context
