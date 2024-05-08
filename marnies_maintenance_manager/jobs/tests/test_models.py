"""Tests for the job models of Marnie's Maintenance Manager."""

import re
import uuid

import pytest

from marnies_maintenance_manager.users.models import User

UUID_REGEX = (
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)


@pytest.mark.django_db()
def test_job_id_field_is_uuid(bob_agent_user: User) -> None:
    """Ensure the 'id' field of a Job instance is a valid UUID."""
    from marnies_maintenance_manager.jobs.models import Job

    job = Job.objects.create(
        agent=bob_agent_user,
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
