"""URL routing definitions for the jobs module in the Marnie's Maintenance Manager.

This module defines URL patterns for the 'jobs' application, mapping URLs to their
respective view functions for listing and creating maintenance jobs. It uses
Django's path function to establish routes.

The urlpatterns list includes:
- A route for the job list page, linked to the `job_list` view.
- A route for the "create job" page, linked to the `job_create` view.

This configuration maintains a clean separation of concerns between URLs and views,
adhering to Django's principles for URL dispatching.

Usage examples:
Access the job list with `/jobs/` and the creation page with `/jobs/create/`.
"""

from django.urls import path

from .views import JobCreateView
from .views import JobDetailView
from .views import JobListView
from .views import JobUpdateView
from .views import accept_quote
from .views import agent_list
from .views import download_quote
from .views import refuse_quote

app_name = "jobs"
urlpatterns = [
    path("", JobListView.as_view(), name="job_list"),
    path("create/", JobCreateView.as_view(), name="job_create"),
    path("<uuid:pk>/", JobDetailView.as_view(), name="job_detail"),
    path("<uuid:pk>/update/", JobUpdateView.as_view(), name="job_update"),
    path("<uuid:pk>/download-quote/", download_quote, name="download_quote"),
    path("<uuid:pk>/refuse-quote/", refuse_quote, name="refuse_quote"),
    path("<uuid:pk>/accept-quote/", accept_quote, name="accept_quote"),
    path("agents/", agent_list, name="agent_list"),
]
