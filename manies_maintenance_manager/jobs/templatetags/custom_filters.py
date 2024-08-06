"""Custom template filters for the jobs app."""

# pylint: disable=magic-value-comparison

from django import template

register = template.Library()


@register.filter(name="to_char")
def to_char(value: str) -> str:
    """Convert a string to a single character.

    Args:
        value (str): The string to convert.

    Returns:
        str: The single character representation of the string.
    """
    if value == "accepted":
        return "A"
    if value == "rejected":
        return "R"
    return value  # Default case if value is not 'accepted' or 'rejected'
