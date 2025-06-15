"""Django staging settings for Manie's Maintenance Manager project."""

# pylint: disable=wildcard-import, unused-wildcard-import

from .production import *  # noqa: F403
from .production import env

# Override the allowed hosts for staging
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["mmm-staging3.ar-ciel.org"])

# Override the default 'from' email address
DEFAULT_FROM_EMAIL = "Manie's Maintenance Manager <noreply@mmm-staging3.ar-ciel.org>"

# Any other staging-specific overrides can go here
