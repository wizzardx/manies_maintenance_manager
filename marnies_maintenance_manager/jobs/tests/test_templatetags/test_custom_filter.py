"""Unit tests for the custom filter to_char in the jobs app."""

from marnies_maintenance_manager.jobs.templatetags.custom_filters import to_char


class TestToChar:
    """Tests for the to_char filter."""

    @staticmethod
    def test_accepted_converts_to_a() -> None:
        """Test that 'accepted' converts to 'A'."""
        assert to_char("accepted") == "A"

    @staticmethod
    def test_rejected_converts_to_r() -> None:
        """Test that 'rejected' converts to 'R'."""
        assert to_char("rejected") == "R"

    @staticmethod
    def test_unknown_string_converts_to_itself() -> None:
        """Test that an unknown string converts to itself."""
        assert to_char("unknown") == "unknown"
