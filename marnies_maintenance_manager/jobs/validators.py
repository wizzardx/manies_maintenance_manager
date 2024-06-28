"""Custom validators for the "jobs" app."""

from django.core.exceptions import ValidationError
from django.db.models.fields.files import FieldFile
from pypdf import PdfReader
from pypdf.errors import PdfReadError

MAX_PDF_SIZE = 5 * 1024 * 1024  # 5 MB


def validate_pdf_contents(file: FieldFile, max_size: int = MAX_PDF_SIZE) -> None:
    """Validate that the uploaded file is a valid PDF by reading its contents.

    Args:
        file (FieldFile): The file to validate.
        max_size (int): The maximum allowed size of the file in bytes.

    Raises:
        ValidationError: If the file is not a valid PDF.
    """
    if file.tell() != 0:
        msg = "The file has already been read"
        raise ValidationError(msg)

    # Limit the file size:
    if file.size > max_size:
        msg = f"File size should not exceed {max_size / (1024 * 1024)} MB."
        raise ValidationError(msg)

    try:  # pylint: disable=too-many-try-statements
        # Create a PdfReader object, to validate for invalid file contents
        PdfReader(file)
    except PdfReadError as err:
        msg = "This is not a valid PDF file"
        raise ValidationError(msg) from err
    finally:
        file.seek(0)  # Reset the file pointer to the beginning
