# ruff: noqa
"""Define URL patterns for the Django project."""

from django.conf import settings
from django.contrib import admin
from django.urls import include
from django.urls import path, re_path
from django.views import defaults as default_views
from django.views.generic import TemplateView
from marnies_maintenance_manager.jobs.views.home_page_view import home_page
from marnies_maintenance_manager.jobs.views.serve_protected_media_view import (
    serve_protected_media,
)

urlpatterns = [
    path("", home_page, name="home"),
    path(
        "about/",
        TemplateView.as_view(template_name="pages/about.html"),
        name="about",
    ),
    # Django Admin, use {% url 'admin:index' %}
    path(settings.ADMIN_URL, admin.site.urls),
    # User management
    path(
        "users/", include("marnies_maintenance_manager.users.urls", namespace="users")
    ),
    path("accounts/", include("allauth.urls")),
    # Your stuff: custom urls includes go here
    path("jobs/", include("marnies_maintenance_manager.jobs.urls", namespace="jobs")),
    # Media files:
    re_path(r"^media/(?P<path>.*)$", serve_protected_media),
]


if settings.DEBUG:
    # This allows the error pages to be debugged during development, just visit
    # these url in browser to see how these error pages look like.
    urlpatterns += [
        path(
            "400/",
            default_views.bad_request,
            kwargs={"exception": Exception("Bad Request!")},
        ),
        path(
            "403/",
            default_views.permission_denied,
            kwargs={"exception": Exception("Permission Denied")},
        ),
        path(
            "404/",
            default_views.page_not_found,
            kwargs={"exception": Exception("Page not Found")},
        ),
        path("500/", default_views.server_error),
    ]
    # pylint: disable=magic-value-comparison
    if "debug_toolbar" in settings.INSTALLED_APPS:
        import debug_toolbar

        urlpatterns = [path("__debug__/", include(debug_toolbar.urls))] + urlpatterns
