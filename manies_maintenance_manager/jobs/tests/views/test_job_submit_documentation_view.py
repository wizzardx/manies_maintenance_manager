"""Tests for the JobCompleteView view."""

# pylint: disable=magic-value-comparison

from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django.http import HttpResponseRedirect
from django.template.response import TemplateResponse
from django.test import Client
from django.urls import reverse
from rest_framework import status
from typeguard import check_type

from manies_maintenance_manager.jobs import constants
from manies_maintenance_manager.jobs.models import Job
from manies_maintenance_manager.jobs.models import JobCompletionPhoto
from manies_maintenance_manager.jobs.tests.conftest import BASIC_TEST_PDF_FILE
from manies_maintenance_manager.jobs.tests.views.utils import assert_no_form_errors
from manies_maintenance_manager.jobs.tests.views.utils import (
    check_basic_page_html_structure,
)
from manies_maintenance_manager.jobs.tests.views.utils import (
    post_update_request_and_check_errors,
)
from manies_maintenance_manager.jobs.tests.views.utils import verify_email_attachment
from manies_maintenance_manager.jobs.utils import safe_read
from manies_maintenance_manager.jobs.views.job_submit_documentation_view import (
    JobSubmitDocumentationView,
)
from manies_maintenance_manager.users.models import User


def test_anonymous_users_are_redirected_to_login_page(
    client: Client,
    bob_job_with_onsite_work_completed_by_manie: Job,
) -> None:
    """Ensure anonymous users are redirected to the login page.

    Args:
        client (Client): The Django test client.
        bob_job_with_onsite_work_completed_by_manie (Job): Job with Manie completing
            the onsite work.
    """
    job = bob_job_with_onsite_work_completed_by_manie
    response = check_type(
        client.get(
            reverse("jobs:job_submit_documentation", kwargs={"pk": job.pk}),
        ),
        HttpResponseRedirect | TemplateResponse,
    )
    assert response.status_code == status.HTTP_302_FOUND
    assert response.url == f"/accounts/login/?next=/jobs/{job.pk}/submit_documentation/"


def test_view_is_accessible_by_manie_when_onsite_work_done(
    bob_job_with_onsite_work_completed_by_manie: Job,
    manie_user_client: Client,
) -> None:
    """Ensure Manie can access the view after the admin uploaded the POP.

    Args:
        bob_job_with_onsite_work_completed_by_manie (Job): Job with Manie completing
            the onsite work.
        manie_user_client (Client): The Django test client for Manie.
    """
    response = manie_user_client.get(
        reverse(
            "jobs:job_submit_documentation",
            kwargs={"pk": bob_job_with_onsite_work_completed_by_manie.pk},
        ),
    )
    assert response.status_code == status.HTTP_200_OK


def test_view_is_inaccessible_by_agents(
    bob_job_with_onsite_work_completed_by_manie: Job,
    bob_agent_user_client: Client,
) -> None:
    """Ensure agents cannot access the view.

    Args:
        bob_job_with_onsite_work_completed_by_manie (Job): Job with Manie completing
            the onsite work.
        bob_agent_user_client (Client): The Django test client for Bob.
    """
    response = bob_agent_user_client.get(
        reverse(
            "jobs:job_submit_documentation",
            kwargs={"pk": bob_job_with_onsite_work_completed_by_manie.pk},
        ),
    )
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_view_is_accessible_by_admins(
    bob_job_with_onsite_work_completed_by_manie: Job,
    admin_client: Client,
) -> None:
    """Ensure admins can access the view.

    Args:
        bob_job_with_onsite_work_completed_by_manie (Job): Job with Manie completing
            the onsite work.
        admin_client (Client): The Django test client for the admin user.
    """
    response = admin_client.get(
        reverse(
            "jobs:job_submit_documentation",
            kwargs={"pk": bob_job_with_onsite_work_completed_by_manie.pk},
        ),
    )
    assert response.status_code == status.HTTP_200_OK


def test_page_has_basic_correct_structure(
    manie_user_client: Client,
    bob_job_with_onsite_work_completed_by_manie: Job,
) -> None:
    """Test that the job update page has the correct basic structure.

    Args:
        manie_user_client (Client): The Django test client for Manie.
        bob_job_with_onsite_work_completed_by_manie (Job): Job with Manie completing
            the onsite work.
    """
    url = reverse(
        "jobs:job_submit_documentation",
        kwargs={"pk": bob_job_with_onsite_work_completed_by_manie.pk},
    )
    check_basic_page_html_structure(
        client=manie_user_client,
        url=url,
        expected_title="Submit Job Documentation",
        expected_template_name="jobs/job_submit_documentation.html",
        expected_h1_text="Submit Job Documentation",
        expected_func_name="view",
        expected_url_name="job_submit_documentation",
        expected_view_class=JobSubmitDocumentationView,
    )


def submit_job_completion_form_and_assert_no_errors(
    client: Client,
    job: Job,
    test_pdf: SimpleUploadedFile,
) -> TemplateResponse:
    """Submit the job completion form and assert no errors.

    Args:
        client (Client): The Django test client.
        job (Job): The job instance to be updated.
        test_pdf (SimpleUploadedFile): The test PDF file.

    Returns:
        TemplateResponse: The response object after submitting the form.
    """
    with safe_read(test_pdf):
        response = check_type(
            client.post(
                reverse(
                    "jobs:job_submit_documentation",
                    kwargs={"pk": job.pk},
                ),
                data={
                    "invoice": test_pdf,
                    "comments": "This job is now complete.",
                    "form-TOTAL_FORMS": "0",
                    "form-INITIAL_FORMS": "0",
                    "form-MIN_NUM_FORMS": "0",
                    "form-MAX_NUM_FORMS": "1000",
                },
                follow=True,
            ),
            TemplateResponse,
        )

    # Assert the response status code is 200
    assert response.status_code == status.HTTP_200_OK

    # There shouldn't be any form errors:
    assert_no_form_errors(response)
    return response


def test_view_has_invoice_field(
    manie_user_client: Client,
    bob_job_with_onsite_work_completed_by_manie: Job,
    test_pdf: SimpleUploadedFile,
) -> None:
    """Ensure the view has a field for the invoice.

    Args:
        manie_user_client (Client): The Django test client for Manie.
        bob_job_with_onsite_work_completed_by_manie (Job): Job with Manie completing
            the onsite work.
        test_pdf (SimpleUploadedFile): The test PDF file.
    """
    job = bob_job_with_onsite_work_completed_by_manie
    with safe_read(test_pdf):
        response = check_type(
            manie_user_client.post(
                reverse(
                    "jobs:job_submit_documentation",
                    kwargs={"pk": job.pk},
                ),
                data={
                    "invoice": test_pdf,
                    "comments": "This job is now complete.",
                    "form-TOTAL_FORMS": "0",
                    "form-INITIAL_FORMS": "0",
                    "form-MIN_NUM_FORMS": "0",
                    "form-MAX_NUM_FORMS": "1000",
                },
                follow=True,
            ),
            TemplateResponse,
        )

    # Assert the response status code is 200
    assert response.status_code == status.HTTP_200_OK

    # There shouldn't be any form errors:
    assert_no_form_errors(response)

    # Check the redirect chain that leads things up to here:
    expected_chain = [("/jobs/?agent=bob", status.HTTP_302_FOUND)]
    assert response.redirect_chain == expected_chain  # type: ignore[attr-defined]

    # Refresh the Maintenance Job from the database, and then check the updated
    # record:
    job.refresh_from_db()
    name = job.invoice.name  # eg: "invoices/test_me0lP9l.pdf"
    assert name.startswith("invoices/test")
    assert name.endswith(".pdf")


def test_view_has_comments_field(
    manie_user_client: Client,
    bob_job_with_onsite_work_completed_by_manie: Job,
    test_pdf: SimpleUploadedFile,
) -> None:
    """Ensure the view has a field for the comments.

    Args:
        manie_user_client (Client): The Django test client for Manie.
        bob_job_with_onsite_work_completed_by_manie (Job): Job with Manie completing
            the onsite work.
        test_pdf (SimpleUploadedFile): The test PDF file.
    """
    job = bob_job_with_onsite_work_completed_by_manie
    with safe_read(test_pdf):
        response = check_type(
            manie_user_client.post(
                reverse(
                    "jobs:job_submit_documentation",
                    kwargs={"pk": job.pk},
                ),
                data={
                    "comments": "This job is now complete.",
                    "invoice": test_pdf,
                    "form-TOTAL_FORMS": "0",
                    "form-INITIAL_FORMS": "0",
                    "form-MIN_NUM_FORMS": "0",
                    "form-MAX_NUM_FORMS": "1000",
                },
                follow=True,
            ),
            TemplateResponse,
        )

    # Assert the response status code is 200
    assert response.status_code == status.HTTP_200_OK

    # There shouldn't be any form errors:
    assert_no_form_errors(response)

    # Check the redirect chain that leads things up to here:
    expected_chain = [("/jobs/?agent=bob", status.HTTP_302_FOUND)]
    assert response.redirect_chain == expected_chain  # type: ignore[attr-defined]

    # Refresh the Maintenance Job from the database, and then check the updated
    # record:
    job.refresh_from_db()
    assert job.comments == "This job is now complete."


def test_invoice_field_is_required(
    manie_user_client: Client,
    bob_job_with_onsite_work_completed_by_manie: Job,
) -> None:
    """Ensure the invoice field is required.

    Args:
        manie_user_client (Client): The Django test client for Manie.
        bob_job_with_onsite_work_completed_by_manie (Job): Job with Manie completing
            the onsite work.
    """
    job = bob_job_with_onsite_work_completed_by_manie
    response = check_type(
        manie_user_client.post(
            reverse("jobs:job_submit_documentation", kwargs={"pk": job.pk}),
            data={
                "comments": "This job is now complete.",
            },
            follow=True,
        ),
        TemplateResponse,
    )

    # Assert the response status code is 200
    assert response.status_code == status.HTTP_200_OK

    # There should be form errors:
    assert response.context["form"].errors == {"invoice": ["This field is required."]}


def test_comments_field_is_not_required(
    manie_user_client: Client,
    bob_job_with_onsite_work_completed_by_manie: Job,
    test_pdf: SimpleUploadedFile,
) -> None:
    """Ensure the "comments" field is not required.

    Args:
        manie_user_client (Client): The Django test client for Manie.
        bob_job_with_onsite_work_completed_by_manie (Job): Job with Manie completing
            the onsite work.
        test_pdf (SimpleUploadedFile): The test PDF file.
    """
    job = bob_job_with_onsite_work_completed_by_manie
    with safe_read(test_pdf):
        response = check_type(
            manie_user_client.post(
                reverse(
                    "jobs:job_submit_documentation",
                    kwargs={"pk": job.pk},
                ),
                data={
                    "invoice": test_pdf,
                    "form-TOTAL_FORMS": "0",
                    "form-INITIAL_FORMS": "0",
                    "form-MIN_NUM_FORMS": "0",
                    "form-MAX_NUM_FORMS": "1000",
                },
                follow=True,
            ),
            TemplateResponse,
        )

    # Assert the response status code is 200
    assert response.status_code == status.HTTP_200_OK

    # There should be no form errors:
    assert "form" not in response.context


def test_updating_job_changes_status(
    manie_user_client: Client,
    bob_job_with_onsite_work_completed_by_manie: Job,
    test_pdf: SimpleUploadedFile,
) -> None:
    """Ensure updating the job changes the status to complete.

    Args:
        manie_user_client (Client): The Django test client for Manie.
        bob_job_with_onsite_work_completed_by_manie (Job): Job with Manie completing
            the onsite work.
        test_pdf (SimpleUploadedFile): The test PDF file.
    """
    job = bob_job_with_onsite_work_completed_by_manie
    # Check the status before updating
    assert job.status == Job.Status.MANIE_COMPLETED_ONSITE_WORK.value

    # Update the job
    submit_job_completion_form_and_assert_no_errors(
        manie_user_client,
        job,
        test_pdf,
    )

    # Refresh the Maintenance Job from the database, and then check the updated
    # record:
    job.refresh_from_db()

    # Check the job status, after the update
    assert job.status == Job.Status.MANIE_SUBMITTED_DOCUMENTATION.value


def test_should_not_allow_txt_extension_file_for_invoice(
    manie_user_client: Client,
    bob_job_with_onsite_work_completed_by_manie: Job,
) -> None:
    """Test that the view doesn't allow a .txt file extension for the 'invoice' field.

    Args:
        manie_user_client (Client): The Django test client for Manie.
        bob_job_with_onsite_work_completed_by_manie (Job): Job with Manie completing
            the onsite work.
    """
    job = bob_job_with_onsite_work_completed_by_manie
    # New TXT file to upload
    test_txt = SimpleUploadedFile(
        "test.txt",
        BASIC_TEST_PDF_FILE.read_bytes(),
        content_type="application/pdf",
    )
    url = reverse("jobs:job_submit_documentation", kwargs={"pk": job.pk})
    with safe_read(test_txt):
        post_update_request_and_check_errors(
            client=manie_user_client,
            url=url,
            data={
                "invoice": test_txt,
                "comments": "This job is now complete.",
            },
            field_name="invoice",
            expected_error="File extension “txt” is not allowed. "
            "Allowed extensions are: pdf.",
        )


def test_validates_pdf_contents(
    bob_job_with_onsite_work_completed_by_manie: Job,
    manie_user_client: Client,
) -> None:
    """Test that the view should validate the contents of the PDF file.

    Args:
        bob_job_with_onsite_work_completed_by_manie (Job): Job with Manie completing
            the onsite work.
        manie_user_client (Client): The Django test client for Manie.
    """
    job = bob_job_with_onsite_work_completed_by_manie
    # New PDF file to upload
    new_pdf = SimpleUploadedFile(
        "new.pdf",
        b"invalid_file_content",
        content_type="application/pdf",
    )
    url = reverse("jobs:job_submit_documentation", kwargs={"pk": job.pk})
    with safe_read(new_pdf):
        post_update_request_and_check_errors(
            client=manie_user_client,
            url=url,
            data={
                "invoice": new_pdf,
                "comments": "This job is now complete.",
            },
            field_name="invoice",
            expected_error="This is not a valid PDF file",
        )


def test_manie_cannot_access_view_after_completing_the_job(
    bob_job_with_manie_final_documentation: Job,
    manie_user_client: Client,
) -> None:
    """Ensure Manie can't access the update view after completing the job.

    Args:
        bob_job_with_manie_final_documentation (Job): Job with Manies final
            documentationf added to it.
        manie_user_client (Client): The Django test client for Manie.
    """
    job = bob_job_with_manie_final_documentation
    url = reverse("jobs:job_submit_documentation", kwargs={"pk": job.pk})
    response = manie_user_client.get(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_admin_cannot_access_view_after_manie_completes_job(
    bob_job_with_manie_final_documentation: Job,
    admin_client: Client,
) -> None:
    """Ensure admin users can't access the update view after Manie completes the job.

    Args:
        bob_job_with_manie_final_documentation (Job): Job with Manies final
            documentationf added to it.
        admin_client (Client): The Django test client for the admin user.
    """
    job = bob_job_with_manie_final_documentation
    url = reverse("jobs:job_submit_documentation", kwargs={"pk": job.pk})
    response = admin_client.get(url)
    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_redirects_to_job_listing_page_after_saving(
    manie_user_client: Client,
    bob_job_with_onsite_work_completed_by_manie: Job,
    test_pdf: SimpleUploadedFile,
) -> None:
    """Ensure the view redirects to the job listing page after saving the form.

    Args:
        manie_user_client (Client): The Django test client for Manie.
        bob_job_with_onsite_work_completed_by_manie (Job): The job where Manie has
            completed the onsite work.
        test_pdf (SimpleUploadedFile): The test PDF file.
    """
    job = bob_job_with_onsite_work_completed_by_manie
    response = submit_job_completion_form(
        manie_user_client,
        job,
        test_pdf,
        "This job is now complete.",
    )

    # Check the redirect chain that leads things up to here:
    expected_chain = [("/jobs/?agent=bob", status.HTTP_302_FOUND)]
    assert response.redirect_chain == expected_chain  # type: ignore[attr-defined]


def submit_job_completion_form(
    client: Client,
    job: Job,
    test_pdf: SimpleUploadedFile,
    comments: str,
) -> TemplateResponse:
    """Submit the job completion form.

    Args:
        client (Client): The Django test client.
        job (Job): The job instance to be updated.
        test_pdf (SimpleUploadedFile): The test PDF file.
        comments (str): The comments for the job completion.

    Returns:
        TemplateResponse: The response object after submitting the form.
    """
    with safe_read(test_pdf):
        response = check_type(
            client.post(
                reverse(
                    "jobs:job_submit_documentation",
                    kwargs={"pk": job.pk},
                ),
                data={
                    "invoice": test_pdf,
                    "comments": comments,
                    "form-TOTAL_FORMS": "0",
                    "form-INITIAL_FORMS": "0",
                    "form-MIN_NUM_FORMS": "0",
                    "form-MAX_NUM_FORMS": "1000",
                },
                follow=True,
            ),
            TemplateResponse,
        )
    # Assert the response status code is 200
    assert response.status_code == status.HTTP_200_OK
    return response


def test_flash_message_displayed_after_saving(
    manie_user_client: Client,
    bob_job_with_onsite_work_completed_by_manie: Job,
    test_pdf: SimpleUploadedFile,
) -> None:
    """Ensure a flash message is displayed after saving the form.

    Args:
        manie_user_client (Client): The Django test client for Manie.
        bob_job_with_onsite_work_completed_by_manie (Job): The job where Manie has
            completed the onsite work.
        test_pdf (SimpleUploadedFile): The test PDF file.
    """
    job = bob_job_with_onsite_work_completed_by_manie
    response = submit_job_completion_form(
        manie_user_client,
        job,
        test_pdf,
        "This job is now complete.",
    )

    # Check the messages that were displayed:
    messages = list(response.context["messages"])
    assert len(messages) == 1
    assert (
        str(messages[0])
        == "Documentation has been submitted. An email has been sent to bob."
    )


def test_manie_clicking_save_sends_an_email_to_agent(
    manie_user_client: Client,
    bob_job_with_onsite_work_completed_by_manie: Job,
    test_pdf: SimpleUploadedFile,
    manie_user: User,
    bob_agent_user: User,
) -> None:
    """Test that Manie clicking 'Save' sends an email to the agent.

    Args:
        manie_user_client (Client): The Django test client for Manie.
        bob_job_with_onsite_work_completed_by_manie (Job): The job where Manie has
            completed the onsite work.
        test_pdf (SimpleUploadedFile): The test PDF file.
        manie_user (User): The Manie user instance.
        bob_agent_user (User): The Bob agent user instance.
    """
    mail.outbox.clear()

    job = bob_job_with_onsite_work_completed_by_manie
    with safe_read(test_pdf):
        response = check_type(
            manie_user_client.post(
                reverse(
                    "jobs:job_submit_documentation",
                    kwargs={"pk": job.pk},
                ),
                data={
                    "invoice": test_pdf,
                    "comments": "This job is now complete.",
                    "form-TOTAL_FORMS": "0",
                    "form-INITIAL_FORMS": "0",
                    "form-MIN_NUM_FORMS": "0",
                    "form-MAX_NUM_FORMS": "1000",
                },
                follow=True,
            ),
            TemplateResponse,
        )

    # Assert the response status code is 200
    assert response.status_code == status.HTTP_200_OK

    # There should be one email in Django's outbox:
    num_mails_sent = len(mail.outbox)
    assert num_mails_sent == 1

    # Grab the mail:
    email = mail.outbox[0]

    # Check various details of the mail here.

    # Check mail metadata:
    assert email.subject == "Manie uploaded documentation for a job."
    assert bob_agent_user.email in email.to
    assert manie_user.email in email.cc
    assert constants.DEFAULT_FROM_EMAIL in email.from_email

    # Check mail contents:
    assert (
        "Manie uploaded documentation for a job. The invoice and any photos are "
        "attached to this mail.\n\n"
    ) in email.body

    assert "Manies comments on the job: This job is now complete.\n\n" in email.body

    # There should now be exactly one job in the database. Fetch it so that we can
    # use it to check the email body.
    verify_email_attachment(
        email,
        expected_prefix="invoices/test",
        expected_suffix=".pdf",
        expected_content=BASIC_TEST_PDF_FILE.read_bytes(),
        expected_mime_type="application/pdf",
    )


def test_submitting_a_photo_causes_a_photo_to_be_associated_with_the_job(
    manie_user_client: Client,
    bob_job_with_onsite_work_completed_by_manie: Job,
    test_pdf: SimpleUploadedFile,
    test_image: SimpleUploadedFile,
) -> None:
    """Ensure that submitting a photo causes it to be associated with the job.

    Args:
        manie_user_client (Client): The Django test client for Manie.
        bob_job_with_onsite_work_completed_by_manie (Job): The job where Manie has
            completed the onsite work.
        test_pdf (SimpleUploadedFile): The test PDF file.
        test_image (SimpleUploadedFile): The test image file.
    """
    job = bob_job_with_onsite_work_completed_by_manie
    with safe_read(test_pdf), safe_read(test_image):
        response = check_type(
            manie_user_client.post(
                reverse(
                    "jobs:job_submit_documentation",
                    kwargs={"pk": job.pk},
                ),
                data={
                    "invoice": test_pdf,
                    "comments": "This job is now complete.",
                    "form-TOTAL_FORMS": "1",
                    "form-INITIAL_FORMS": "0",
                    "form-MIN_NUM_FORMS": "0",
                    "form-MAX_NUM_FORMS": "1000",
                    "form-0-photo": test_image,
                },
                follow=True,
            ),
            TemplateResponse,
        )

    # Assert the response status code is 200
    assert response.status_code == status.HTTP_200_OK

    # There shouldn't be any form errors:
    assert_no_form_errors(response)

    # Refresh the Maintenance Job from the database, and then check the updated
    # record:
    job.refresh_from_db()

    # Check that the photo has been associated with the job:
    assert job.job_completion_photos.count() == 1
    photo = check_type(
        job.job_completion_photos.first(),
        JobCompletionPhoto,
    )
    with safe_read(test_image):
        assert photo.photo.read() == test_image.read()
    assert photo.job == job
    assert photo.job_id == job.id


def test_submitting_pdf_as_photo_causes_error_to_be_returned(
    manie_user_client: Client,
    bob_job_with_onsite_work_completed_by_manie: Job,
    test_pdf: SimpleUploadedFile,
    test_pdf_2: SimpleUploadedFile,
) -> None:
    """Ensure that submitting a PDF as a photo causes an error to be returned.

    Args:
        manie_user_client (Client): The Django test client for Manie.
        bob_job_with_onsite_work_completed_by_manie (Job): The job where Manie has
            completed the onsite work.
        test_pdf (SimpleUploadedFile): The test PDF file.
        test_pdf_2 (SimpleUploadedFile): The test PDF file.
    """
    job = bob_job_with_onsite_work_completed_by_manie
    with safe_read(test_pdf, test_pdf_2):
        response = check_type(
            manie_user_client.post(
                reverse(
                    "jobs:job_submit_documentation",
                    kwargs={"pk": job.pk},
                ),
                data={
                    "invoice": test_pdf,
                    "comments": "This job is now complete.",
                    "form-TOTAL_FORMS": "1",
                    "form-INITIAL_FORMS": "0",
                    "form-MIN_NUM_FORMS": "0",
                    "form-MAX_NUM_FORMS": "1000",
                    "form-0-photo": test_pdf_2,
                },
                follow=True,
            ),
            TemplateResponse,
        )

        expected_html = (
            "<strong>Upload a valid image. The file you uploaded "
            "was either not an image or a corrupted image.</strong>"
        )

        assert expected_html in response.content.decode()
