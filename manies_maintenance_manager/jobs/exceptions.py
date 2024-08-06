"""This module contains custom exceptions for the "jobs" app."""


class ManieUserNotFoundError(Exception):
    """Exception raised when no Manie user is found."""

    def __init__(self, message: str = "No Manie user found") -> None:
        """Initialize the exception with a message.

        Args:
            message (str): A custom message describing the exception.
        """
        super().__init__(message)


class MultipleManieUsersError(Exception):
    """Exception raised when multiple Manie users are found."""

    def __init__(self, message: str = "Multiple Manie users found") -> None:
        """Initialize the exception with a message.

        Args:
            message (str): A custom message describing the exception.
        """
        super().__init__(message)


class NoSystemAdministratorUserError(Exception):
    """Exception raised when no system administrator user is found."""

    def __init__(self, message: str = "No system administrator user found") -> None:
        """Initialize the exception with a message.

        Args:
            message (str): A custom message describing the exception.
        """
        super().__init__(message)


class LogicalError(Exception):
    """Exception raised when a logical error is encountered."""

    def __init__(self, message: str = "A logical error occurred") -> None:
        """Initialize the exception with a message.

        Args:
            message (str): A custom message describing the exception.
        """
        super().__init__(message)


class EnvironmentVariableNotSetError(Exception):
    """Exception raised when an expected environment variable is not set."""

    def __init__(self, message: str = "Environment variable not set") -> None:
        """Initialize the exception with a message.

        Args:
            message (str): A custom message describing the exception.
        """
        super().__init__(message)
