from time import time
import logging
import os



def _resolve_level() -> int:
    level_str = os.environ.get("LOG_LEVEL")
    if not level_str:
        return logging.INFO
    try:
        return getattr(logging, level_str.upper())
    except Exception:
        return logging.INFO


logging_level = _resolve_level()
logging.basicConfig(level=logging_level, format="%(levelname)s %(message)s")

logger = logging.getLogger("weather_ai")


class LogDuration():
    start: float
    def __init__(self, activity:str, depth=0):
        self.activity = activity
        self.tabs="\t" * depth
    def __enter__(self):
        self.start = time()
        logger.log(logging.INFO, f"{self.tabs}Started {self.activity}" )

    def __exit__(self, *args, **kwargs):
        logger.log(logging.INFO, f"{self.tabs}Finished {self.activity} in {int(time() - self.start) *1000} ms")
        
    