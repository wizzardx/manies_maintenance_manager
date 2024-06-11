"""Provide a view to create a new Maintenance Job."""

from pathlib import Path

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import FileResponse
from django.http import Http404
from django.http import HttpRequest
from django.http import HttpResponse
from rest_framework import status
from typeguard import check_type

from marnies_maintenance_manager.jobs.models import Job
from marnies_maintenance_manager.users.models import User

# Pattern found in the path to the file indicating directory traversal
TRAVERSE = ".."
GET_HTTP_METHOD = "GET"


@login_required
def protected_media(
    request: HttpRequest,
    path: str,
) -> HttpResponse | FileResponse:
    """Serve protected media files.

    This function now handles requests to /media/ on the server. It checks if the user
    is a superuser, and if so, serves the file requested by the user.

    Otherwise, we carefully check permissions to make sure that only the right users
    can access the right files.

    Args:
        request (HttpRequest): The HTTP request.
        path (str): The path to the file.

    Returns:
        HttpResponse | FileResponse: The HTTP response.

    Raises:
        Http404: If the file is not found.
    """
    # None-GET methods not allowed.
    if request.method != GET_HTTP_METHOD:
        return HttpResponse(status=status.HTTP_405_METHOD_NOT_ALLOWED)

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

    media_root = Path(settings.MEDIA_ROOT)
    full_path = media_root / path2

    # Quit if the file does not exist:
    if not full_path.exists():
        raise Http404

    # Path to the file
    file_path = full_path
    file_name = full_path.name

    # Open the file in binary mode
    file_handle = file_path.open("rb")  # pylint: disable=consider-using-with

    # Create and return the FileResponse object
    return FileResponse(file_handle, as_attachment=True, filename=file_name)


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
    # Admins can access everything:
    user = check_type(request.user, User)
    if user.is_superuser:
        return True

    # Is it a quote file?
    if _is_quote_file(path):
        # Yes. Check if the user is allowed to access the quote file:
        return _access_allowed_for_quote_file(user, path)

    # If the logic reaches this point, then access is not allowed:
    return False


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


def _access_denied() -> HttpResponse:
    return HttpResponse(status=status.HTTP_403_FORBIDDEN)


def _access_allowed_for_quote_file(user: User, path: Path) -> bool:
    # We don't need to check for admin user, they were already given access earlier.

    # Marnie can access all quote files:
    if user.is_marnie:
        return True

    # If the user is an agent, then they can access the quote file if they created the
    # job that the quote is for.
    if user.is_agent:
        # Get the related job from the file path for the 'quote' field:
        try:
            job = Job.objects.get(quote=path)
        except Job.DoesNotExist:
            # If a matching job is not found, then we treat this as a permission denied.
            # This is a security measure to prevent agents from accessing quote files.
            # The file itself might actually exist on the server, but we don't want to
            # reveal its existence to agents unnecessarily.
            return False
        except Job.MultipleObjectsReturned:
            # If multiple matching jobs are found, then we treat this as a permission
            # denied.
            return False

        # Return True if the agent created the job, otherwise False.
        return job.agent == user

    # Not Marnie or an agent, so access is not allowed:
    return False
