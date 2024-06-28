"""Custom validators for the "jobs" app."""

import magic
from django.core.exceptions import ValidationError
from django.db.models.fields.files import FieldFile

MAX_PDF_SIZE = 5 * 1024 * 1024  # 5 MB
PDF_MIME_TYPE = "application/pdf"


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

    # Use python-magic to check the file type
    mime = magic.Magic(mime=True)
    # Read the first 1024 bytes to get the MIME type
    file_mime_type = mime.from_buffer(file.read(1024))

    try:  # pylint: disable=too-many-try-statements
        if file_mime_type != PDF_MIME_TYPE:
            msg = "This is not a valid PDF file"
            raise ValidationError(msg)
    finally:
        # Regardless of what happens, reset the file pointer to the beginning
        file.seek(0)
