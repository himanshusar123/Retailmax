"""
================================================================================
RetailMax Enterprise Data Platform

Module:      async_fetcher.py
Purpose:     Concurrent Asynchronous Fetcher for Auxiliary Corporate Feeds
Author:      Himanshu Sardana
Copyright:   (c) 2026 RetailMax Corp. All rights reserved.
================================================================================
"""

import asyncio
import time
from typing import Any

import httpx

from constants import (
    HTTP_TIMEOUT_SECONDS,
    MOCK_HOLIDAY_URL,
    MOCK_TIME_URL,
    MOCK_WEATHER_URL,
)
from logging_config import get_logger

# Initialize logger
logger = get_logger("async_fetcher")


class AsyncFeedFetcher:
    """Demonstrates non-blocking network calls to aggregate corporate feeds concurrently."""

    def __init__(self) -> None:
        self.timeout = httpx.Timeout(float(HTTP_TIMEOUT_SECONDS))

    async def fetch_feed(self, client: httpx.AsyncClient, name: str, url: str) -> dict[str, Any]:
        """Asynchronously fetches a single HTTP feed.

        Falls back to dummy local JSON on request failures to ensure resilience.
        """
        logger.info(f"Initiating async GET request for '{name}' feed...")
        start = time.perf_counter()

        try:
            response = await client.get(url, timeout=self.timeout)
            response.raise_for_status()
            elapsed = time.perf_counter() - start
            logger.debug(f"Feed '{name}' fetched successfully in {elapsed:.4f}s.")
            return {"feed": name, "status": "success", "data": response.json()}
        except Exception as e:
            logger.warning(
                f"Async fetch failed for '{name}' feed: {e}. Utilizing local mock dictionary fallback."
            )
            # Offline Mock payloads
            mock_data = self._get_mock_feed_data(name)
            return {"feed": name, "status": "fallback", "data": mock_data}

    async def fetch_all_feeds_concurrently(self) -> tuple[list[dict[str, Any]], float]:
        """Fetches Weather, Holiday, and Time feeds concurrently using asyncio.gather.

        Returns:
            Tuple[List[Dict[str, Any]], float]: (feed payloads list, elapsed time in seconds).
        """
        logger.info("Starting concurrent async execution of all data feeds...")
        start_time = time.perf_counter()

        # httpx.AsyncClient manages connection reuse via async sockets
        async with httpx.AsyncClient() as client:
            tasks = [
                self.fetch_feed(client, "Weather", MOCK_WEATHER_URL),
                self.fetch_feed(client, "Holidays", MOCK_HOLIDAY_URL),
                self.fetch_feed(client, "Time", MOCK_TIME_URL),
            ]

            # Executed concurrently in the single-thread event loop
            results = await asyncio.gather(*tasks, return_exceptions=False)

        total_elapsed = time.perf_counter() - start_time
        logger.info(f"Concurrent async aggregation complete. Elapsed: {total_elapsed:.4f} seconds.")
        return results, total_elapsed

    def _get_mock_feed_data(self, name: str) -> dict[str, Any]:
        """Provides offline mock payload structures for the feeds."""
        if name == "Weather":
            return {"temperature": 28.5, "condition": "Sunny", "location": "Bangalore Office"}
        elif name == "Holidays":
            return {"upcoming_holidays_count": 3, "next_holiday": "Republic Day"}
        elif name == "Time":
            return {"timezone": "Asia/Kolkata", "dst": False, "epoch": int(time.time())}
        return {}


# Executable entry point for local validation
if __name__ == "__main__":

    async def main() -> None:
        fetcher = AsyncFeedFetcher()
        results, duration = await fetcher.fetch_all_feeds_concurrently()
        print(f"\nCompleted concurreny fetch in {duration:.4f}s. Results:")
        for r in results:
            print(f"- {r['feed']}: Status={r['status']} Data={r['data']}")

    asyncio.run(main())


# ==============================================================================
# INTERVIEW NOTES & CONCURRENCY CONCEPTS:
#
# Q1: What is the Event Loop in Python Asyncio?
#     The event loop is the engine that drives asynchronous programming. It runs
#     in a single thread, monitoring tasks (coroutines) and waiting for events
#     like socket reads/writes to complete. When a task blocks (awaits), the loop
#     pauses it, shifts execution context, and runs another ready task.
#
# Q2: How does Concurrency differ from Parallelism?
#     - Concurrency: Dealing with multiple tasks at once. Running tasks in overlapping
#       intervals by interleaving them on a single CPU core (like async I/O).
#     - Parallelism: Doing multiple tasks at once. Running tasks simultaneously
#       across multiple physical CPU cores (like multiprocessing).
#
# Q3: Why can't we use 'requests' inside an async coroutine?
#     The 'requests' library is synchronous and blocking. If you call 'requests.get'
#     inside a coroutine, the executing thread will completely halt, blocking the
#     entire event loop. No other task will run until the request finishes, negating
#     all async benefits. We must use an async client library like 'httpx' or 'aiohttp'.
# ==============================================================================
