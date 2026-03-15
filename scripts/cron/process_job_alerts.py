#!/usr/bin/env python3
"""Cron script: Process due job alerts (daily/weekly). Run via Render cron."""

from __future__ import annotations

import asyncio
import os
import sys

_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, _root)
sys.path.insert(0, os.path.join(_root, "packages"))

import asyncpg
from backend.domain.job_alerts import AlertFrequency, JobAlertService

from shared.config import get_settings
from shared.logging_config import get_logger

logger = get_logger("cron.job_alerts")


def _get_ssl_config(settings) -> object:
    """Derive SSL configuration for the cron script database pool.

    Uses secure verification when db_ssl_ca_cert_path is set,
    otherwise uses system defaults (requires valid CA-signed cert).
    """
    import ssl

    if getattr(settings, "db_ssl_ca_cert_path", None):
        ctx = ssl.create_default_context(cafile=settings.db_ssl_ca_cert_path)
        return ctx
    # Use system default SSL verification (requires valid CA-signed cert)
    return False


async def main() -> None:
    frequency = os.environ.get("ALERT_FREQUENCY", "daily")
    try:
        freq = AlertFrequency(frequency)
    except ValueError:
        logger.error("Invalid ALERT_FREQUENCY: %s (use daily or weekly)", frequency)
        sys.exit(1)

    settings = get_settings()
    ssl_arg = _get_ssl_config(settings)
    pool = await asyncpg.create_pool(
        settings.database_url,
        min_size=1,
        max_size=2,
        ssl=ssl_arg,
        timeout=30.0,
        command_timeout=60.0,
    )

    try:
        service = JobAlertService(pool)
        result = await service.process_alerts(freq)
        logger.info("Job alerts %s: sent=%d skipped=%d failed=%d", frequency, **result)
    finally:
        await pool.close()


if __name__ == "__main__":
    asyncio.run(main())
