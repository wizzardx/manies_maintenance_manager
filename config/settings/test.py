"""With these settings, tests run faster."""

# pylint: disable=wildcard-import, unused-wildcard-import
from .base import *  # noqa: F403
from .base import TEMPLATES
from .base import env

# GENERAL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#secret-key
SECRET_KEY = env(
    "DJANGO_SECRET_KEY",
    default="BjxV78fJZFLRaZVApWzLo5gbT2D0tF2Zx6k2mmy0qZotV09KJpUKkcL2gesdFfkM",
)
# https://docs.djangoproject.com/en/dev/ref/settings/#test-runner
TEST_RUNNER = "django.test.runner.DiscoverRunner"

# PASSWORDS
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#password-hashers
PASSWORD_HASHERS = ["django.contrib.auth.hashers.MD5PasswordHasher"]

# EMAIL
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#email-backend
EMAIL_BACKEND = "django.core.mail.backends.locmem.EmailBackend"

# DEBUGGING FOR TEMPLATES
# ------------------------------------------------------------------------------
TEMPLATES[0]["OPTIONS"]["debug"] = True  # type: ignore[index]

# MEDIA
# ------------------------------------------------------------------------------
# https://docs.djangoproject.com/en/dev/ref/settings/#media-url
# Disabled in this project, we're using our own secured views to serve media files.

# ------------------------------------------------------------------------------
# Your stuff...
# ------------------------------------------------------------------------------

# https://github.com/boxed/django-fastdev#usage
INSTALLED_APPS += ["django_fastdev"]  # noqa: F405

# https://docs.djangoproject.com/en/dev/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ["django"]

# django-allauth
# ------------------------------------------------------------------------------
# Disable rate limiting during tests. Functional tests sign in many times from the
# same IP (the live server / Docker container), which trips allauth's default
# `login: 30/m/ip` limit and returns a 429 (surfacing as a "Server Error"). Note
# that `{}` does NOT work here: allauth merges the supplied dict over its defaults,
# so only the sentinel `False` fully disables rate limiting.
# https://docs.allauth.org/en/latest/account/rate_limits.html
ACCOUNT_RATE_LIMITS = False
