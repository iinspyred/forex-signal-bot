import asyncio
from functools import wraps
from typing import Callable


def async_retry(retries: int = 3, delay: float = 1.0):
    def deco(fn: Callable):
        @wraps(fn)
        async def wrapper(*args, **kwargs):
            last_exc = None
            for i in range(retries):
                try:
                    return await fn(*args, **kwargs)
                except Exception as e:
                    last_exc = e
                    await asyncio.sleep(delay * (i + 1))
            raise last_exc

        return wrapper

    return deco
