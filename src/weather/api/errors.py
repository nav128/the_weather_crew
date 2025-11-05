class WeatherValidationError(ValueError):
	"""Raised when the incoming request fails validation."""


class WeatherProviderError(RuntimeError):
	"""Raised when the provider (Open-Meteo) fails to fetch data."""


class WeatherRateLimitError(WeatherProviderError):
	"""Raised when the provider indicates rate limiting."""

class FlowError(RuntimeError):
	"""Raised when the flow fails irrecoverably."""
