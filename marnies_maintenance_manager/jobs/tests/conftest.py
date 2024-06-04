"""Fixtures for the "jobs" app tests."""

from pathlib import Path

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

BASIC_TEST_PDF_FILE = Path(__file__).parent / "views" / "test.pdf"
BASIC_TEST_PDF_FILE_2 = Path(__file__).parent / "views" / "test_2.pdf"


@pytest.fixture()
def test_pdf() -> SimpleUploadedFile:
    """Return a test PDF file as a SimpleUploadedFile.

    Returns:
        SimpleUploadedFile: The test PDF file.
    """
    return SimpleUploadedFile(
        "test.pdf",
        BASIC_TEST_PDF_FILE.read_bytes(),
        content_type="application/pdf",
    )


@pytest.fixture()
def test_pdf_2() -> SimpleUploadedFile:
    """Return a test PDF file as a SimpleUploadedFile.

    Returns:
        SimpleUploadedFile: The test PDF file.
    """
    return SimpleUploadedFile(
        "test_2.pdf",
        BASIC_TEST_PDF_FILE_2.read_bytes(),
        content_type="application/pdf",
    )
