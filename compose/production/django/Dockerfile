# define an alias for the specific python version used in this file.
FROM docker.io/python:3.12.4-slim-bookworm AS python

# Python build stage
FROM python AS python-build-stage

ARG BUILD_ENVIRONMENT=production

# Install apt packages
RUN apt-get update && apt-get install --no-install-recommends -y \
  # dependencies for building Python packages
  build-essential \
  # psycopg dependencies
  libpq-dev

# Requirements are installed here to ensure they will be cached.
COPY ./requirements .

# Create Python Dependency and Sub-Dependency Wheels.
RUN --mount=type=cache,target=/root/.cache/pip \
  pip install --upgrade pip && \
  pip wheel --wheel-dir /usr/src/app/wheels  \
  -r ${BUILD_ENVIRONMENT}.txt


# Python 'run' stage
FROM python AS python-run-stage

ARG BUILD_ENVIRONMENT=production
ARG APP_HOME=/app

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV BUILD_ENV=${BUILD_ENVIRONMENT}

WORKDIR ${APP_HOME}

RUN addgroup --system django \
    && adduser --system --ingroup django django


# Install required system dependencies
RUN apt-get update && apt-get install --no-install-recommends -y \
  # psycopg dependencies
  libpq-dev \
  # Translations dependencies
  gettext \
  # python-magic dependencies
  libmagic1 \
  # cleaning up unused files
  && apt-get purge -y --auto-remove -o APT::AutoRemove::RecommendsImportant=false \
  && rm -rf /var/lib/apt/lists/*

# All absolute dir copies ignore workdir instruction. All relative dir copies are wrt to the workdir instruction
# copy python dependency wheels from python-build-stage
COPY --from=python-build-stage /usr/src/app/wheels  /wheels/

# use wheels to install python dependencies
RUN pip install --no-cache-dir --no-index --find-links=/wheels/ /wheels/* \
  && rm -rf /wheels/


COPY --chown=django:django ./compose/production/django/entrypoint /entrypoint
RUN sed -i 's/\r$//g' /entrypoint
RUN chmod +x /entrypoint


COPY --chown=django:django ./compose/production/django/start /start
RUN sed -i 's/\r$//g' /start
RUN chmod +x /start


# copy application code to WORKDIR
COPY --chown=django:django . ${APP_HOME}

# make django owner of the WORKDIR directory as well.
RUN chown -R django:django ${APP_HOME}

# Switch to root user to compile messages
USER root

# Temporarily set environment variables to compile translations
RUN DJANGO_SECRET_KEY=temporary_secret_key \
    DJANGO_SETTINGS_MODULE="config.settings.production" \
    DATABASE_URL="" \
    DJANGO_ADMIN_URL=dummy_admin_url \
    DJANGO_SERVER_EMAIL=dummy_server_email \
    MAILGUN_API_KEY=dummy_mailgun_api_key \
    MAILGUN_DOMAIN=dummy_mailgun_domain \
    DJANGO_ACCOUNT_ALLOW_REGISTRATION=true \
    SENTRY_DSN=http://public_key@localhost/123 \
    WEB_CONCURRENCY=4 \
    python manage.py compilemessages

# Switch back to django user
USER django

ENTRYPOINT ["/entrypoint"]
