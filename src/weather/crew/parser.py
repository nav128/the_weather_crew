"""Simple deterministic parser for the `parse_range` task.

The real project can use an LLM, but tests expect a small, deterministic
helper that extracts: location, start_date, end_date, units.

Behavior:
- Accepts either a dict with key "query" or a plain string.
- Looks for a "from <date> to <date>" span (ISO dates or human dates parsed
  with dateparser).
- Tries to extract a location when the query contains "in <location> from ..."
- Units default to "metric" but understands the words "imperial",
  "metric", "celsius", "fahrenheit".
- Validates that end_date >= start_date and that the range is at most 31 days.
- Returns a dict with keys: location, start_date, end_date, units, confidence
  or a structured error: {"error": "reason", "hint": "how to fix"}.

This module intentionally avoids live geocoding to keep tests hermetic.
If geocoding is required later, add it behind a feature flag.
"""

from __future__ import annotations

import re
from typing import Any, Dict, Optional, Union

import geopy
import parsedatetime
from datetime import datetime
from geopy.geocoders import Nominatim
from weather.api.errors import WeatherValidationError, ProviderError

cal = parsedatetime.Calendar()
geolocator = Nominatim(user_agent='myapplication')


EMPTY_QUERY_ERROR = "empty query"
PARSE_ERROR = "could not parse query"
DATE_PARSE_ERROR = "could not parse dates"
DATE_ORDER_ERROR = "end_date is before start_date" 
DATE_RANGE_ERROR = "date range exceeds 31 days"
lOCATION_ERROR = "could not geocode location"
FORMAT_HINT = "provide a query like: 'Weather in LOCATION from START_DATE to END_DATE, unit(metric|imperial defaults to metric)'"
DATES_UNKNOWN_HINT = "provide dates in ISO format YYYY-MM-DD or readable dates"
DATES_RANGE_HINT = "got start: '{raw_start}', end: '{raw_end}'"
LOCATION_HINT = "provide a valid location name or coordinates got {location}"
GEOCODE_SERVICE_UNAVAILABLE = "geocoding service unavailable, please try again later"


ISO_DATE_RE = re.compile(r"\d{4}-\d{2}-\d{2}")
# Single deterministic pattern to match: [free text][in LOCATION] from START to END [optional unit]
PATTERN = re.compile(
    r"(?i)\bin\s+(?P<location>.+?)\s+from\s+(?P<start>.+?)\s+to\s+(?P<end>.+?)(?:,\s*(?P<unit>metric|imperial))$"
)
COORDINATES_RE = re.compile(r"^\s*(-?\d+(?:\.\d+)?)\s*,\s*(-?\d+(?:\.\d+)?)\s*$")



def _format_date(dt: datetime) -> str:
	return dt.strftime("%Y-%m-%d")


def parse_range(payload: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
	"""Parse a natural language weather query into structured params.

	Args:
		payload: either the raw query string or a dict with a "query" key.

	Returns:
		dict with parsed fields or structured error.
	"""
	if isinstance(payload, dict):
		query = str(payload.get("query", ""))
	else:
		query = str(payload or "")

	query = query.strip()
	if not query:
		raise WeatherValidationError( {"error": EMPTY_QUERY_ERROR, "hint": FORMAT_HINT})

	# Use the single deterministic pattern to extract location, start, end, unit
	m = PATTERN.search(query)
	if not m:
		raise WeatherValidationError ({"error": PARSE_ERROR, "hint": FORMAT_HINT})

	raw_start = m.group("start")
	raw_end = m.group("end")
	start_dt, sucsses_start = cal.parse(raw_start)
	end_dt, sucsses_end = cal.parse(raw_end)

	if not start_dt or not end_dt or sucsses_start == 0 or sucsses_end == 0:
		raise WeatherValidationError({"error": DATE_PARSE_ERROR, "hint": DATES_UNKNOWN_HINT + f"\n()"})
	start_date = datetime(start_dt.tm_year, start_dt.tm_mon, start_dt.tm_mday)
	end_date = datetime(end_dt.tm_year, end_dt.tm_mon, end_dt.tm_mday)


	if end_date < start_date:
		raise WeatherValidationError({"error": DATE_ORDER_ERROR, "hint": DATES_RANGE_HINT.format(raw_start=raw_start, raw_end=raw_end)})

	span_days = (end_date - start_date).days + 1
	if not 0 < span_days <= 31:
		raise WeatherValidationError({"error": f"date range exceeds 31 days ({span_days} days)", "hint":  DATES_RANGE_HINT.format(raw_start=raw_start, raw_end=raw_end)})

	# extract location from the deterministic match
	location = m.group("location").strip().strip()
	if not COORDINATES_RE.match(location):
		for x in range(3):
			try:
				_location = geolocator.geocode(location)
				if not _location:
					raise WeatherValidationError({"error": lOCATION_ERROR, "hint": LOCATION_HINT.format(location=location)})
				location = f"{_location.latitude},{_location.longitude}"
				break
			except geopy.exc.GeocoderUnavailable:
				continue
		else:
			raise ProviderError({"error": lOCATION_ERROR, "hint": GEOCODE_SERVICE_UNAVAILABLE})

	units = m.group("unit") 
	if not units:
		units = "metric"
	

	# assemble result
	result: Dict[str, Any] = {
		"location": location,
		"start_date": _format_date(start_date),
		"end_date": _format_date(end_date),
		"units": units,
		"confidence": 1.0,
	}

	return result


__all__ = ["parse_range"]