"""
Retry utility with exponential backoff.

Provides decorators and functions to automatically retry failed operations
with configurable backoff strategies.
"""

import time
import logging
from typing import Any, Callable, Optional, TypeVar, Tuple, Type, Union
from functools import wraps

logger = logging.getLogger(__name__)

# Type variable for generic function return types
T = TypeVar('T')

import time
import logging
from typing import Callable, Any, TypeVar, Optional
from functools import wraps


logger = logging.getLogger(__name__)

T = TypeVar('T')


def retry_with_backoff(
    func: Optional[Callable[..., T]] = None,
    *,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: Tuple[Type[Exception], ...] = (Exception,)
) -> Union[Callable[..., T], Callable[[Callable[..., T]], Callable[..., T]]]:
    """
    Decorator that retries a function with exponential backoff.
    
    Can be used with or without parentheses:
        @retry_with_backoff
        def my_func(): ...
        
        @retry_with_backoff(max_attempts=5)
        def my_func(): ...
    
    Args:
        func: The function to retry (auto-filled when used without parentheses)
        max_attempts: Maximum number of retry attempts (default: 3)
        base_delay: Initial delay between retries in seconds (default: 1.0)
        max_delay: Maximum delay between retries in seconds (default: 60.0)
        exceptions: Tuple of exception types to catch and retry (default: all exceptions)
    
    Returns:
        Wrapped function with retry logic or decorator function
        
    Example:
        @retry_with_backoff(max_attempts=5, base_delay=2.0)
        def unreliable_api_call():
            return requests.get("https://api.example.com/data")
    """
    def decorator(f: Callable[..., T]) -> Callable[..., T]:
        @wraps(f)
        def wrapper(*args: Any, **kwargs: Any) -> T:
            last_exception = None
            func_name = getattr(f, '__name__', '<function>')
            
            for attempt in range(1, max_attempts + 1):
                try:
                    logger.debug(f"🔄 Attempt {attempt}/{max_attempts} for {func_name}")
                    result = f(*args, **kwargs)
                    
                    if attempt > 1:
                        logger.info(f"✅ {func_name} succeeded on attempt {attempt}")
                    
                    return result
                    
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_attempts:
                        # Calculate exponential backoff with max_delay cap
                        delay = min(base_delay * (2 ** (attempt - 1)), max_delay)
                        
                        logger.warning(
                            f"⚠️  {func_name} attempt {attempt} failed: {e}. "
                            f"Retrying in {delay:.2f}s..."
                        )
                        
                        time.sleep(delay)
                    else:
                        logger.error(
                            f"❌ {func_name} failed after {max_attempts} attempts. "
                            f"Last error: {e}"
                        )
            
            # If we exhausted all retries, raise the last exception
            if last_exception:
                raise last_exception
            
            # This should never happen, but makes type checker happy
            raise RuntimeError(f"Unexpected state in retry logic for {func_name}")
        
        return wrapper
    
    # Support both @retry_with_backoff and @retry_with_backoff(...)
    if func is not None:
        return decorator(func)
    else:
        return decorator


def execute_with_retry(
    func: Callable[..., T],
    *args: Any,
    max_attempts: int = 3,
    base_delay: float = 1.0,
    max_delay: Optional[float] = None,
    exceptions: tuple = (Exception,),
    **kwargs: Any
) -> T:
    """
    Execute a function with retry logic (functional interface).
    
    This is a functional alternative to the decorator interface.
    
    Args:
        func: Function to execute
        *args: Positional arguments to pass to func
        max_attempts: Maximum number of attempts (default: 3)
        base_delay: Base delay in seconds between retries (default: 1.0)
        max_delay: Maximum delay cap in seconds (default: None)
        exceptions: Tuple of exception types to catch and retry (default: (Exception,))
        **kwargs: Keyword arguments to pass to func
        
    Returns:
        Result of func(*args, **kwargs)
        
    Raises:
        Last exception after max_attempts exceeded
        
    Example:
        >>> result = execute_with_retry(
        >>>     requests.get,
        >>>     "https://api.example.com/data",
        >>>     max_attempts=5,
        >>>     base_delay=0.5,
        >>>     timeout=10
        >>> )
    """
    # Handle None max_delay
    actual_max_delay = max_delay if max_delay is not None else 60.0
    
    decorated = retry_with_backoff(
        func,
        max_attempts=max_attempts,
        base_delay=base_delay,
        max_delay=actual_max_delay,
        exceptions=exceptions
    )
    
    result = decorated(*args, **kwargs)
    return result  # type: ignore[return-value]
