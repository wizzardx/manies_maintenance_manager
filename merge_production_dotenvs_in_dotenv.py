# ruff: noqa

"""
Merge dotenv files for production into a single .env file.

This module is responsible for combining separate dotenv configuration files
for different parts of the application (like Django and Postgres) into a single
dotenv file that can be used in production environments.
"""

import os
from collections.abc import Sequence
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
PRODUCTION_DOTENVS_DIR = BASE_DIR / ".envs" / ".production"
PRODUCTION_DOTENV_FILES = [
    PRODUCTION_DOTENVS_DIR / ".django",
    PRODUCTION_DOTENVS_DIR / ".postgres",
]
DOTENV_FILE = BASE_DIR / ".env"


def merge(
    output_file: Path,
    files_to_merge: Sequence[Path],
) -> None:
    """
    Merge multiple dotenv files into a single dotenv file.

    Args:
        output_file (Path): The path where the merged dotenv file will be saved.
        files_to_merge (Sequence[Path]): A sequence of paths to dotenv files
            that will be merged.

    The function reads each file in the sequence, concatenates its contents, and
    writes the combined content to the output file. Each file's contents are
    separated by the system's line separator.
    """
    merged_content = ""
    for merge_file in files_to_merge:
        merged_content += merge_file.read_text()
        merged_content += os.linesep
    output_file.write_text(merged_content)


if __name__ == "__main__":
    merge(DOTENV_FILE, PRODUCTION_DOTENV_FILES)
