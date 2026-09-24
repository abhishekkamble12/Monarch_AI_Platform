import functools
import time
from utils.logger import log


def llm_retry(max_retries: int = 3, initial_delay: float = 1.0, backoff_factor: float = 2.0):
    """Decorator that retries an LLM or network function with exponential backoff."""
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            delay = initial_delay
            last_exception = None
            for attempt in range(1, max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as exc:
                    last_exception = exc
                    log.warning(
                        "Attempt %d/%d for '%s' failed with error: %s. Retrying in %.2fs...",
                        attempt,
                        max_retries,
                        func.__name__,
                        exc,
                        delay,
                    )
                    if attempt == max_retries:
                        break
                    time.sleep(delay)
                    delay *= backoff_factor
            log.error("All %d retry attempts exhausted for '%s'.", max_retries, func.__name__)
            raise last_exception
        return wrapper
    return decorator
