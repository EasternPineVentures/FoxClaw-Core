"""Read-only Kalshi REST transport.

This is the only Phase A network boundary. It sends no credentials, stores no secrets,
and exposes only GET JSON calls for public market-data endpoints.
"""

from __future__ import annotations

import json
import random
import time
import urllib.error
import urllib.parse
import urllib.request
from dataclasses import dataclass
from typing import Any, Mapping

from .environments import KalshiEnvironment, get_environment


class KalshiTransportError(RuntimeError):
    pass


@dataclass(frozen=True)
class KalshiResponseReceipt:
    method: str
    url: str
    status: int
    attempts: int


class KalshiHttpClient:
    def __init__(
        self,
        *,
        environment: str | KalshiEnvironment = "production",
        timeout_s: float = 20.0,
        max_retries: int = 3,
        user_agent: str = "foxclaw-core/kalshi-api-desk",
    ) -> None:
        self.environment = (
            environment if isinstance(environment, KalshiEnvironment) else get_environment(environment)
        )
        self.timeout_s = timeout_s
        self.max_retries = max_retries
        self.user_agent = user_agent
        self.last_receipt: KalshiResponseReceipt | None = None

    def get_json(self, path: str, params: Mapping[str, Any] | None = None) -> Mapping[str, Any]:
        url = self._url(path, params)
        attempts = 0
        while True:
            attempts += 1
            request = urllib.request.Request(
                url,
                method="GET",
                headers={
                    "Accept": "application/json",
                    "User-Agent": self.user_agent,
                },
            )
            try:
                with urllib.request.urlopen(request, timeout=self.timeout_s) as response:
                    status = int(response.status)
                    data = response.read().decode("utf-8")
                    self.last_receipt = KalshiResponseReceipt("GET", url, status, attempts)
                    loaded = json.loads(data)
                    if not isinstance(loaded, Mapping):
                        raise KalshiTransportError(f"expected JSON object from {url}")
                    return loaded
            except urllib.error.HTTPError as exc:
                self.last_receipt = KalshiResponseReceipt("GET", url, exc.code, attempts)
                if exc.code == 429 and attempts <= self.max_retries:
                    time.sleep(_backoff(attempts))
                    continue
                raise KalshiTransportError(f"GET {url} failed with HTTP {exc.code}") from exc
            except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exc:
                if attempts <= self.max_retries:
                    time.sleep(_backoff(attempts))
                    continue
                raise KalshiTransportError(f"GET {url} failed: {exc}") from exc

    def _url(self, path: str, params: Mapping[str, Any] | None) -> str:
        clean_path = "/" + str(path).lstrip("/")
        query_items = {
            key: value
            for key, value in dict(params or {}).items()
            if value is not None and value != ""
        }
        url = self.environment.rest_base_url.rstrip("/") + clean_path
        if query_items:
            url += "?" + urllib.parse.urlencode(query_items, doseq=True)
        return url


def _backoff(attempts: int) -> float:
    base = min(8.0, 0.25 * (2 ** max(0, attempts - 1)))
    return base + random.uniform(0.0, 0.1)
