"""View for completing a Maintenance Job."""

from typing import TYPE_CHECKING
from typing import Any
from typing import cast

from django.contrib import messages
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.mixins import UserPassesTestMixin
from django.http import HttpResponse
from django.views.generic import UpdateView
from typeguard import check_type

from manies_maintenance_manager.jobs.forms import JobCompletionPhotoFormSet
from manies_maintenance_manager.jobs.forms import JobSubmitDocumentationForm
from manies_maintenance_manager.jobs.models import Job
from manies_maintenance_manager.jobs.models import JobCompletionPhoto
from manies_maintenance_manager.jobs.views.mixins import JobSuccessUrlMixin
from manies_maintenance_manager.jobs.views.utils import AttachmentType
from manies_maintenance_manager.jobs.views.utils import prepare_and_send_email
from manies_maintenance_manager.users.models import User

if TYPE_CHECKING:  # pylint: disable=consider-ternary-expression
    TypedUpdateView = UpdateView[  # pragma: no cover
        Job,
        JobSubmitDocumentationForm,
    ]
else:
    TypedUpdateView = UpdateView


class JobSubmitDocumentationView(
    LoginRequiredMixin,
    UserPassesTestMixin,
    JobSuccessUrlMixin,
    TypedUpdateView,
):
    """Complete a Maintenance Job."""

    model = Job
    form_class = JobSubmitDocumentationForm  # fields = [""invoice", "comments"]
    template_name = "jobs/job_submit_documentation.html"

    def test_func(self) -> bool:
        """Check if the user can access this view.

        Returns:
            bool: True if the user can access this view, False otherwise.
        """
        # Only Manie and Admin users can reach this view, and only if the onsite
        # work has just been completed by Manie.
        user = check_type(self.request.user, User)

        job = self.get_object()
        return (job.status == Job.Status.MANIE_COMPLETED_ONSITE_WORK.value) and (
            user.is_superuser or user.is_manie
        )

    def form_valid(self, form: JobSubmitDocumentationForm) -> HttpResponse:
        """Save the form.

        Args:
            form (JobSubmitDocumentationForm): The form instance.

        Returns:
            HttpResponse: The HTTP response.
        """
        # This method is called when valid form data has been POSTed. It's responsible
        # for doing things before and after performing the actual save of the form.
        # (to the database).
        context = self.get_context_data()
        photo_formset = context["photo_formset"]

        if not (form.is_valid() and photo_formset.is_valid()):
            form2 = cast(dict[str, Any], form)
            return self.render_to_response(self.get_context_data(form=form2))

        # Associate each photo with the job before saving the formset
        job = form.save(commit=False)
        for photo_form in photo_formset:
            photo_form.instance.job = job
        photo_formset.save()

        # Update the Job's state to "manie submitted his documentation"
        job.status = Job.Status.MANIE_SUBMITTED_DOCUMENTATION.value
        job.save()

        # Call validations/etc on parent classes
        # noinspection PyUnresolvedReferences
        response = super().form_valid(form)

        # Email the agent.
        email_subject = "Manie uploaded documentation for a job."

        email_body = (
            "Manie uploaded documentation for a job. "
            "The invoice and any photos are attached to this mail.\n\n"
        )

        if job.comments:
            email_body += f"Manies comments on the job: {job.comments}\n\n"

        email_body += (
            "Details of your original request:\n\n"
            "-----\n\n"
            f"Subject: New maintenance request by {job.agent.username}\n\n"
        )

        request = self.request
        prepare_and_send_email(
            email_subject,
            email_body,
            job,
            request,
            AttachmentType.INVOICE_AND_PHOTOS,
        )

        # Send a success flash message to the user:
        agent = job.agent
        msg = (
            "Documentation has been submitted. "
            f"An email has been sent to {agent.username}."
        )
        messages.success(self.request, msg)

        # Return response back to the caller:
        return response

    def get_context_data(self, **kwargs: dict[str, Any]) -> dict[str, Any]:
        """Get the context data for this view.

        Args:
            **kwargs (dict[str, Any]): The keyword arguments

        Returns:
            dict[str, Any]: The context data.
        """
        # noinspection PyUnresolvedReferences
        context = super().get_context_data(**kwargs)
        if self.request.POST:
            context["photo_formset"] = JobCompletionPhotoFormSet(
                self.request.POST,
                self.request.FILES,
                queryset=JobCompletionPhoto.objects.filter(job=self.object),
            )
        else:
            context["photo_formset"] = JobCompletionPhotoFormSet(
                queryset=JobCompletionPhoto.objects.filter(job=self.object),
            )
        return context
