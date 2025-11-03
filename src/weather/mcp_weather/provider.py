"""Open-Meteo provider
----------------------
Minimal client for retrieving weather data from the Open-Meteo API.

This module provides a small, dependency-free provider class intended to be
used by the MCP tool. It expects the request to follow the strict JSON
schema used by the project (see `weather.crew.mcp_client.validate_request`).

Design notes:
- This implementation expects `location` to be a latitude,longitude string
  (for example: "31.7683,35.2137"). If a non-numeric location is provided
  the provider will raise a ValueError. Adding geocoding is left for later.
- Uses the stdlib `urllib` so no extra dependencies are required.
"""

from __future__ import annotations

import json
from typing import Dict, Any, Tuple
from urllib.parse import urlencode
from urllib.request import urlopen, Request
from urllib.error import URLError, HTTPError
from datetime import date, timedelta


def _parse_latlon(location: str) -> Tuple[float, float]:
    """Parse a "lat,lon" pair from the `location` string.

    Raises ValueError if the location cannot be parsed as two floats.
    """
    parts = [p.strip() for p in location.split(",")]
    if len(parts) != 2:
        raise ValueError("location must be 'lat,lon' (two comma-separated floats)")
    try:
        lat = float(parts[0])
        lon = float(parts[1])
    except ValueError as exc:
        raise ValueError("location must contain numeric latitude and longitude") from exc
    return lat, lon


class OpenMeteoProvider:
    """Simple Open-Meteo client.

    Usage:
        prov = OpenMeteoProvider()
        out = prov.fetch(request_dict)

    The returned structure is a dict with the parsed JSON from Open-Meteo
    under the `data` key and some small metadata under `meta`.
    """

    BASE_FORECAST = "https://api.open-meteo.com/v1/forecast"
    BASE_ARCHIVE = "https://archive-api.open-meteo.com/v1/archive"

    def __init__(self, timeout: float = 10.0) -> None:
        self.timeout = timeout

    def _build_url(self, lat: float, lon: float, start: str, end: str, units: str = 'metric', past: bool = True) -> str:
        # choose temperature unit for the API
        params = {
        "latitude": lat,
        "longitude": lon,
        "start_date": start,
        "end_date": end,
        "daily": "temperature_2m_max,temperature_2m_min,precipitation_sum,windspeed_10m_max,weathercode",
        "timezone": "auto",
        "temperature_unit": "celsius" if units == "metric" else "fahrenheit",
        "windspeed_unit": "kmh" if units == "metric" else "mph",
        "precipitation_unit": "mm" if units == "metric" else "inch"
    }
        if units == "imperial":
            # Open-Meteo supports temperature_unit=fahrenheit
            params["temperature_unit"] = "fahrenheit"

        return f"{self.BASE_ARCHIVE if past else self.BASE_FORECAST}?{urlencode(params)}"
    
    def _build_urls(self, lat: float, lon: float, start: date, end: date, units: str = 'metric') -> list[str]:
        # if all of the date are in the past
        """Build 1 OR 2 URLs for the given date range.

        Splits Tthe range into historical and forecast if needed.
        """
        urls = []
        if end < date.today():
            # all dates in the past
            url = self._build_url(lat, lon, start.isoformat(), end.isoformat(), units, past=True)
            urls.append(url)
        elif start >= date.today():
            # all dates in the future
            url = self._build_url(lat, lon, start.isoformat(), end.isoformat(), units, past=False)
            urls.append(url)
        else:
            # split into two requests
            url1 = self._build_url(lat, lon, start.isoformat(), (date.today() - timedelta(days=1)).isoformat(), units, past=True)
            url2 = self._build_url(lat, lon, date.today().isoformat(), end.isoformat(), units, past=False)
            urls.extend([url1, url2])
        return urls
    
    def _fetch(self, *params) -> Dict[str, Any]:
        urls = self._build_urls(*params)
        days = []
        for url in urls:
            req = Request(url, headers={"User-Agent": "weather-provider/0.1"})

            try:
                
                with urlopen(req, timeout=self.timeout) as resp:
                    body = resp.read()
                    encoding = resp.headers.get_content_charset() or "utf-8"
                    text = body.decode(encoding)
                    data = json.loads(text)
            except HTTPError as exc:
                raise RuntimeError(f"Open-Meteo HTTP error: {exc.code} {exc.reason} \nfor {url}") from exc
            except URLError as exc:
                raise RuntimeError(f"Open-Meteo request failed: {exc.reason} \nfor {url}") from exc
            except json.JSONDecodeError as exc:
                raise RuntimeError(f"Open-Meteo returned invalid JSON: {exc.msg} \nfor {url}") from exc
            for i, date in enumerate(data["daily"]["time"]):
                days.append({
                    "date": date,
                    "tmin": data["daily"]["temperature_2m_min"][i],
                    "tmax": data["daily"]["temperature_2m_max"][i],
                    "precip_mm": data["daily"]["precipitation_sum"][i],
                    "wind_max_kph": data["daily"]["windspeed_10m_max"][i],
                    "code": data["daily"]["weathercode"][i]
                })
        return days
    
    def fetch(self, request: Dict[str, Any]) -> Dict[str, Any]:
        """Fetch weather data for a validated request.

        The `request` MUST conform to the schema validated by
        `weather.crew.mcp_client.validate_request` (it will be validated here
        as well). The function returns a dictionary with keys:
        - `meta`: echo of input metadata
        - `data`: raw JSON returned by Open-Meteo

        Raises ValueError for invalid input and RuntimeError for network/API
        issues.
        """
        # validate strict schema (raises ValueError on failure)
        # validate_request(request)

        # parse lat/lon from the location string
        lat, lon = _parse_latlon(request["location"])
        
       
        # build URL and call Open-Meteo
        days = self._fetch(
            lat,
            lon,
            date.fromisoformat(request["start_date"]),
            date.fromisoformat(request["end_date"]),
            request.get("units", "metric")
        )

        return {
            "daily": days,
            "source": "open-meteo"
        }
        


__all__ = ["OpenMeteoProvider", "validate_request", "_parse_latlon"]

