"""Provide a view to create a new Maintenance Job."""

from pathlib import Path

from django.conf import settings
from django.contrib.auth.decorators import login_required
from django.http import FileResponse
from django.http import Http404
from django.http import HttpRequest
from django.http import HttpResponse


@login_required
def serve_protected_media(
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
    if not request.user.is_superuser:
        # Authorization error
        return HttpResponse(status=403)

    media_root = Path(settings.MEDIA_ROOT)
    full_path = media_root / path

    if not full_path.exists():
        raise Http404

    # Path to the file
    file_path = full_path
    file_name = full_path.name

    # Open the file in binary mode
    file_handle = file_path.open("rb")  # pylint: disable=consider-using-with

    # Create and return the FileResponse object
    return FileResponse(file_handle, as_attachment=True, filename=file_name)
