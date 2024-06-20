"""Fixtures for the "jobs" app tests."""

from collections.abc import Iterator
from pathlib import Path

import pytest
from django.core.files.uploadedfile import SimpleUploadedFile

BASIC_TEST_PDF_FILE = Path(__file__).parent / "views" / "test.pdf"
BASIC_TEST_PDF_FILE_2 = Path(__file__).parent / "views" / "test_2.pdf"


@pytest.fixture(scope="session")
def test_pdf() -> Iterator[SimpleUploadedFile]:
    """Return a test PDF file as a SimpleUploadedFile.

    Yields:
        SimpleUploadedFile: The test PDF file.
    """
    f = SimpleUploadedFile(
        "test.pdf",
        BASIC_TEST_PDF_FILE.read_bytes(),
        content_type="application/pdf",
    )
    yield f
    assert f.tell() == 0, "File position not reset to 0 after use"


@pytest.fixture(scope="session")
def test_pdf_2() -> Iterator[SimpleUploadedFile]:
    """Return a test PDF file as a SimpleUploadedFile.

    Yields:
        SimpleUploadedFile: The test PDF file.
    """
    f = SimpleUploadedFile(
        "test_2.pdf",
        BASIC_TEST_PDF_FILE_2.read_bytes(),
        content_type="application/pdf",
    )
    yield f
    assert f.tell() == 0, "File position not reset to 0 after use"
