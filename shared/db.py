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

        # Build query params with sslmode=require as default for production safety.
        # Respect explicit user overrides (e.g. sslmode=disable for local dev).
        # Skip SSL for localhost connections (local development)
        query_params = dict(parse_qsl(parsed.query))
        if "sslmode" not in query_params:
            # Don't require SSL for localhost (local development)
            if parsed.hostname in (
                "localhost",
                "127.0.0.1",
                "::1",
            ) or parsed.hostname.startswith("127."):
                query_params["sslmode"] = "disable"
            else:
                query_params["sslmode"] = "require"

        # Skip DNS resolution if already an IPv4 literal
        if parsed.hostname.replace(".", "").isdigit():
            updated = parsed._replace(query=urlencode(query_params))
            return urlunparse(updated)

        infos = socket.getaddrinfo(
            parsed.hostname,
            parsed.port or 5432,
            socket.AF_INET,
        )
        if not infos:
            updated = parsed._replace(query=urlencode(query_params))
            return urlunparse(updated)

        ipv4_addr = str(infos[0][4][0])
        username = parsed.username
        password = parsed.password
        port = parsed.port
        if username:
            if password:
                netloc = f"{username}:{password}@{ipv4_addr}:{port}"
            else:
                netloc = f"{username}@{ipv4_addr}:{port}"
        else:
            netloc = f"{ipv4_addr}:{port}"
        resolved = urlunparse(
            parsed._replace(netloc=netloc, query=urlencode(query_params))
        )
        logger.info(
            "Resolved DB host %s -> %s (IPv4, sslmode=require)",
            parsed.hostname,
            ipv4_addr,
        )
        return resolved
    except Exception as exc:
        logger.warning("IPv4 DNS resolution failed, using original DSN: %s", exc)
        return dsn
