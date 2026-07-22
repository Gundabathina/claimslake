"""
retry_handler.py

Retry-with-backoff helper for recoverable ingestion failures.

Design decision: only a small, explicit set of exceptions is treated as
retryable (transient I/O problems). Errors that indicate a permanent,
non-recoverable problem - a missing source file, invalid YAML
configuration, or a schema validation failure - are NOT retried, because
retrying them would only waste time and produce identical failures. This
distinction is intentional and is documented in ingestion/README.md.
"""

import time
from typing import Callable, Tuple, Type

from ingestion.src.logger import get_logger

logger = get_logger(__name__)

# Exceptions that represent a transient, potentially self-resolving problem.
RETRYABLE_EXCEPTIONS: Tuple[Type[BaseException], ...] = (
    OSError,       # transient filesystem / IO errors (temporary lock, disk hiccup)
    TimeoutError,
)

# Exceptions that are permanent / non-recoverable and must NOT be retried.
# NOTE: FileNotFoundError is a subclass of OSError, so it is listed here and
# caught first, ensuring a missing file is never retried.
NON_RETRYABLE_EXCEPTIONS: Tuple[Type[BaseException], ...] = (
    FileNotFoundError,  # the file will not appear on retry
    ValueError,         # bad config / bad schema - retrying will not fix bad data
)


class IngestionError(Exception):
    """Raised when ingestion fails after exhausting retries, or fails
    immediately for a non-recoverable reason."""


def run_with_retry(
    func: Callable,
    *args,
    max_retries: int = 3,
    delay_seconds: float = 2.0,
    source_name: str = "",
    **kwargs,
):
    """
    Execute func(*args, **kwargs), retrying on retryable failures.

    - Retries up to max_retries times, pausing delay_seconds between
      attempts (a simple, explainable fixed-delay strategy; production
      systems would typically add exponential backoff and jitter).
    - Non-retryable exceptions are raised immediately on the first attempt.
    - If all retries are exhausted, raises IngestionError wrapping the
      last exception.
    """
    attempt = 1
    while True:
        try:
            return func(*args, **kwargs)
        except NON_RETRYABLE_EXCEPTIONS as exc:
            logger.error(
                "Non-retryable error for source '%s': %s: %s",
                source_name, type(exc).__name__, exc,
            )
            raise IngestionError(str(exc)) from exc
        except RETRYABLE_EXCEPTIONS as exc:
            if attempt >= max_retries:
                logger.error(
                    "Source '%s' failed after %d attempt(s): %s: %s",
                    source_name, attempt, type(exc).__name__, exc,
                )
                raise IngestionError(
                    "Failed after %d attempts: %s" % (attempt, exc)
                ) from exc
            logger.warning(
                "Attempt %d/%d for '%s' failed with %s: %s - retrying in %.1fs",
                attempt, max_retries, source_name, type(exc).__name__, exc,
                delay_seconds,
            )
            time.sleep(delay_seconds)
            attempt += 1
