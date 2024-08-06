"""URL routing definitions for the jobs module in the Manie's Maintenance Manager.

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

from .views.agent_export_jobs_to_spreadsheet_view import (
    agent_export_jobs_to_spreadsheet_view,
)
from .views.agent_list_view import agent_list
from .views.deposit_pop_update_view import DepositPOPUpdateView
from .views.final_payment_pop_update_view import FinalPaymentPOPUpdateView
from .views.job_complete_inspection import JobCompleteInspectionView
from .views.job_complete_onsite_work_view import JobCompleteOnsiteWorkView
from .views.job_create_view import JobCreateView
from .views.job_detail_view import JobDetailView
from .views.job_list_view import JobListView
from .views.job_submit_documentation_view import JobSubmitDocumentationView
from .views.quote_accept_view import quote_accept
from .views.quote_reject_view import quote_reject
from .views.quote_update_view import QuoteUpdateView
from .views.quote_upload_view import QuoteUploadView

app_name = "jobs"
urlpatterns = [
    path("", JobListView.as_view(), name="job_list"),
    path("agents/", agent_list, name="agent_list"),
    path(
        "agents/<uuid:pk>/export_jobs_to_spreadsheet/",
        agent_export_jobs_to_spreadsheet_view,
        name="agent_export_jobs_to_spreadsheet_view",
    ),
    path("create/", JobCreateView.as_view(), name="job_create"),
    path("<uuid:pk>/", JobDetailView.as_view(), name="job_detail"),
    path(
        "<uuid:pk>/complete_inspection/",
        JobCompleteInspectionView.as_view(),
        name="job_complete_inspection",
    ),
    path(
        "<uuid:pk>/complete_onsite_work/",
        JobCompleteOnsiteWorkView.as_view(),
        name="job_complete_onsite_work",
    ),
    path(
        "<uuid:pk>/submit_documentation/",
        JobSubmitDocumentationView.as_view(),
        name="job_submit_documentation",
    ),
    path("<uuid:pk>/quote/upload/", QuoteUploadView.as_view(), name="quote_upload"),
    path("<uuid:pk>/quote/accept/", quote_accept, name="quote_accept"),
    path("<uuid:pk>/quote/reject/", quote_reject, name="quote_reject"),
    path("<uuid:pk>/quote/update/", QuoteUpdateView.as_view(), name="quote_update"),
    path(
        "<uuid:pk>/deposit-pop/update/",
        DepositPOPUpdateView.as_view(),
        name="deposit_pop_update",
    ),
    path(
        "<uuid:pk>/final-payment-pop/update/",
        FinalPaymentPOPUpdateView.as_view(),
        name="final_payment_pop_update",
    ),
]
