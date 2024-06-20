"""Custom validators for the "jobs" app."""

from django.core.exceptions import ValidationError
from django.db.models.fields.files import FieldFile
from pypdf import PdfReader
from pypdf.errors import PdfReadError


def validate_pdf_contents(file: FieldFile) -> None:
    """Validate that the uploaded file is a valid PDF by reading its contents.

    Args:
        file (FieldFile): The file to validate.

    Raises:
        ValidationError: If the file is not a valid PDF.
    """
    if file.tell() != 0:
        msg = "The file has already been read"
        raise ValidationError(msg)
    try:  # pylint: disable=too-many-try-statements
        # Create a PdfReader object, to validate for invalid file contents
        PdfReader(file)
    except PdfReadError as err:
        msg = "This is not a valid PDF file"
        raise ValidationError(msg) from err
    finally:
        file.seek(0)  # Reset the file pointer to the beginning
