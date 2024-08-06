"""Permission functions for the "jobs" app.

This module mainly contains the private_media_permissions, and associated
helper functions.

The private_media_permissions function is used with the
private_storage package to check if a user is allowed to access a private
media file.
"""

from pathlib import Path

from django.http import HttpRequest
from private_storage.models import PrivateFile
from typeguard import check_type

from manies_maintenance_manager.jobs.models import Job
from manies_maintenance_manager.jobs.models import JobCompletionPhoto
from manies_maintenance_manager.users.models import User

# Pattern found in the path to the file indicating directory traversal
TRAVERSE = ".."
GET_HTTP_METHOD = "GET"


def _is_quote_file(path: Path) -> bool:
    """Check if the file is a quote file.

    Args:
        path (Path): The simplified relative path to the file.
            - example value: Path("quotes/test.pdf")

    Returns:
        bool: True if the file is a quote file, otherwise False.
    """
    # Break into parts:
    dirname, basename = path.parts

    quotes_dirname = "quotes"
    is_quotes_dir = dirname == quotes_dirname
    is_pdf_file = basename.endswith(".pdf")

    return is_quotes_dir and is_pdf_file


# This constant is used in the _is_file_accessible_by_user function to check if the
# user has access to a JobCompletionPhoto object.
SPECIAL_JOB_COMPLETION_PHOTO_FIELD = "job_completion_photo"


def _get_job_from_completion_photo(path: Path) -> Job | None:
    """Retrieve the job associated with a JobCompletionPhoto.

    Args:
        path (Path): The relative path to the JobCompletionPhoto.

    Returns:
        Job | None: The associated Job if found, otherwise None.
    """
    try:
        completion_photo = JobCompletionPhoto.objects.get(photo=path)
    except (
        JobCompletionPhoto.DoesNotExist,
        JobCompletionPhoto.MultipleObjectsReturned,
    ):
        return None

    return completion_photo.job


def _get_job_from_field(path: Path, field_name: str) -> Job | None:
    """Retrieve the job associated with a specific field.

    Args:
        path (Path): The relative path to the field.
        field_name (str): The field name in the Job model.

    Returns:
        Job | None: The associated Job if found, otherwise None.
    """
    try:
        return Job.objects.get(**{field_name: path})
    except (Job.DoesNotExist, Job.MultipleObjectsReturned):
        return None


def _is_file_accessible_by_user(user: User, path: Path, field_name: str) -> bool:
    """Check if the user has access to a specific file type.

    Args:
        user (User): The user requesting access.
        path (Path): The relative path to the file.
        field_name (str): The field name in the Job model to check (e.g., 'quote',
            'deposit_proof_of_payment', 'invoice').
            - If the value is "job_completion_photo", then this is interpreted instead
              as access to a JobCompletionPhoto object, rather than a Job object.

    Returns:
        bool: True if the user is allowed to access the file, otherwise False.
    """
    # Manie can access all files:
    if user.is_manie:
        return True

    # If the user is an agent, then they can access the file if they created the job
    # that the file is for.
    if user.is_agent:
        # Get the related job from the file path for the specified field:
        if field_name == SPECIAL_JOB_COMPLETION_PHOTO_FIELD:
            job = _get_job_from_completion_photo(path)
        else:
            job = _get_job_from_field(path, field_name)

        # Return True if the agent created the job, otherwise False.
        if job:
            return job.agent == user
        return False

    # Unknown user type, so deny access:
    return False


def _access_allowed_for_quote_file(user: User, path: Path) -> bool:
    return _is_file_accessible_by_user(user, path, "quote")


def _is_deposit_proof_of_payment_file(path: Path) -> bool:
    """Check if the file is a Deposit Proof of Payment file.

    Args:
        path (Path): The simplified relative path to the file.
            - example value: Path("deposit_pops/test.pdf")

    Returns:
        bool: True if the file is a Deposit Proof of Payment file, otherwise False.
    """
    # Break into parts:
    dirname, basename = path.parts
    deposit_proofs_dirname = "deposit_pops"
    is_deposit_proofs_dir = dirname == deposit_proofs_dirname
    is_pdf_file = basename.endswith(".pdf")

    return is_deposit_proofs_dir and is_pdf_file


def _access_allowed_for_deposit_proof_of_payment_file(user: User, path: Path) -> bool:
    return _is_file_accessible_by_user(user, path, "deposit_proof_of_payment")


def _is_invoice_file(path: Path) -> bool:
    """Check if the file is an Invoice file.

    Args:
        path (Path): The simplified relative path to the file.
            - example value: Path("invoices/test.pdf")

    Returns:
        bool: True if the file is an Invoice file, otherwise False.
    """
    # Break into parts:
    dirname, basename = path.parts
    invoices_dirname = "invoices"
    is_invoices_dir = dirname == invoices_dirname
    is_pdf_file = basename.endswith(".pdf")

    return is_invoices_dir and is_pdf_file


def _access_allowed_for_invoice_file(user: User, path: Path) -> bool:
    return _is_file_accessible_by_user(user, path, "invoice")


def _is_final_payment_pop_file(path: Path) -> bool:
    """Check if the file is a Final Payment Proof of Payment file.

    Args:
        path (Path): The simplified relative path to the file.
            - example value: Path("final_payment_pops/test.pdf")

    Returns:
        bool: True if the file is a Final Payment Proof of Payment file, otherwise
            False.
    """
    # Break into parts:
    dirname, basename = path.parts
    final_payment_proofs_dirname = "final_payment_pops"
    is_final_payment_proofs_dir = dirname == final_payment_proofs_dirname
    is_pdf_file = basename.endswith(".pdf")

    return is_final_payment_proofs_dir and is_pdf_file


def _has_common_image_filename_extension(
    basename: str,
) -> bool:
    """Check if the filename has a common image filename extension.

    Args:
        basename (str): The basename of the file.

    Returns:
        bool: True if the filename has a common image filename extension, otherwise
              False.
    """
    return basename.lower().endswith((".jpg", ".jpeg", ".png", ".gif", ".bmp"))


def _is_job_completion_photo(path: Path) -> bool:
    """Check if the file is a Job Completion Photo image.

    Args:
        path (Path): The simplified relative path to the file.
            - example value: Path("final_payment_pops/test.pdf")

    Returns:
        bool: True if the file is a Job Completion Photo, otherwise False.
    """
    # Break into parts:
    dirname, basename = path.parts
    job_completion_photos_dirname = "completion_photos"
    is_final_payment_proofs_dir = dirname == job_completion_photos_dirname
    is_image_file = _has_common_image_filename_extension(basename)
    return is_final_payment_proofs_dir and is_image_file


def _access_allowed_for_final_payment_pop_file(user: User, path: Path) -> bool:
    return _is_file_accessible_by_user(user, path, "final_payment_pop")


def _access_allowed_for_job_completion_photo_file(user: User, path: Path) -> bool:
    return _is_file_accessible_by_user(user, path, "job_completion_photo")


def _access_allowed(request: HttpRequest, path: Path) -> bool:
    """Check if the user is allowed to access the file.

    Args:
        request (HttpRequest): The HTTP request.
        path (Path): The (relative) path to the file.
            - eg: Path("quotes/test.pdf")
            - This is the same value that's seen in the FileField.name field.

    Returns:
        bool: True if the user is allowed to access the file, otherwise False.
    """
    user = check_type(request.user, User)

    # Admins can access everything:
    if user.is_superuser:
        return True

    # Define a mapping of file type check functions to their respective access functions
    # fmt: off
    file_type_access_check_map = {
        _is_quote_file: _access_allowed_for_quote_file,
        _is_deposit_proof_of_payment_file:
            _access_allowed_for_deposit_proof_of_payment_file,
        _is_invoice_file: _access_allowed_for_invoice_file,
        _is_final_payment_pop_file: _access_allowed_for_final_payment_pop_file,
        _is_job_completion_photo: _access_allowed_for_job_completion_photo_file,
    }
    # fmt: on

    for file_type_check, access_function in file_type_access_check_map.items():
        if file_type_check(path):
            return access_function(user, path)

    # If the logic reaches this point, then access is not allowed:
    return False


def _access_denied() -> bool:
    return False


def private_media_permissions(private_file: PrivateFile) -> bool:
    """Check if the user is allowed to access the private file.

    This permission function is used with the `private_storage` package to check if a
    user is allowed to access a private media file.

    Args:
        private_file (PrivateFile): The private file object.

    Returns:
        bool: True if the user is allowed to access the file, otherwise False.
    """
    request = private_file.request
    path = private_file.relative_name

    if not request.user.is_authenticated:
        return _access_denied()

    # Convert from str to Path
    path2 = Path(path)

    # Absolute paths are not allowed
    if path2.is_absolute():
        return _access_denied()

    # Directory traversals aren't allowed
    if TRAVERSE in path2.parts:
        return _access_denied()

    # If access is not allowed, then return early:
    if not _access_allowed(request, path2):
        return _access_denied()

    # All checks passed, so the permission checks passed
    return True
