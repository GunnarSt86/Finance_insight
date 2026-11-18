"""Public exceptions raised by :mod:`nordicstats`."""


class NordicStatsError(Exception):
    """Base class for package-specific failures."""


class APIError(NordicStatsError, RuntimeError):
    """A provider returned an unsuccessful HTTP response."""


class ResponseFormatError(NordicStatsError, ValueError):
    """A provider response did not have the expected structure or format."""


class SelectionError(NordicStatsError, ValueError):
    """A table selection is incomplete, invalid, or too large."""
