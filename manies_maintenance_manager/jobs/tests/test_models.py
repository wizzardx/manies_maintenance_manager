"""Tests for the job models of Manie's Maintenance Manager."""

# pylint: disable=no-self-use, magic-value-comparison, redefined-outer-name

import datetime
import re
import uuid
from unittest.mock import patch

import django
import model_utils
import private_storage
import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.core.validators import FileExtensionValidator
from django.db.models.fields.files import FileField
from django.db.models.fields.files import ImageFieldFile
from django.db.models.fields.related_descriptors import ForwardManyToOneDescriptor
from django.db.utils import IntegrityError
from django.forms.models import ModelForm
from django.urls import reverse
from typeguard import check_type

from manies_maintenance_manager.jobs.models import Job
from manies_maintenance_manager.jobs.models import JobCompletionPhoto
from manies_maintenance_manager.jobs.utils import safe_read
from manies_maintenance_manager.jobs.validators import validate_pdf_contents
from manies_maintenance_manager.users.models import User

UUID_REGEX = (
    r"^[0-9a-f]{8}-[0-9a-f]{4}-[1-5][0-9a-f]{3}-[89ab][0-9a-f]{3}-[0-9a-f]{12}$"
)

BASIC_TEST_JPG_FILE_SIZE = 138782


@pytest.mark.django_db()
def test_job_id_field_is_uuid(bob_agent_user: User) -> None:
    """Ensure the 'id' field of a Job instance is a valid UUID.

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
        address_details="1234 Main St, Springfield, IL",
        gps_link="https://www.google.com/maps",
        quote_request_details="Replace the kitchen sink",
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

    def test_creating_a_job_with_an_invalid_agent(self, manie_user: User) -> None:
        """Ensure job creation fails when the agent is not flagged as an Agent.

        Args:
            manie_user (User): User instance representing Manie, who is not an agent.
        """
        with pytest.raises(ValidationError) as err:
            Job.objects.create(
                agent=manie_user,  # Manie is not a valid agent.
                date="2022-01-01",
                address_details="1234 Main St, Springfield, IL",
                gps_link="https://www.google.com/maps",
                quote_request_details="Replace the kitchen sink",
            )

        assert err.value.message_dict["agent"] == [
            "manie is not an Agent.",
        ], "The error message should indicate that the agent is not an agent user."

    def test_creating_a_job_with_a_valid_user_agent(self, bob_agent_user: User) -> None:
        """Ensure job creation succeeds with a user flagged as an Agent.

        Args:
            bob_agent_user (User): The agent user Bob used to validate job creation.
        """
        Job.objects.create(
            agent=bob_agent_user,
            date="2022-01-01",
            address_details="1234 Main St, Springfield, IL",
            gps_link="https://www.google.com/maps",
            quote_request_details="Replace the kitchen sink",
        )

    def test_updating_a_job_with_an_invalid_agent(
        self,
        job_created_by_bob: Job,
        manie_user: User,
    ) -> None:
        """Ensure updating a job fails when the new agent is not flagged as an Agent.

        Args:
            job_created_by_bob (Job): Job instance created by Bob, initially with a
                                      valid agent.
            manie_user (User): User instance for Manie, intended to be set as the
                                agent but is invalid.
        """
        job = job_created_by_bob
        job.agent = manie_user
        with pytest.raises(ValidationError) as err:
            job.full_clean()  # pragma: no branch
        assert err.value.message_dict["agent"] == [
            "manie is not an Agent.",
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
    job1, job2 = _create_two_test_jobs(bob_agent_user)

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


def _create_two_test_jobs(agent_user: User) -> tuple[Job, Job]:
    """Create two job instances for testing.

    Args:
        agent_user (User): The agent user used to create Job instances.

    Returns:
        tuple[Job, Job]: The created job instances.
    """
    job1 = Job.objects.create(
        agent=agent_user,
        date="2022-01-01",
        address_details="1234 Main St, Springfield, IL",
        gps_link="https://www.google.com/maps",
        quote_request_details="Replace the kitchen sink",
    )

    job2 = Job.objects.create(
        agent=agent_user,
        date="2022-01-02",
        address_details="1235 Main St, Springfield, IL",
        gps_link="https://www.google.com/maps",
        quote_request_details="Replace the bathroom sink",
    )

    return job1, job2


def _create_three_test_jobs(
    bob_agent_user: User,
    alice_agent_user: User,
) -> tuple[Job, Job, Job]:
    job1, job2 = _create_two_test_jobs(bob_agent_user)

    job3 = Job.objects.create(
        agent=alice_agent_user,
        date="2022-01-01",
        address_details="1236 Main St, Springfield, IL",
        gps_link="https://www.google.com/maps",
        quote_request_details="Replace the toilet",
    )

    return job1, job2, job3


class TestJobModelPerAgentAutoIncrementingNumberField:
    """Define tests for the Job model's auto-incrementing 'number' field per agent."""

    @pytest.mark.django_db()
    def test_number_field_auto_increment_per_agent(
        self,
        bob_agent_user: User,
        alice_agent_user: User,
    ) -> None:
        """Ensure the 'number' field auto-increments per agent.

        Args:
            bob_agent_user (User): The agent user Bob used to create a Job instance.
            alice_agent_user (User): The agent user Alice used to create a Job instance.
        """
        (job1, job2, job3) = _create_three_test_jobs(bob_agent_user, alice_agent_user)

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
        alice_agent_user: User,
    ) -> None:
        """Ensure the 'number' field increments only within the same agent.

        Args:
            bob_agent_user (User): The agent user Bob used to create a Job instance.
            alice_agent_user (User): The agent user Alice used to create a Job instance.
        """
        (job1, job2, job3) = _create_three_test_jobs(bob_agent_user, alice_agent_user)

        job4 = Job.objects.create(
            agent=alice_agent_user,
            date="2022-01-02",
            address_details="1237 Main St, Springfield, IL",
            gps_link="https://www.google.com/maps",
            quote_request_details="Replace the toilet",
        )

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

        # This one raises:
        with pytest.raises(ValidationError):
            job1.full_clean()

        # This also raises:
        with pytest.raises(ValidationError):
            job1.save()


def test_has_date_of_inspection_field() -> None:
    """Ensure the Job model has a 'date_of_inspection' field."""
    assert hasattr(Job, "date_of_inspection")


def test_has_quote_field() -> None:
    """Ensure the Job model has a 'quote' field."""
    assert hasattr(Job, "quote")


def test_valid_values_for_accept_or_reject_field(job_created_by_bob: Job) -> None:
    """Ensure the 'accept_or_reject' field only accepts 'accept' or 'reject'.

    Args:
        job_created_by_bob (Job): Job instance created by Bob.
    """
    # Check for errors with supported values:
    job = job_created_by_bob

    # The default 'empty' value is allowed (for strings we use "" instead of None):
    job.accepted_or_rejected = ""
    job.full_clean()

    job.accepted_or_rejected = "accepted"
    job.full_clean()

    job.accepted_or_rejected = "rejected"
    job.full_clean()

    # Check for errors with unsupported values:
    job.accepted_or_rejected = "unknown"
    with pytest.raises(ValidationError) as err:
        job.full_clean()
    assert err.value.message_dict["accepted_or_rejected"] == [
        "Value 'unknown' is not a valid choice.",
    ]

    job.accepted_or_rejected = None  # type: ignore[assignment]
    job.full_clean()  # Should not raise
    with pytest.raises(IntegrityError) as err:  # type: ignore[assignment]
        job.save()

    # SQLite3 text:
    expected_1 = "NOT NULL constraint failed: jobs_job.accepted_or_rejected"
    # PostgreSQL text:
    expected_2 = (
        'null value in column "accepted_or_rejected" of relation "jobs_job" '
        "violates not-null constraint"
    )

    err_str = str(err.value)
    assert expected_1 in err_str or expected_2 in err_str


def test_has_deposit_proof_of_payment_field() -> None:
    """Ensure the Job model has a 'deposit_proof_of_payment' field."""
    assert hasattr(Job, "deposit_proof_of_payment")


def test_deposit_proof_of_payment_field_is_setup_correctly() -> None:
    """Ensure the 'deposit_proof_of_payment' field is set up correctly."""
    field = Job.deposit_proof_of_payment.field
    assert field.null is True
    assert field.blank is True
    assert field.upload_to == "deposit_pops/"
    assert field.storage is not None
    assert field.help_text == "Upload the deposit proof of payment here."
    assert field.verbose_name == "Deposit Proof of Payment"

    # Only the .pdf file extension is allowed and the PDF contents must be valid:
    assert_pdf_field_validators(field)


def assert_pdf_field_validators(field: FileField) -> None:
    """Ensure the validators for a field are correctly set up for PDF files.

    Args:
        field (FileField): The file field to check.
    """
    # Only the .pdf file extension is allowed:
    validators = check_type(field.validators, list)
    num_validators_used_for_pdf = 2
    assert len(validators) == num_validators_used_for_pdf
    assert isinstance(validators[0], FileExtensionValidator)
    assert validators[0].allowed_extensions == ["pdf"]

    # The PDF file contents must be valid:
    # pylint: disable=comparison-with-callable
    assert validators[1] == validate_pdf_contents


def test_full_clean_is_called_on_save(bob_agent_user: User) -> None:
    """Ensure that the full_clean method is called on save.

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

    # This should not raise an exception:
    job.save()

    # This should raise an exception:
    # noinspection SpellCheckingInspection
    job.status = "zzzzzz"

    with pytest.raises(ValidationError):
        job.save()


def test_job_onsite_work_completion_date_is_setup_correctly() -> None:
    """Ensure the 'job_onsite_work_completion_date' field is set up correctly."""
    # pylint: disable=no-member
    # noinspection PyUnresolvedReferences
    field = Job.job_onsite_work_completion_date.field
    assert field.null is True
    assert field.blank is True
    assert field.help_text == "Date when onsite work was completed."
    assert field.verbose_name == "Job Date"


def test_invoice_field_is_setup_correctly() -> None:
    """Ensure the 'invoice' field is set up correctly."""
    field = Job.invoice.field
    assert field.null is True
    assert field.blank is True
    assert field.upload_to == "invoices/"
    assert field.storage is not None
    assert field.verbose_name == "Invoice"
    assert field.help_text == "Upload the invoice here."

    # Only the .pdf file extension is allowed and the PDF contents must be valid:
    assert_pdf_field_validators(field)


def test_comments_field_is_setup_correctly() -> None:
    """Ensure the 'comments' field is set up correctly."""
    # pylint: disable=no-member
    # noinspection PyUnresolvedReferences
    field = Job.comments.field
    assert field.default == ""
    assert field.blank is True
    assert field.verbose_name == "Comments"
    assert field.help_text == "Add any comments you have about the job here."


def test_has_complete_field() -> None:
    """Ensure the Job model has a 'complete' field."""
    assert hasattr(Job, "complete")


class TestFinalPaymentPOPField:
    """Tests for the 'final_payment_pop' field of the Job model."""

    def test_has_final_payment_pop_field(self) -> None:
        """Ensure the Job model has a 'final_payment_pop' field."""
        assert hasattr(Job, "final_payment_pop")

    def test_final_payment_pop_field_is_setup_correctly(self) -> None:
        """Ensure the 'final_payment_pop' field is set up correctly."""
        field = Job.final_payment_pop.field
        assert field.null is True
        assert field.blank is True
        assert field.upload_to == "final_payment_pops/"
        assert field.storage is not None
        assert field.verbose_name == "Final Payment Proof of Payment"
        assert field.help_text == "Upload the final payment proof of payment here."

        # Only the .pdf file extension is allowed and the PDF contents must be valid:
        assert_pdf_field_validators(field)


@pytest.fixture()
def job_completion_photo(
    job_created_by_bob: Job,
    test_image: SimpleUploadedFile,
) -> JobCompletionPhoto:
    """Create a JobCompletionPhoto instance for testing.

    Args:
        job_created_by_bob (Job): Job instance created by Bob.
        test_image (SimpleUploadedFile): A simple uploaded file for testing.

    Returns:
        JobCompletionPhoto: The created JobCompletionPhoto instance.
    """
    with safe_read(test_image):
        return JobCompletionPhoto.objects.create(
            job=job_created_by_bob,
            photo=test_image,
        )


@pytest.mark.django_db()
class TestJobCompletionPhoto:
    """Tests for the JobCompletionPhoto model."""

    @staticmethod
    def test_has_uuid_id_field(job_completion_photo: JobCompletionPhoto) -> None:
        """Ensure the JobCompletionPhoto model has an 'id' field that is a valid UUID.

        Args:
            job_completion_photo (JobCompletionPhoto): JobCompletionPhoto instance.
        """
        # Check an instance of the JobCompletionPhoto model
        assert job_completion_photo.id is not None
        assert isinstance(job_completion_photo.id, uuid.UUID)
        uuid_length = 36
        assert len(str(job_completion_photo.id)) == uuid_length
        assert re.match(UUID_REGEX, str(job_completion_photo.id))

        # Also check the JobCompletionPhoto class
        assert isinstance(
            JobCompletionPhoto.id,
            django.db.models.query_utils.DeferredAttribute,
        )
        idfield = JobCompletionPhoto.id.field  # pylint: disable=no-member
        assert isinstance(idfield, model_utils.fields.UUIDField)

    @staticmethod
    def test_has_created_field(job_completion_photo: JobCompletionPhoto) -> None:
        """Ensure the JobCompletionPhoto model has a 'created' field.

        Args:
            job_completion_photo (JobCompletionPhoto): JobCompletionPhoto instance
        """
        # Check an instance of the JobCompletionPhoto model
        assert job_completion_photo.created is not None
        assert isinstance(job_completion_photo.created, datetime.datetime)

        # Also check the JobCompletionPhoto class
        assert hasattr(JobCompletionPhoto, "created")
        assert isinstance(
            JobCompletionPhoto.created,
            django.db.models.query_utils.DeferredAttribute,
        )

        field = JobCompletionPhoto.created.field  # pylint: disable=no-member
        assert isinstance(field, model_utils.fields.AutoCreatedField)
        assert field.auto_now_add is False
        assert field.auto_now is False
        assert field.verbose_name == "created"

    @staticmethod
    def test_has_job_foreign_key_field(
        job_completion_photo: JobCompletionPhoto,
    ) -> None:
        """Ensure the JobCompletionPhoto model has a 'job' field.

        Args:
            job_completion_photo (JobCompletionPhoto): JobCompletionPhoto instance
        """
        # Check an instance of the JobCompletionPhoto model
        assert job_completion_photo.job is not None
        assert isinstance(job_completion_photo.job, Job)
        assert hasattr(job_completion_photo.job, "job_completion_photos")
        assert (
            job_completion_photo.job.job_completion_photos.__class__.__name__
            == "RelatedManager"
        )

        # Also check the JobCompletionPhoto class
        assert hasattr(JobCompletionPhoto, "job")
        assert JobCompletionPhoto.job.__class__.__name__ == "ForwardManyToOneDescriptor"
        assert isinstance(JobCompletionPhoto.job, ForwardManyToOneDescriptor)

    @staticmethod
    def test_has_photo_field(job_completion_photo: JobCompletionPhoto) -> None:
        """Ensure the JobCompletionPhoto model has a 'photo' field.

        Args:
            job_completion_photo (JobCompletionPhoto): JobCompletionPhoto instance
        """
        # Check an instance of the JobCompletionPhoto model
        photo = check_type(job_completion_photo.photo, ImageFieldFile)
        photo_name = check_type(photo.name, str)

        # eg photo.name: 'completion_photos/test_ofzSmry.jpp'
        assert photo_name.startswith("completion_photos/test_")
        assert photo_name.endswith(".jpg")

        # eg photo.url: '/private-media/completion_photos/test_OmnPAY5.jpg'
        assert photo.url.startswith("/private-media/completion_photos/test_")
        assert photo.url.endswith(".jpg")

        # Check the file exists and has the correct size
        assert photo.storage.exists(photo_name)
        assert photo.storage.size(photo_name) == BASIC_TEST_JPG_FILE_SIZE

        # Also check the JobCompletionPhoto class
        assert hasattr(JobCompletionPhoto, "photo")
        descriptor = JobCompletionPhoto.photo
        assert isinstance(descriptor, django.db.models.fields.files.ImageFileDescriptor)
        field = descriptor.field
        assert isinstance(field, private_storage.fields.PrivateImageField)
        assert field.upload_to == "completion_photos/"
        assert field.storage is not None
        assert field.verbose_name == "photo"
        assert field.null is False
        assert field.blank is False

    @staticmethod
    def test_str_method(job_completion_photo: JobCompletionPhoto) -> None:
        """Ensure the __str__ method returns the job date and the start of the address.

        Args:
            job_completion_photo (JobCompletionPhoto): JobCompletionPhoto instance.
        """
        photo = job_completion_photo
        assert str(photo) == (
            f"Photo for job {photo.job.number} of agent "
            f"{photo.job.agent.username}, uploaded at {photo.created}"
        )

    @staticmethod
    def test_job_completion_photo_save_calls_full_clean(
        bob_agent_user: User,
        test_image: SimpleUploadedFile,
    ) -> None:
        """Ensure the full_clean method is called before saving a JobCompletionPhoto.

        Args:
            bob_agent_user (User): The agent user Bob used to create a Job instance.
            test_image (SimpleUploadedFile): A simple uploaded file for testing.
        """
        # Create a job instance
        job = Job.objects.create(
            agent=bob_agent_user,
            date="2022-01-01",
            address_details="1234 Main St, Springfield, IL",
            gps_link="https://www.google.com/maps",
            quote_request_details="Replace the kitchen sink",
        )

        # Create a JobCompletionPhoto instance
        with safe_read(test_image):
            job_completion_photo = JobCompletionPhoto(job=job, photo=test_image)

            # Patch the full_clean method to assert it gets called
            with patch.object(
                job_completion_photo,
                "full_clean",
                wraps=job_completion_photo.full_clean,
            ) as mock_full_clean:
                job_completion_photo.save()

        # Assert that full_clean was called
        mock_full_clean.assert_called_once()

        # Ensure the instance was saved correctly
        saved_photo = JobCompletionPhoto.objects.get(pk=job_completion_photo.pk)
        assert saved_photo is not None
        assert saved_photo.job == job
        assert saved_photo.photo.name == job_completion_photo.photo.name
        assert saved_photo.photo.url == job_completion_photo.photo.url
