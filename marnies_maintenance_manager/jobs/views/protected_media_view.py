"""Provide a view to create a new Maintenance Job."""

from pathlib import Path

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import FileResponse
from django.http import Http404
from django.http import HttpRequest
from django.http import HttpResponse
from typeguard import check_type

from marnies_maintenance_manager.users.models import User

# Pattern found in the path to the file indicating directory traversal
TRAVERSE = ".."


@login_required
def protected_media(
    request: HttpRequest,
    path: str,
) -> HttpResponse | FileResponse:
    """Serve protected media files.

    This function now handles requests to /media/ on the server. It checks if the user
    is a superuser, and if so, serves the file requested by the user.

    Otherwise, this project considers the user uploaded-and-specific media files
    to be too sensitive to be freely accessed.

    Args:
        request (HttpRequest): The HTTP request.
        path (str): The path to the file.

    Returns:
        HttpResponse | FileResponse: The HTTP response.

    Raises:
        Http404: If the file is not found.
    """
    # Convert from str to Path
    path2 = Path(path)

    # Absolute paths are not allowed
    if path2.is_absolute():
        return HttpResponse("Access denied", status=403)

    # Directory traversals aren't allowed
    if TRAVERSE in path2.parts:
        return HttpResponse("Access denied", status=403)

    # If access is not allowed, then return early:
    if not _access_allowed(request, path2):
        return HttpResponse("Access denied", status=403)

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
        path (Path): The path to the file.

    Returns:
        bool: True if the user is allowed to access the file, otherwise False.
    """
    # superusers can access everything:
    user = check_type(request.user, User)
    if user.is_superuser:
        return True

    # Marnie can download quote files:
    if user.is_marnie:
        if _is_quote_file(path):
            return True

    # If the logic reaches this point, then access is not allowed:
    return False


def _is_quote_file(path: Path) -> bool:
    """Check if the file is a quote file.

    Args:
        path (Path): The simplified relative path to the file.

    Returns:
        bool: True if the file is a quote file, otherwise False.
    """
    # eg path: Path("quotes/test.pdf")

    # Break into parts:
    dirname, basename = path.parts

    quotes_dirname = "quotes"
    is_quotes_dir = dirname == quotes_dirname
    is_pdf_file = basename.endswith(".pdf")

    return is_quotes_dir and is_pdf_file
