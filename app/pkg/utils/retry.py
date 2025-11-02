"""Retry and backoff utilities."""

import asyncio
import functools
import random
import time
from typing import Any, Callable, Optional, Type, Union, List, Awaitable
from dataclasses import dataclass
from enum import Enum

from app.pkg.logger import logger

__all__ = [
    "BackoffStrategy",
    "RetryConfig",
    "RetryError",
    "retry_async",
    "retry_sync",
    "exponential_backoff",
    "linear_backoff",
    "constant_backoff",
    "jitter_backoff"
]


class BackoffStrategy(str, Enum):
    """Backoff strategies for retry."""
    CONSTANT = "constant"
    LINEAR = "linear"
    EXPONENTIAL = "exponential"
    EXPONENTIAL_JITTER = "exponential_jitter"


@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_attempts: int = 3
    base_delay: float = 1.0
    max_delay: float = 60.0
    backoff_strategy: BackoffStrategy = BackoffStrategy.EXPONENTIAL
    jitter: bool = True
    retriable_exceptions: tuple = (Exception,)
    non_retriable_exceptions: tuple = ()


class RetryError(Exception):
    """Exception raised when all retry attempts are exhausted."""

    def __init__(self, message: str, last_exception: Exception, attempt_count: int):
        super().__init__(message)
        self.last_exception = last_exception
        self.attempt_count = attempt_count


def exponential_backoff(attempt: int, base_delay: float, max_delay: float, jitter: bool = True) -> float:
    """Calculate exponential backoff delay."""
    delay = base_delay * (2 ** (attempt - 1))
    delay = min(delay, max_delay)

    if jitter:
        delay = delay * (0.5 + random.random() * 0.5)

    return delay


def linear_backoff(attempt: int, base_delay: float, max_delay: float, jitter: bool = True) -> float:
    """Calculate linear backoff delay."""
    delay = base_delay * attempt
    delay = min(delay, max_delay)

    if jitter:
        delay = delay * (0.8 + random.random() * 0.4)

    return delay


def constant_backoff(attempt: int, base_delay: float, max_delay: float, jitter: bool = True) -> float:
    """Calculate constant backoff delay."""
    delay = base_delay

    if jitter:
        delay = delay * (0.8 + random.random() * 0.4)

    return min(delay, max_delay)


def jitter_backoff(attempt: int, base_delay: float, max_delay: float, jitter: bool = True) -> float:
    """Calculate full jitter backoff delay."""
    max_backoff = min(base_delay * (2 ** (attempt - 1)), max_delay)
    return random.uniform(0, max_backoff)


def _calculate_delay(config: RetryConfig, attempt: int) -> float:
    """Calculate delay based on backoff strategy."""
    if config.backoff_strategy == BackoffStrategy.CONSTANT:
        return constant_backoff(attempt, config.base_delay, config.max_delay, config.jitter)
    elif config.backoff_strategy == BackoffStrategy.LINEAR:
        return linear_backoff(attempt, config.base_delay, config.max_delay, config.jitter)
    elif config.backoff_strategy == BackoffStrategy.EXPONENTIAL:
        return exponential_backoff(attempt, config.base_delay, config.max_delay, config.jitter)
    elif config.backoff_strategy == BackoffStrategy.EXPONENTIAL_JITTER:
        return jitter_backoff(attempt, config.base_delay, config.max_delay, config.jitter)
    else:
        return exponential_backoff(attempt, config.base_delay, config.max_delay, config.jitter)


def _should_retry(exception: Exception, config: RetryConfig) -> bool:
    """Determine if an exception should trigger a retry."""
    # Check non-retriable exceptions first
    if config.non_retriable_exceptions and isinstance(exception, config.non_retriable_exceptions):
        return False

    # Check retriable exceptions
    return isinstance(exception, config.retriable_exceptions)


def retry_async(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_strategy: BackoffStrategy = BackoffStrategy.EXPONENTIAL,
    jitter: bool = True,
    retriable_exceptions: tuple = (Exception,),
    non_retriable_exceptions: tuple = (),
    on_retry: Optional[Callable[[Exception, int], Awaitable[None]]] = None
):
    """
    Async retry decorator with configurable backoff strategies.

    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        backoff_strategy: Backoff strategy to use
        jitter: Whether to add jitter to delays
        retriable_exceptions: Exceptions that should trigger retry
        non_retriable_exceptions: Exceptions that should not trigger retry
        on_retry: Optional callback function called on each retry
    """
    config = RetryConfig(
        max_attempts=max_attempts,
        base_delay=base_delay,
        max_delay=max_delay,
        backoff_strategy=backoff_strategy,
        jitter=jitter,
        retriable_exceptions=retriable_exceptions,
        non_retriable_exceptions=non_retriable_exceptions
    )

    def decorator(func: Callable[..., Awaitable[Any]]) -> Callable[..., Awaitable[Any]]:
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(1, config.max_attempts + 1):
                try:
                    result = await func(*args, **kwargs)

                    # Log successful retry if this wasn't the first attempt
                    if attempt > 1:
                        logger.info(
                            "Function %s succeeded on attempt %d/%d",
                            func.__name__, attempt, config.max_attempts
                        )

                    return result

                except Exception as e:
                    last_exception = e

                    # Check if we should retry this exception
                    if not _should_retry(e, config):
                        logger.error(
                            "Function %s failed with non-retriable exception: %s",
                            func.__name__, str(e)
                        )
                        raise

                    # Don't retry if this was the last attempt
                    if attempt == config.max_attempts:
                        break

                    # Calculate delay for next attempt
                    delay = _calculate_delay(config, attempt)

                    logger.warning(
                        "Function %s failed on attempt %d/%d: %s. Retrying in %.2f seconds",
                        func.__name__, attempt, config.max_attempts, str(e), delay
                    )

                    # Call retry callback if provided
                    if on_retry:
                        try:
                            await on_retry(e, attempt)
                        except Exception as callback_error:
                            logger.error("Retry callback failed: %s", str(callback_error))

                    # Wait before next attempt
                    await asyncio.sleep(delay)

            # All attempts exhausted
            error_message = (
                f"Function {func.__name__} failed after {config.max_attempts} attempts. "
                f"Last error: {str(last_exception)}"
            )

            logger.error(error_message)
            raise RetryError(error_message, last_exception, config.max_attempts)

        return wrapper
    return decorator


def retry_sync(
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    backoff_strategy: BackoffStrategy = BackoffStrategy.EXPONENTIAL,
    jitter: bool = True,
    retriable_exceptions: tuple = (Exception,),
    non_retriable_exceptions: tuple = (),
    on_retry: Optional[Callable[[Exception, int], None]] = None
):
    """
    Sync retry decorator with configurable backoff strategies.

    Args:
        max_attempts: Maximum number of retry attempts
        base_delay: Base delay in seconds
        max_delay: Maximum delay in seconds
        backoff_strategy: Backoff strategy to use
        jitter: Whether to add jitter to delays
        retriable_exceptions: Exceptions that should trigger retry
        non_retriable_exceptions: Exceptions that should not trigger retry
        on_retry: Optional callback function called on each retry
    """
    config = RetryConfig(
        max_attempts=max_attempts,
        base_delay=base_delay,
        max_delay=max_delay,
        backoff_strategy=backoff_strategy,
        jitter=jitter,
        retriable_exceptions=retriable_exceptions,
        non_retriable_exceptions=non_retriable_exceptions
    )

    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args, **kwargs) -> Any:
            last_exception = None

            for attempt in range(1, config.max_attempts + 1):
                try:
                    result = func(*args, **kwargs)

                    # Log successful retry if this wasn't the first attempt
                    if attempt > 1:
                        logger.info(
                            "Function %s succeeded on attempt %d/%d",
                            func.__name__, attempt, config.max_attempts
                        )

                    return result

                except Exception as e:
                    last_exception = e

                    # Check if we should retry this exception
                    if not _should_retry(e, config):
                        logger.error(
                            "Function %s failed with non-retriable exception: %s",
                            func.__name__, str(e)
                        )
                        raise

                    # Don't retry if this was the last attempt
                    if attempt == config.max_attempts:
                        break

                    # Calculate delay for next attempt
                    delay = _calculate_delay(config, attempt)

                    logger.warning(
                        "Function %s failed on attempt %d/%d: %s. Retrying in %.2f seconds",
                        func.__name__, attempt, config.max_attempts, str(e), delay
                    )

                    # Call retry callback if provided
                    if on_retry:
                        try:
                            on_retry(e, attempt)
                        except Exception as callback_error:
                            logger.error("Retry callback failed: %s", str(callback_error))

                    # Wait before next attempt
                    time.sleep(delay)

            # All attempts exhausted
            error_message = (
                f"Function {func.__name__} failed after {config.max_attempts} attempts. "
                f"Last error: {str(last_exception)}"
            )

            logger.error(error_message)
            raise RetryError(error_message, last_exception, config.max_attempts)

        return wrapper
    return decorator


class AsyncRetryContext:
    """Context manager for retry operations."""

    def __init__(self, config: RetryConfig):
        self.config = config
        self.attempt = 0
        self.last_exception = None

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            return False

        self.attempt += 1
        self.last_exception = exc_val

        # Check if we should retry
        if not _should_retry(exc_val, self.config):
            return False

        # Check if we've exhausted attempts
        if self.attempt >= self.config.max_attempts:
            return False

        # Calculate and apply delay
        delay = _calculate_delay(self.config, self.attempt)
        logger.warning(
            "Operation failed on attempt %d/%d: %s. Retrying in %.2f seconds",
            self.attempt, self.config.max_attempts, str(exc_val), delay
        )

        await asyncio.sleep(delay)
        return True  # Suppress the exception to retry