"""
URL configurations for the user management features of Marnie's Maintenance Manager.

This module defines the URL patterns for user interactions such as redirection,
user detail viewing, and user profile updating. These patterns help navigate
through different user-related views.
"""

from django.urls import path

from .views import user_detail_view
from .views import user_redirect_view
from .views import user_update_view

app_name = "users"
urlpatterns = [
    path("~redirect/", view=user_redirect_view, name="redirect"),
    path("~update/", view=user_update_view, name="update"),
    path("<str:username>/", view=user_detail_view, name="detail"),
]
