# #!/usr/bin/env python3

"caching context for weather data"

from datetime import datetime


class WeatherCache:
    def __init__(self):
        self.cache = {}

    def get(self, key):
        return self.cache.get(key, [None, None])[1]

    def set(self, key, value):
        now = datetime.now()
        
        
        if key in self.cache:
            # update timestamp
            self.cache[key][0] = now
        else:
            self.cache[key] = [now, value]
        self._cleanup(now)

    def _cleanup(self, now: datetime):
        # filter all entries older than 10 minutes
        seconds_to_keep = 10 * 60
        self.cache = {k: v for k, v in self.cache.items() if ((now - v[0]).total_seconds()) <= seconds_to_keep}

weather_cache = WeatherCache()
# def weather_cache(func):
#     cache = WeatherCache()
#     def wrapper(*args, **kwargs):
#         key = str((args, frozenset(kwargs.items())))
#         cached_value = cache.get(key)
#         if cached_value is not None:
#             return cached_value
#         result = func(*args, **kwargs)
#         cache.set(key, result)
#         return result
#     return wrapper
