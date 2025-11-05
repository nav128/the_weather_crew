class WeatherValidationError(ValueError):
	"""Raised when the incoming request fails validation."""


class ProviderError(RuntimeError):
	"""Raised when the provider (geopy, Open-Meteo) fails to fetch data."""


class WeatherRateLimitError(ProviderError):
	"""Raised when the provider indicates rate limiting."""

class FlowError(RuntimeError):
	"""Raised when the flow fails irrecoverably."""
