"""Provide a view to create a new Maintenance Job."""

from typing import Any

from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.db.models import QuerySet
from django.http import HttpRequest
from django.http import HttpResponseBadRequest
from django.http import HttpResponseBase
from django.views.generic import ListView
from typeguard import check_type

from marnies_maintenance_manager.jobs.models import Job
from marnies_maintenance_manager.users.models import User


# noinspection PyArgumentList
class JobListView(LoginRequiredMixin, UserPassesTestMixin, ListView):  # type: ignore[type-arg] # pylint: disable=too-many-ancestors
    """Display a list of all Maintenance Jobs.

    This view extends Django's ListView class to display a list of all maintenance jobs
    in the system. It uses the 'jobs/job_list.html' template.
    """

    model = Job
    template_name = "jobs/job_list.html"

    def test_func(self) -> bool:
        """Check if the user is an agent, or Marnie, or a superuser.

        Returns:
            bool: True if the user has the required permissions, False otherwise.
        """
        user = check_type(self.request.user, User)
        return user.is_agent or user.is_superuser or user.is_marnie

    def dispatch(
        self,
        request: HttpRequest,
        *args: int,
        **kwargs: int,
    ) -> HttpResponseBase:
        """Handle exceptions in dispatch and provide appropriate responses.

        Enhances the default dispatch method by catching ValueError exceptions
        and returning a bad request response with the error message.

        Args:
            request (HttpRequest): The HTTP request.
            *args (int): Additional positional arguments.
            **kwargs (int): Additional keyword arguments.

        Returns:
            HttpResponseBase: The HTTP response.
        """
        try:
            return super().dispatch(request, *args, **kwargs)
        except ValueError as e:
            return HttpResponseBadRequest(str(e))

    def get_queryset(self) -> QuerySet[Job]:
        """Filter Job instances by user's role and optional query parameters.

        Returns:
            QuerySet[Job]: The queryset of Job instances.

        Raises:
            ValueError: If conditions are not met or parameters are missing.
        """
        user = check_type(self.request.user, User)

        if user.is_marnie:
            agent_username = self.request.GET.get("agent")
            if not agent_username:  # pylint: disable=consider-using-assignment-expr
                msg = "Agent username parameter is missing"
                raise ValueError(msg)
            try:
                agent = User.objects.get(username=agent_username)
            except User.DoesNotExist as err:
                msg = "Agent username not found"
                raise ValueError(msg) from err
            return Job.objects.filter(agent=agent)

        if user.is_agent:
            # For agents, we return all jobs that they initially created
            return Job.objects.filter(agent=user)

        if user.is_superuser:  # pragma: no branch
            if not (agent_username := self.request.GET.get("agent")):
                # Agent's username parameter not provided, so for superuser, return all
                # jobs.
                return Job.objects.all()
            try:
                agent = User.objects.get(username=agent_username)
            except User.DoesNotExist as err:
                msg = "Agent username not found"
                raise ValueError(msg) from err
            return Job.objects.filter(agent=agent)

        # There are no known use cases past this point (they should have been caught
        # in various other logic branches before logic reaches this point), but
        # just in case we do somehow reach this point, raise an error:
        msg = "Unknown user type"  # pragma: no cover
        raise ValueError(msg)  # pragma: no cover

    def get_context_data(self, **kwargs: Any) -> dict[str, Any]:
        """Add additional context data to the template.

        Args:
            **kwargs (Any): Additional keyword arguments.

        Returns:
            dict[str, Any]: The context data.
        """
        context = super().get_context_data(**kwargs)

        # Present a different title to the template if "agent" is in the
        # query parameters.
        if agent_username := self.request.GET.get("agent"):
            context["title"] = f"Maintenance Jobs for {agent_username}"
            # Also put the agent username in the context, so the template can display
            # the agent's name.
            context["agent_username"] = agent_username
        else:
            context["title"] = "Maintenance Jobs"
        return context
