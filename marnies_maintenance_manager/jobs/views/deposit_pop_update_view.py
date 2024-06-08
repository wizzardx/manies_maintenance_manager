"""Provide a view to update the Proof of Payment for a Maintenance Job."""

from typing import TYPE_CHECKING

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.views.generic.edit import UpdateView
from typeguard import check_type

from marnies_maintenance_manager.jobs.models import Job
from marnies_maintenance_manager.users.models import User

if TYPE_CHECKING:  # pragma: no cover
    from marnies_maintenance_manager.jobs.forms import DepositPOPUpdateForm

    UpdateViewTyped = UpdateView[Job, DepositPOPUpdateForm]
else:
    UpdateViewTyped = UpdateView


class DepositPOPUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateViewTyped):
    """Provide a view to update the Proof of Payment for a Maintenance Job."""

    model = Job
    fields = [
        "deposit_proof_of_payment",
    ]
    template_name = "jobs/deposit_pop_update.html"

    def test_func(self) -> bool:
        """Check if the user is allowed to update the deposit POP for the job.

        Returns:
            bool: True if the user can update the deposit POP, False otherwise.
        """
        job = self.get_object()
        user = check_type(self.request.user, User)

        # Only superuser or the agent who created the job can update the deposit POP
        if not (user.is_superuser or (user.is_agent and user == job.agent)):
            return False
        return True
