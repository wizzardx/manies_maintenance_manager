"""Tests for the job models of Marnie's Maintenance Manager."""

import re
import uuid

import pytest
from django.core.exceptions import ValidationError

from marnies_maintenance_manager.jobs.models import Job
from marnies_maintenance_manager.users.models import User

UUID_REGEX = (
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)


@pytest.mark.django_db()
def test_job_id_field_is_uuid(bob_agent_user: User) -> None:
    """Ensure the 'id' field of a Job instance is a valid UUID."""
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


def test_agent_field_is_not_editable(bob_agent_user: User) -> None:
    """Verify the 'agent' field is not editable in the Job model form."""
    # Making the agent field "not editable" is the closest I can do to making it
    # read-only

    # Create a user instance
    job = Job.objects.create(
        agent=bob_agent_user,
        date="2022-01-01",
    )

    # For this test, create a ModeLForm based on all fields in the Job model
    from django.forms.models import ModelForm

    class JobForm(ModelForm):  # type: ignore[type-arg]
        class Meta:
            model = Job
            fields = "__all__"  # noqa: DJ007

    form = JobForm(instance=job)

    # Check that the 'agent' field is not present:
    assert (
        "agent" not in form.fields
    ), "The 'agent' field should not be present in the form"


class TestJobAgentMustBeAUserOfTypeAgent:
    """Define tests to ensure a Job's agent is explicitly flagged as an Agent."""

    def test_creating_a_job_with_an_invalid_agent(self, marnie_user: User) -> None:
        """Ensure job creation fails when the agent is not flagged as an Agent."""
        job = Job.objects.create(
            agent=marnie_user,  # Marnie is not a valid agent.
            date="2022-01-01",
        )
        with pytest.raises(ValidationError) as err:
            job.full_clean()

        assert err.value.message_dict["agent"] == [
            "marnie is not an Agent.",
        ], "The error message should indicate that the agent is not an agent user."

    def test_creating_a_job_with_a_valid_user_agent(self, bob_agent_user: User) -> None:
        """Ensure job creation succeeds with a user flagged as an Agent."""
        job = Job.objects.create(
            agent=bob_agent_user,
            date="2022-01-01",
            address_details="1234 Main St, Springfield, IL",
            gps_link="https://www.google.com/maps",
            quote_request_details="Replace the kitchen sink",
        )
        job.full_clean()

    def test_updating_a_job_with_an_invalid_agent(
        self,
        job_created_by_bob: Job,
        marnie_user: User,
    ) -> None:
        """Ensure updating a job fails when the new agent is not flagged as an Agent."""
        job = job_created_by_bob
        job.agent = marnie_user
        with pytest.raises(ValidationError) as err:
            job.full_clean()  # pragma: no branch
        assert err.value.message_dict["agent"] == [
            "marnie is not an Agent.",
        ], "The error message should indicate that the agent is not an agent user."

    def test_updating_a_job_with_a_valid_user(
        self,
        job_created_by_bob: Job,
        bob_agent_user: User,
    ) -> None:
        """Ensure updating a job's agent to another flagged Agent succeeds."""
        job = job_created_by_bob
        job.agent = bob_agent_user
        job.full_clean()
