"""Provide a view to create a new Maintenance Job."""

from typing import Any
from typing import cast

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic import DetailView

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
        user = cast(User, self.request.user)
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
        user = cast(User, self.request.user)
        obj = self.get_object()
        update_link_present = (
            user.is_marnie or user.is_superuser
        ) and obj.status == Job.Status.PENDING_INSPECTION.value

        # The "Refuse Quote" button may only be seen when the Job is a correct status,
        # and the user is Admin or an Agent. If the user is an Agent, then we also check
        # # if it's the same agent who created the Job, even though technically that's
        # not needed (since the user doesn't have permission to see other agents' jobs
        # anyway).
        refuse_quote_button_present = obj.status in {
            Job.Status.INSPECTION_COMPLETED.value,
            Job.Status.QUOTE_REFUSED_BY_AGENT.value,
        } and ((user.is_agent and user == obj.agent) or user.is_superuser)

        # The "Accept Quote" button has the same conditions for when it should be
        # displayed.
        accept_quote_button_present = refuse_quote_button_present

        context = super().get_context_data(**kwargs)
        context["update_link_present"] = update_link_present
        context["refuse_quote_button_present"] = refuse_quote_button_present
        context["accept_quote_button_present"] = accept_quote_button_present
        return context
