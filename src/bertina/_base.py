from __future__ import annotations

import asyncio
import hashlib
import logging
import time
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
)

from .constants import DEFAULT_HEADERS, RETRY_STATUS_CODES
from .exceptions import BertinaHTTPError, BertinaRateLimitError

logger = logging.getLogger("bertina")


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, BertinaRateLimitError):
        return True
    if isinstance(exc, BertinaHTTPError):
        return exc.status_code in RETRY_STATUS_CODES
    if isinstance(
        exc, (httpx.ConnectError, httpx.TimeoutException, httpx.RemoteProtocolError)
    ):
        return True
    return False


def _check_response(response: httpx.Response) -> None:
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
    ) -> None:
        self.debug = debug
        self._cache = _CacheStore(cache_ttl)
        merged = {**DEFAULT_HEADERS, **(headers or {})}
        self._client = httpx.Client(
            timeout=timeout,
            headers=merged,
            proxy=proxy,
            follow_redirects=True,
        )
        self._max_retries = max_retries

    def _get(self, url: str, params: dict | None = None) -> str:
        params = params or {}
        cached = self._cache.get(url, params)
        if cached is not None:
            logger.debug("cache hit: %s %s", url, params)
            return cached

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
            response = self._client.head(url, timeout=timeout, follow_redirects=True)
            # Some servers block HEAD — fall back to GET with no body
            if response.status_code == 405:
                response = self._client.get(url, timeout=timeout, follow_redirects=True)
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
    ) -> None:
        self.debug = debug
        self._cache = _CacheStore(cache_ttl)
        merged = {**DEFAULT_HEADERS, **(headers or {})}
        self._client = httpx.AsyncClient(
            timeout=timeout,
            headers=merged,
            proxy=proxy,
            follow_redirects=True,
        )
        self._max_retries = max_retries
        self._semaphore = asyncio.Semaphore(max_concurrent)

    async def _aget(self, url: str, params: dict | None = None) -> str:
        params = params or {}
        cached = self._cache.get(url, params)
        if cached is not None:
            logger.debug("cache hit: %s %s", url, params)
            return cached

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
            response = await self._client.head(
                url, timeout=timeout, follow_redirects=True
            )
            if response.status_code == 405:
                response = await self._client.get(
                    url, timeout=timeout, follow_redirects=True
                )
            logger.debug("alive check %s -> %s", url, response.status_code)
            return response.status_code < 400
        except Exception as exc:
            logger.debug("alive check failed %s: %s", url, exc)
            return False

    async def aclose(self) -> None:
        await self._client.aclose()

    async def __aenter__(self) -> "AsyncBaseClient":
        return self

    async def __aexit__(self, *_: Any) -> None:
        await self.aclose()
