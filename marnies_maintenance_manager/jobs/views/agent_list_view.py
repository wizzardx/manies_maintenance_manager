"""View for the Agent list page."""

from django.contrib.auth.decorators import login_required
from django.http import HttpRequest
from django.http import HttpResponse
from django.shortcuts import render
from rest_framework import status
from typeguard import check_type

from marnies_maintenance_manager.users.models import User


@login_required
def agent_list(request: HttpRequest) -> HttpResponse:
    """Render the list of Agent users.

    Or more precisely, we want to - for the benefit of Marnie - map between each
    Agent, and the jobs created by them, in something spiritually similar to a
    'per-agent spreadsheet'

    Args:
        request (HttpRequest): The HTTP request.

    Returns:
        HttpResponse: The HTTP response.
    """
    # Only Marnie user and the Admin may access this view. Return a 403 Forbidden
    # response if some other user is trying to access this view.
    user = check_type(request.user, User)
    if not (user.is_superuser or user.is_marnie):
        return HttpResponse(status=status.HTTP_403_FORBIDDEN)
    context = {"agent_list": User.objects.filter(is_agent=True).order_by("username")}
    return render(request, "jobs/agent_list.html", context=context)
