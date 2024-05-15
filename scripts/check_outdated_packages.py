#!/usr/bin/env python
"""Check for outdated pip packages and optionally ignore specified packages."""

import argparse
import subprocess  # nosec
import sys


def check_outdated_packages(ignore_list):
    """
    Check for outdated pip packages and return an appropriate exit code.

    Args:
        ignore_list (list): List of package names to ignore.

    Returns:
        int: 1 if there are non-ignored outdated packages, 0 otherwise.
    """
    try:
        # Run pip list --outdated and capture the output
        # Using sys.executable for the full path to Python interpreter
        # This subprocess call is considered safe in this context as we're
        # invoking a known and trusted command
        result = subprocess.run(
            [sys.executable, "-m", "pip", "list", "--outdated"],  # nosec  # noqa: S603
            capture_output=True,
            text=True,
            check=True,
        )
    except subprocess.CalledProcessError as e:
        print(f"Error running pip list --outdated: {e}", file=sys.stderr)  # noqa: T201
        return 1

    # Split the output into lines
    lines = result.stdout.strip().split("\n")

    # Check if there are any outdated packages
    outdated_packages = []
    for line in lines[2:]:  # Skip the header lines
        parts = line.split()
        if len(parts) > 0 and parts[0] not in ignore_list:
            outdated_packages.append(parts[0])
        elif len(parts) > 0 and parts[0] in ignore_list:
            print(f"An upgrade for {parts[0]} is being ignored")  # noqa: T201

    # Print remaining packages that need an upgrade
    if outdated_packages:
        print("\nPackages that need an upgrade:")  # noqa: T201
        for pkg in outdated_packages:
            print(pkg)  # noqa: T201
        return 1
    return 0


def main():
    """Parse command-line arguments and check for outdated pip packages."""
    parser = argparse.ArgumentParser(description="Check for outdated pip packages")
    parser.add_argument(
        "--ignore",
        type=str,
        help="Comma-separated list of packages to ignore",
    )
    args = parser.parse_args()

    ignore_list = args.ignore.split(",") if args.ignore else []

    # Exit with the appropriate code
    sys.exit(check_outdated_packages(ignore_list))


if __name__ == "__main__":
    main()
