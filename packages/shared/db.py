"""Shared database utilities."""

from __future__ import annotations

import socket
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse

from shared.logging_config import get_logger

logger = get_logger("sorce.shared.db")


def resolve_dsn_ipv4(dsn: str) -> str:
    """Resolve the hostname in a PostgreSQL DSN to an IPv4 address and enforce SSL.

    Render containers often lack IPv6 connectivity, causing
    ``[Errno 101] Network is unreachable`` when asyncpg tries to connect
    to a hostname that resolves to an AAAA (IPv6) record first.  This
    helper forces AF_INET (IPv4) resolution and rewrites the DSN so
    asyncpg connects directly to the IPv4 address.

    It also ensures ``sslmode=require`` is present to keep connections
    compatible with managed Postgres providers (e.g., Render).

    If resolution fails for any reason the original *dsn* is returned
    unchanged.
    """
    try:
        parsed = urlparse(dsn)
        if not parsed.hostname:
            return dsn

        # Build query params with enforced sslmode=require when missing.
        query_params = dict(parse_qsl(parsed.query))
        if query_params.get("sslmode", "").lower() != "require":
            query_params["sslmode"] = "require"

        # Skip DNS resolution if already an IPv4 literal
        if parsed.hostname.replace(".", "").isdigit():
            updated = parsed._replace(query=urlencode(query_params))
            return urlunparse(updated)

        infos = socket.getaddrinfo(
            parsed.hostname, parsed.port or 5432, socket.AF_INET,
        )
        if not infos:
            updated = parsed._replace(query=urlencode(query_params))
            return urlunparse(updated)

        ipv4_addr = infos[0][4][0]
        netloc = parsed.netloc.replace(parsed.hostname, ipv4_addr)
        resolved = urlunparse(parsed._replace(netloc=netloc, query=urlencode(query_params)))
        logger.info("Resolved DB host %s -> %s (IPv4, sslmode=require)", parsed.hostname, ipv4_addr)
        return resolved
    except Exception as exc:
        logger.warning("IPv4 DNS resolution failed, using original DSN: %s", exc)
        return dsn
