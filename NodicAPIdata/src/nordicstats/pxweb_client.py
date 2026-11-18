"""Compatibility facade for the original combined client module.

New code should import from :mod:`nordicstats`, :mod:`nordicstats.pxweb_v1`,
or :mod:`nordicstats.pxweb_v2`.
"""

from .analysis import comparable_time_series
from .client_base import require_dimensions as _require_dimensions
from .client_base import selection_values as _selection_values
from .http import create_session as _session
from .http import response_json as _json
from .jsonstat import category_codes as _codes_for_dimension
from .jsonstat import jsonstat_to_frame
from .pxweb_v1 import ICELAND_BASE, IcelandPxWeb
from .pxweb_v2 import SWEDEN_BASE, SwedenPxWeb

__all__ = [
    "ICELAND_BASE",
    "SWEDEN_BASE",
    "IcelandPxWeb",
    "SwedenPxWeb",
    "comparable_time_series",
    "jsonstat_to_frame",
]
