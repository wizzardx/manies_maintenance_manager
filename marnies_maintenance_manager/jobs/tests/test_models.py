"""Tests for the job models of Marnie's Maintenance Manager."""

import datetime
import re
import uuid

import pytest
from django.core.exceptions import ValidationError
from django.db.utils import IntegrityError
from django.forms.models import ModelForm
from django.urls import reverse

from marnies_maintenance_manager.jobs.models import Job
from marnies_maintenance_manager.users.models import User

UUID_REGEX = (
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)

# pylint: disable=no-self-use, magic-value-comparison


@pytest.mark.django_db()
def test_job_id_field_is_uuid(bob_agent_user: User) -> None:
    """Ensure the 'id' field of a Job instance is a valid UUID.

    Args:
        bob_agent_user (User): The agent user Bob used to create a Job instance.
    """
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
    """Verify the 'agent' field is not editable in the Job model form.

    Args:
        bob_agent_user (User): The agent user Bob used to create a Job instance.
    """
    # Making the agent field "not editable" is the closest I can do to making it
    # read-only

    # Create a user instance
    job = Job.objects.create(
        agent=bob_agent_user,
        date="2022-01-01",
    )

    # For this test, create a ModeLForm based on all fields in the Job model

    class JobForm(ModelForm):  # type: ignore[type-arg]
        """ModelForm for the Job model."""

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
        """Ensure job creation fails when the agent is not flagged as an Agent.

        Args:
            marnie_user (User): User instance representing Marnie, who is not an agent.
        """
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
        """Ensure job creation succeeds with a user flagged as an Agent.

        Args:
            bob_agent_user (User): The agent user Bob used to validate job creation.
        """
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
        """Ensure updating a job fails when the new agent is not flagged as an Agent.

        Args:
            job_created_by_bob (Job): Job instance created by Bob, initially with a
                                      valid agent.
            marnie_user (User): User instance for Marnie, intended to be set as the
                                agent but is invalid.
        """
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
        """Ensure updating a job's agent to another flagged Agent succeeds.

        Args:
            job_created_by_bob (Job): Job initially created by Bob, for which agent
                                      will be updated.
            bob_agent_user (User): Bob's user instance, an agent, reassigned to the job.
        """
        job = job_created_by_bob
        job.agent = bob_agent_user
        job.full_clean()


def test_str_method_returns_job_date_and_start_of_address(bob_agent_user: User) -> None:
    """Ensure the __str__ method returns the job date and the start of the address.

    Args:
        bob_agent_user (User): The agent user Bob used to create a Job instance.
    """
    job = Job.objects.create(
        agent=bob_agent_user,
        date="2022-01-01",
        address_details="1234 Main St, Springfield, IL",
        gps_link="https://www.google.com/maps",
        quote_request_details="Replace the kitchen sink",
    )

    assert str(job) == "2022-01-01: 1234 Main St, Springfield, IL"


def test_str_method_only_contains_up_to_50_characters_of_address(
    bob_agent_user: User,
) -> None:
    """Ensure __str__ only returns the first 50 characters of the address.

    Args:
        bob_agent_user (User): The agent user Bob used to create a Job instance with a
                               long address.
    """
    job = Job.objects.create(
        agent=bob_agent_user,
        date="2022-01-01",
        address_details="1234 Main St, Springfield, IL",
        gps_link="https://www.google.com/maps",
        quote_request_details="Replace the kitchen sink",
    )

    job.address_details = (
        "1234 Main St, Springfield, IL, USA, Earth, Milky Way, Universe"
    )
    assert str(job) == "2022-01-01: 1234 Main St, Springfield, IL, USA, Earth, Milky W"


def test_str_method_converts_newlines_in_address_to_spaces(
    bob_agent_user: User,
) -> None:
    """Ensure the __str__ method converts newlines in the address to spaces.

    Args:
        bob_agent_user (User): The agent user Bob used to create a Job instance with
                               newline characters in the address.
    """
    job = Job.objects.create(
        agent=bob_agent_user,
        date="2022-01-01",
        address_details="1234 Main St,\nSpringfield, IL",
        gps_link="https://www.google.com/maps",
        quote_request_details="Replace the kitchen sink",
    )

    assert str(job) == "2022-01-01: 1234 Main St, Springfield, IL"


def test_job_model_has_a_canonical_website_location(job_created_by_bob: Job) -> None:
    """Ensure the Job model has a canonical website location.

    Args:
        job_created_by_bob (Job): Job instance created by Bob.
    """
    assert job_created_by_bob.get_absolute_url() == reverse(
        "jobs:job_detail",
        kwargs={"pk": job_created_by_bob.pk},
    )


def test_job_model_ordered_by_db_insertion_time(bob_agent_user: User) -> None:
    """Ensure Job instances are ordered by the time of insertion into the database.

    Args:
        bob_agent_user (User): The agent user Bob used to create Job instances.
    """
    job1 = Job.objects.create(
        agent=bob_agent_user,
        date="2022-01-01",
        address_details="1234 Main St, Springfield, IL",
        gps_link="https://www.google.com/maps",
        quote_request_details="Replace the kitchen sink",
    )

    job2 = Job.objects.create(
        agent=bob_agent_user,
        date="2022-01-02",
        address_details="1235 Main St, Springfield, IL",
        gps_link="https://www.google.com/maps",
        quote_request_details="Replace the bathroom sink",
    )

    job3 = Job.objects.create(
        agent=bob_agent_user,
        date="2022-01-03",
        address_details="1236 Main St, Springfield, IL",
        gps_link="https://www.google.com/maps",
        quote_request_details="Replace the toilet",
    )

    # Check that "ordering by creation time" is the default setting in the model:
    # (this is not really BDD/behavioral testing, but it's a good sanity check)
    assert Job._meta.ordering == ["created"]  # noqa: SLF001

    # If the above works, then the following checks should always pass:
    jobs = Job.objects.all()
    assert list(jobs) == [job1, job2, job3]
    assert jobs[0].date == datetime.date(2022, 1, 1)
    assert jobs[1].date == datetime.date(2022, 1, 2)
    assert jobs[2].date == datetime.date(2022, 1, 3)


def _create_three_test_jobs(
    bob_agent_user: User,
    peter_agent_user: User,
) -> tuple[Job, Job, Job]:
    job1 = Job.objects.create(
        agent=bob_agent_user,
        date="2022-01-01",
        address_details="1234 Main St, Springfield, IL",
        gps_link="https://www.google.com/maps",
        quote_request_details="Replace the kitchen sink",
    )
    job1.full_clean()

    job2 = Job.objects.create(
        agent=bob_agent_user,
        date="2022-01-02",
        address_details="1235 Main St, Springfield, IL",
        gps_link="https://www.google.com/maps",
        quote_request_details="Replace the bathroom sink",
    )
    job2.full_clean()

    job3 = Job.objects.create(
        agent=peter_agent_user,
        date="2022-01-01",
        address_details="1236 Main St, Springfield, IL",
        gps_link="https://www.google.com/maps",
        quote_request_details="Replace the toilet",
    )
    job3.full_clean()

    return job1, job2, job3


class TestJobModelPerAgentAutoIncrementingNumberField:
    """Define tests for the Job model's auto-incrementing 'number' field per agent."""

    @pytest.mark.django_db()
    def test_number_field_auto_increment_per_agent(
        self,
        bob_agent_user: User,
        peter_agent_user: User,
    ) -> None:
        """Ensure the 'number' field auto-increments per agent.

        Args:
            bob_agent_user (User): The agent user Bob used to create a Job instance.
            peter_agent_user (User): The agent user Peter used to create a Job instance.
        """
        (job1, job2, job3) = _create_three_test_jobs(bob_agent_user, peter_agent_user)

        assert job1.number == 1
        assert job2.number == 2  # noqa: PLR2004
        assert job3.number == 1

    @pytest.mark.django_db()
    def test_number_field_is_readonly(self) -> None:
        """Ensure the 'number' field is read-only in the Job model form."""

        class JobForm(ModelForm):  # type: ignore[type-arg]
            """ModelForm for the Job model."""

            class Meta:
                model = Job
                fields = "__all__"  # noqa: DJ007

        form = JobForm()
        assert "number" not in form.fields

    @pytest.mark.django_db()
    def test_number_field_increment_only_within_agent(
        self,
        bob_agent_user: User,
        peter_agent_user: User,
    ) -> None:
        """Ensure the 'number' field increments only within the same agent.

        Args:
            bob_agent_user (User): The agent user Bob used to create a Job instance.
            peter_agent_user (User): The agent user Peter used to create a Job instance.
        """
        (job1, job2, job3) = _create_three_test_jobs(bob_agent_user, peter_agent_user)

        job4 = Job.objects.create(
            agent=peter_agent_user,
            date="2022-01-02",
            address_details="1237 Main St, Springfield, IL",
            gps_link="https://www.google.com/maps",
            quote_request_details="Replace the toilet",
        )
        job4.full_clean()

        assert job1.number == 1
        assert job2.number == 2  # noqa: PLR2004
        assert job3.number == 1
        assert job4.number == 2  # noqa: PLR2004

    def test_agent_and_number_unique_together(self, bob_agent_user: User) -> None:
        """Ensure that the combination of agent and number is unique together.

        Args:
            bob_agent_user (User): The agent user Bob used to create a Job instance.

        """
        # Create job twice, with the same user.
        job1 = Job.objects.create(
            agent=bob_agent_user,
            date="2022-01-01",
            address_details="1234 Main St, Springfield, IL",
            gps_link="https://www.google.com/maps",
            quote_request_details="Replace the kitchen sink",
        )

        job2 = Job.objects.create(
            agent=bob_agent_user,
            date="2022-01-01",
            address_details="1234 Main St, Springfield, IL",
            gps_link="https://www.google.com/maps",
            quote_request_details="Replace the kitchen sink",
        )

        # Confirm that they got the expected job number.
        assert job1.number == 1
        assert job2.number == 2  # noqa: PLR2004

        # Confirm that it's an error to try to reuse the same agent job number.
        job1.number = 2
        with pytest.raises(IntegrityError):
            job1.save()


def test_has_date_of_inspection_field() -> None:
    """Ensure the Job model has a 'date_of_inspection' field."""
    assert hasattr(Job, "date_of_inspection")


def test_has_quote_field() -> None:
    """Ensure the Job model has a 'quote' field."""
    assert hasattr(Job, "quote")
