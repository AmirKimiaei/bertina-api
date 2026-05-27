from __future__ import annotations

import asyncio
import hashlib
import logging
import random
import time
from typing import Any, Callable

from curl_cffi import requests as curl_requests
from curl_cffi.requests import AsyncSession
from curl_cffi.requests import RequestsError
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from .constants import DEFAULT_HEADERS, RETRY_STATUS_CODES
from .exceptions import BertinaHTTPError, BertinaRateLimitError

logger = logging.getLogger("bertina")

_IMPERSONATE = "chrome124"

# Type alias: any callable that takes no args and returns seconds to sleep.
SleepStrategy = Callable[[], float]


class DefaultSleepStrategy:
    """Default pacing strategy.

    - Per-request: random 1.50–3.50 s before every real HTTP call.
    - Bulk: random 30.001–300.008 s pause after every 10–70 requests.

    Pass a different callable as ``sleep_strategy`` to any client to replace
    this entirely. Examples::

        # no sleep at all
        BertinaSearch(sleep_strategy=lambda: 0.0)

        # fixed 2 s between requests
        BertinaSearch(sleep_strategy=lambda: 2.0)

        # custom class with state
        class MySleep:
            def __call__(self) -> float:
                return random.uniform(0.5, 1.5)

        BertinaSearch(sleep_strategy=MySleep())
    """

    def __init__(self) -> None:
        self._request_count = 0
        self._next_bulk_threshold = random.randint(10, 70)

    def __call__(self) -> float:
        self._request_count += 1
        per_delay = round(random.uniform(1.50, 3.50), 2)

        if self._request_count >= self._next_bulk_threshold:
            bulk_delay = round(random.uniform(30.001, 300.008), 3)
            logger.debug(
                "bulk sleep after %d requests: %.3fs",
                self._request_count,
                bulk_delay,
            )
            self._request_count = 0
            self._next_bulk_threshold = random.randint(10, 70)
            return round(per_delay + bulk_delay, 3)

        return per_delay


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, BertinaRateLimitError):
        return True
    if isinstance(exc, BertinaHTTPError):
        return exc.status_code in RETRY_STATUS_CODES
    if isinstance(exc, RequestsError):
        return True
    return False


def _check_response(response: Any) -> None:
    if response.status_code == 429:
        raise BertinaRateLimitError()
    if response.status_code >= 400:
        raise BertinaHTTPError(
            f"HTTP {response.status_code} for {response.url}",
            status_code=response.status_code,
        )


class _CacheStore:
    def __init__(self, ttl: int) -> None:
        self._ttl = ttl
        self._store: dict[str, tuple[Any, float]] = {}

    def _key(self, url: str, params: dict) -> str:
        raw = url + str(sorted(params.items()))
        return hashlib.md5(raw.encode()).hexdigest()

    def get(self, url: str, params: dict) -> Any | None:
        key = self._key(url, params)
        entry = self._store.get(key)
        if entry and time.monotonic() - entry[1] < self._ttl:
            return entry[0]
        return None

    def set(self, url: str, params: dict, value: Any) -> None:
        self._store[self._key(url, params)] = (value, time.monotonic())


class BaseClient:
    def __init__(
        self,
        *,
        timeout: float = 15.0,
        headers: dict | None = None,
        proxy: str | None = None,
        debug: bool = False,
        cache_ttl: int = 300,
        max_retries: int = 3,
        sleep_strategy: SleepStrategy | None = None,
    ) -> None:
        self.debug = debug
        self._cache = _CacheStore(cache_ttl)
        merged = {**DEFAULT_HEADERS, **(headers or {})}
        self._client = curl_requests.Session(
            impersonate=_IMPERSONATE,
            headers=merged,
            timeout=timeout,
            proxies={"http://": proxy, "https://": proxy} if proxy else None,
        )
        self._max_retries = max_retries
        self._sleep = sleep_strategy if sleep_strategy is not None else DefaultSleepStrategy()

    def _get(self, url: str, params: dict | None = None) -> str:
        params = params or {}
        cached = self._cache.get(url, params)
        if cached is not None:
            logger.debug("cache hit: %s %s", url, params)
            return cached

        delay = self._sleep()
        logger.debug("sleep %.3fs", delay)
        time.sleep(delay)

        @retry(
            retry=retry_if_exception(_is_retryable),
            stop=stop_after_attempt(self._max_retries),
            wait=wait_exponential(multiplier=1, min=1, max=8),
            reraise=True,
        )
        def _do() -> str:
            logger.debug("GET %s params=%s", url, params)
            response = self._client.get(url, params=params)
            _check_response(response)
            return response.text

        html = _do()
        self._cache.set(url, params, html)
        return html

    def check_url_alive(self, url: str, timeout: float = 5.0) -> bool:
        """Return True if the URL responds with a non-error status code."""
        try:
            response = self._client.head(url, timeout=timeout)
            if response.status_code == 405:
                response = self._client.get(url, timeout=timeout)
            logger.debug("alive check %s -> %s", url, response.status_code)
            return response.status_code < 400
        except Exception as exc:
            logger.debug("alive check failed %s: %s", url, exc)
            return False

    def close(self) -> None:
        self._client.close()

    def __enter__(self) -> "BaseClient":
        return self

    def __exit__(self, *_: Any) -> None:
        self.close()


class AsyncBaseClient:
    def __init__(
        self,
        *,
        timeout: float = 15.0,
        headers: dict | None = None,
        proxy: str | None = None,
        debug: bool = False,
        cache_ttl: int = 300,
        max_retries: int = 3,
        max_concurrent: int = 5,
        sleep_strategy: SleepStrategy | None = None,
    ) -> None:
        self.debug = debug
        self._cache = _CacheStore(cache_ttl)
        merged = {**DEFAULT_HEADERS, **(headers or {})}
        self._client = AsyncSession(
            impersonate=_IMPERSONATE,
            headers=merged,
            timeout=timeout,
            proxies={"http://": proxy, "https://": proxy} if proxy else None,
        )
        self._max_retries = max_retries
        self._semaphore = asyncio.Semaphore(max_concurrent)
        self._sleep = sleep_strategy if sleep_strategy is not None else DefaultSleepStrategy()

    async def _aget(self, url: str, params: dict | None = None) -> str:
        params = params or {}
        cached = self._cache.get(url, params)
        if cached is not None:
            logger.debug("cache hit: %s %s", url, params)
            return cached

        delay = self._sleep()
        logger.debug("sleep %.3fs", delay)
        await asyncio.sleep(delay)

        @retry(
            retry=retry_if_exception(_is_retryable),
            stop=stop_after_attempt(self._max_retries),
            wait=wait_exponential(multiplier=1, min=1, max=8),
            reraise=True,
        )
        async def _do() -> str:
            async with self._semaphore:
                logger.debug("GET %s params=%s", url, params)
                response = await self._client.get(url, params=params)
                _check_response(response)
                return response.text

        html = await _do()
        self._cache.set(url, params, html)
        return html

    async def check_url_alive(self, url: str, timeout: float = 5.0) -> bool:
        """Return True if the URL responds with a non-error status code."""
        try:
            response = await self._client.head(url, timeout=timeout)
            if response.status_code == 405:
                response = await self._client.get(url, timeout=timeout)
            logger.debug("alive check %s -> %s", url, response.status_code)
            return response.status_code < 400
        except Exception as exc:
            logger.debug("alive check failed %s: %s", url, exc)
            return False

    async def aclose(self) -> None:
        await self._client.close()

    async def __aenter__(self) -> "AsyncBaseClient":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.aclose()
