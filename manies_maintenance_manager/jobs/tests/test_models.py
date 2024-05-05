"""Tests for the job models of Manies Maintenance Manager."""

import re
import uuid

import pytest

UUID_REGEX = (
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)


@pytest.mark.django_db()
def test_job_id_field_is_uuid():
    """Ensure the 'id' field of a Job instance is a valid UUID."""
    from manies_maintenance_manager.jobs.models import Job

    job = Job.objects.create(
        date="2022-01-01",
    )
    assert job.id is not None
    assert isinstance(job.id, uuid.UUID)
    uuid_length = 36
    assert len(str(job.id)) == uuid_length

    # Make sure that it matches the regex for a UUID, too:
    assert re.match(
        UUID_REGEX,
        str(job.id),
    )
