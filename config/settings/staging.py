"""Django staging settings for Marnie's Maintenance Manager project."""

# pylint: disable=wildcard-import, unused-wildcard-import

from .production import *  # noqa: F403
from .production import env

# Override the allowed hosts for staging
ALLOWED_HOSTS = env.list("DJANGO_ALLOWED_HOSTS", default=["mmm-staging2.ar-ciel.org"])

# Override the default 'from' email address
DEFAULT_FROM_EMAIL = "Marnie's Maintenance Manager <noreply@mmm-staging2.ar-ciel.org>"

# Any other staging-specific overrides can go here
