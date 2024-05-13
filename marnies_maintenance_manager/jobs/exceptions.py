"""This module contains custom exceptions for the jobs app."""


class MarnieUserNotFoundError(Exception):
    """Exception raised when no Marnie user is found."""

    def __init__(self, message: str = "No Marnie user found.") -> None:
        """
        Initialize the exception with a message.

        Args:
            message (str): A custom message describing the exception.
        """
        super().__init__(message)


class MultipleMarnieUsersError(Exception):
    """Exception raised when multiple Marnie users are found."""

    def __init__(self, message: str = "Multiple Marnie users found.") -> None:
        """
        Initialize the exception with a message.

        Args:
            message (str): A custom message describing the exception.
        """
        super().__init__(message)


class NoSystemAdministratorUserError(Exception):
    """Exception raised when no system administrator user is found."""

    def __init__(self, message: str = "No system administrator user found.") -> None:
        """
        Initialize the exception with a message.

        Args:
            message (str): A custom message describing the exception.
        """
        super().__init__(message)


class LogicalError(Exception):
    """Exception raised when a logical error is encountered."""

    def __init__(self, message: str = "A logical error occurred.") -> None:
        """
        Initialize the exception with a message.

        Args:
            message (str): A custom message describing the exception.
        """
        super().__init__(message)
