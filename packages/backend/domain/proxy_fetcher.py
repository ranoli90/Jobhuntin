"""Free proxy fetcher for JobSpy scraping.
Fetches rotating proxies from:
- GimmeProxy API (no signup)
- PubProxy API
- Public proxy lists (e.g. GitHub raw URLs, proxy-list repos)
Supports kill-after-1-use: each fetch returns a fresh proxy.
"""

from __future__ import annotations

import asyncio
import random
from typing import Any

import httpx

from shared.logging_config import get_logger

logger = get_logger("sorce.proxy_fetcher")

# GimmeProxy: returns one proxy per request, supports country, protocol
GIMME_PROXY_URL = "https://gimmeproxy.com/api/getProxy"

# Public proxy list URLs (GitHub raw, etc.) - one proxy per line, format ip:port or protocol://ip:port
PROXY_LIST_URLS = [
    "https://raw.githubusercontent.com/TheSpeedX/PROXY-List/master/http.txt",
    "https://raw.githubusercontent.com/ShiftyTR/Proxy-List/master/http.txt",
]

# Realistic User-Agents for rotation (Chrome, Firefox, Safari)
USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36 Edg/118.0.0.0",
]


def get_random_user_agent() -> str:
    """Return a random User-Agent string for request rotation."""
    return random.choice(USER_AGENTS)


async def fetch_gimmeproxy(
    *,
    country: str | None = "US",
    protocol: str = "http",
    supports_post: bool = True,
    timeout: float = 10.0,
) -> str | None:
    """Fetch a single proxy from GimmeProxy API.
    Returns proxy string like 'ip:port' or None on failure.
    """
    params: dict[str, Any] = {
        "get": "true",
        "supportsHttps": "true",
        "maxCheckPeriod": 3600,
    }
    if country:
        params["country"] = country
    if protocol:
        params["protocol"] = protocol
    if supports_post:
        params["supportsPost"] = "true"

    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.get(GIMME_PROXY_URL, params=params)
            r.raise_for_status()
            data = r.json()
            ip = data.get("ip")
            port = data.get("port")
            if ip and port:
                return f"{ip}:{port}"
    except Exception as e:
        logger.debug("GimmeProxy fetch failed: %s", e)
    return None


async def fetch_pubproxy(timeout: float = 10.0) -> str | None:
    """Fallback: fetch from PubProxy (free, no API key)."""
    url = "https://api.pubproxy.com/api/proxy?limit=1&format=txt"
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.get(url)
            r.raise_for_status()
            line = (r.text or "").strip().split("\n")[0]
            if line and ":" in line:
                return line.strip()
    except Exception as e:
        logger.debug("PubProxy fetch failed: %s", e)
    return None


async def fetch_from_proxy_list(url: str, timeout: float = 10.0) -> str | None:
    """Fetch a random proxy from a public proxy list (e.g. GitHub raw)."""
    try:
        async with httpx.AsyncClient(timeout=timeout) as client:
            r = await client.get(url)
            r.raise_for_status()
            lines = [ln.strip() for ln in (r.text or "").splitlines() if ln.strip() and ":" in ln]
            if lines:
                return random.choice(lines)
    except Exception as e:
        logger.debug("Proxy list %s fetch failed: %s", url[:50], e)
    return None


def normalize_proxy_url(proxy: str) -> str:
    """Ensure proxy has http:// or https:// prefix for httpx."""
    p = proxy.strip()
    if not p:
        return p
    if p.startswith(("http://", "https://", "socks5://")):
        return p
    return f"http://{p}"


async def validate_proxy(proxy: str, timeout: float = 5.0) -> bool:
    """Quick health check: proxy can reach a simple endpoint."""
    url = normalize_proxy_url(proxy)
    if not url:
        return False
    try:
        async with httpx.AsyncClient(proxy=url, timeout=timeout) as client:
            r = await client.get("http://httpbin.org/ip")
            return r.status_code == 200
    except Exception:
        return False


async def fetch_free_proxy(validate: bool = False) -> str | None:
    """Fetch a free proxy; try GimmeProxy, PubProxy, then public proxy lists."""
    for fetcher in [fetch_gimmeproxy, fetch_pubproxy]:
        proxy = await fetcher()
        if proxy and (not validate or await validate_proxy(proxy)):
            return proxy
    for url in PROXY_LIST_URLS:
        proxy = await fetch_from_proxy_list(url)
        if proxy and (not validate or await validate_proxy(proxy)):
            return proxy
    return None
