"""Test module for merging dotenv files into a single .env file.

This module provides unit tests for the `merge` function, ensuring it combines
multiple dotenv files into one accurately. It handles various cases, from empty
inputs to lists of environment variables.
"""

from pathlib import Path

import pytest

from merge_production_dotenvs_in_dotenv import merge


@pytest.mark.parametrize(
    ("input_contents", "expected_output"),
    [
        ([], ""),
        ([""], "\n"),
        (["JANE=doe"], "JANE=doe\n"),
        (["SEP=true", "AR=ator"], "SEP=true\nAR=ator\n"),
        (["A=0", "B=1", "C=2"], "A=0\nB=1\nC=2\n"),
        (["X=x\n", "Y=y", "Z=z\n"], "X=x\n\nY=y\nZ=z\n\n"),
    ],
)
def test_merge(
    tmp_path: Path,
    input_contents: list[str],
    expected_output: str,
) -> None:
    """Test merging multiple dotenv files into a single .env file.

    Args:
        tmp_path (Path): The temporary directory path used for testing.
        input_contents (list[str]): A list of strings representing the
            contents of individual dotenv files to be merged.
        expected_output (str): The expected content of the output .env file
            after merging.

    Ensures the merge function outputs match the expected combined dotenv file.
    """
    output_file = tmp_path / ".env"

    files_to_merge = []
    for num, input_content in enumerate(input_contents, start=1):
        merge_file = tmp_path / f".service{num}"
        merge_file.write_text(input_content)
        files_to_merge.append(merge_file)

    merge(output_file, files_to_merge)

    assert output_file.read_text() == expected_output
