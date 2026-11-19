"""Notebook-friendly access to Nordic official-statistics APIs."""

from .analysis import comparable_time_series
from .catalog import catalog
from .denmark_client import DenmarkStatbank
from .exceptions import APIError, NordicStatsError, ResponseFormatError, SelectionError
from .jsonstat import jsonstat_to_frame
from .pxweb_v1 import IcelandPxWeb
from .pxweb_v2 import SwedenPxWeb
from .sources import SOURCES, Source, client_for, list_sources, sources_dataframe

__all__ = [
    "DenmarkStatbank",
    "APIError",
    "IcelandPxWeb",
    "NordicStatsError",
    "SOURCES",
    "Source",
    "ResponseFormatError",
    "SelectionError",
    "SwedenPxWeb",
    "catalog",
    "client_for",
    "comparable_time_series",
    "jsonstat_to_frame",
    "list_sources",
    "sources_dataframe",
]

__version__ = "0.1.0"
