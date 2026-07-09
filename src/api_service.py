"""
================================================================================
RetailMax Enterprise Data Platform

Module:      api_service.py
Purpose:     Synchronous REST API Client to fetch remote user data.
Author:      Himanshu Sardana
Copyright:   (c) 2026 RetailMax Corp. All rights reserved.
================================================================================
"""

from typing import Any

import requests

from constants import EMPLOYEE_API_URL, HTTP_TIMEOUT_SECONDS
from exceptions import APIPayloadError
from logging_config import get_logger

# Initialize logger
logger = get_logger("api_service")


class APIServiceClient:
    """Consumes REST API endpoints to ingest employee payloads."""

    def __init__(self, endpoint_url: str = EMPLOYEE_API_URL) -> None:
        """Initializes the API client.

        Args:
            endpoint_url: The target REST API endpoint URL.
        """
        self.endpoint_url = endpoint_url
        logger.debug(f"APIServiceClient initialized targeting URL: {self.endpoint_url}")

    def fetch_raw_employees(self) -> list[dict[str, Any]]:
        """Sends an HTTP GET request to retrieve raw user listings.

        If a network error occurs, it falls back to pre-defined mock datasets
        to guarantee resilient operation in offline training environments.

        Returns:
            List[Dict[str, Any]]: A list of raw JSON-like user dictionaries.

        Raises:
            APIPayloadError: If the received response cannot be parsed as JSON.
            APIConnectionError: If connection errors or non-200 statuses occur.
        """
        logger.info(f"Ingesting raw employees via API: {self.endpoint_url}")

        try:
            response = requests.get(self.endpoint_url, timeout=HTTP_TIMEOUT_SECONDS)

            # Raise an HTTPError if the status code was not 200/success
            response.raise_for_status()

            try:
                payload = response.json()
            except ValueError as ve:
                raise APIPayloadError(f"API returned invalid JSON: {ve}")

            if not isinstance(payload, list):
                raise APIPayloadError("Invalid payload schema: Expected a JSON array of users.")

            logger.info(f"Successfully fetched {len(payload)} users from API.")
            return payload

        except requests.exceptions.Timeout:
            logger.warning("API connection timeout. Invoking offline mock dataset fallback.")
            return self._get_offline_mock_data()
        except requests.exceptions.RequestException as re:
            logger.warning(
                f"REST API connection failed ({re}). Invoking offline mock dataset fallback."
            )
            return self._get_offline_mock_data()

    def _get_offline_mock_data(self) -> list[dict[str, Any]]:
        """Provides high-quality offline fallback records matching the JSONPlaceholder schema."""
        logger.debug("Generating offline fallback mock data...")
        return [
            {
                "id": 1,
                "name": "Leanne Graham",
                "username": "Bret",
                "email": "Sincere@april.biz",
                "address": {
                    "street": "Kulas Light",
                    "suite": "Apt. 556",
                    "city": "Gwenborough",
                    "zipcode": "92998-3874",
                    "geo": {"lat": "-37.3159", "lng": "81.1496"},
                },
                "phone": "1-770-736-8031 x56442",
                "website": "hildegard.org",
                "company": {
                    "name": "Romaguera-Crona",
                    "catchPhrase": "Multi-layered client-server neural-net",
                    "bs": "harness real-time e-markets",
                },
            },
            {
                "id": 2,
                "name": "Ervin Howell",
                "username": "Antonette",
                "email": "Shanna@melissa.tv",
                "address": {
                    "street": "Victor Plains",
                    "suite": "Suite 879",
                    "city": "Wisokyburgh",
                    "zipcode": "90566-7771",
                    "geo": {"lat": "-43.9509", "lng": "-34.4618"},
                },
                "phone": "010-692-6593 x09125",
                "website": "anastasia.net",
                "company": {
                    "name": "Deckow-Crist",
                    "catchPhrase": "Proactive didactic contingency",
                    "bs": "synergize scalable supply-chains",
                },
            },
            {
                "id": 3,
                "name": "Clementine Bauch",
                "username": "Samantha",
                "email": "Nathan@yesenia.net",
                "address": {
                    "street": "Douglas Extension",
                    "suite": "Suite 847",
                    "city": "McKenziehaven",
                    "zipcode": "59590-4157",
                    "geo": {"lat": "-68.6102", "lng": "-47.0653"},
                },
                "phone": "1-463-123-4447",
                "website": "ramiro.info",
                "company": {
                    "name": "Romaguera-Jacobson",
                    "catchPhrase": "Face to face bifurcated interface",
                    "bs": "e-enable strategic applications",
                },
            },
            {
                "id": 4,
                "name": "Patricia Lebsack",
                "username": "Karianne",
                "email": "Julianne.OConner@kory.org",
                "address": {
                    "street": "Hoeger Mall",
                    "suite": "Apt. 692",
                    "city": "South Elvis",
                    "zipcode": "53919-4257",
                    "geo": {"lat": "29.4572", "lng": "-164.2990"},
                },
                "phone": "493-170-9623 x156",
                "website": "kale.biz",
                "company": {
                    "name": "Robel-Corkery",
                    "catchPhrase": "Multi-tiered zero tolerance productivity",
                    "bs": "transition cutting-edge web services",
                },
            },
            {
                "id": 5,
                "name": "Chelsey Dietrich",
                "username": "Kamren",
                "email": "Lucio_Hettinger@annie.ca",
                "address": {
                    "street": "Skiles Walks",
                    "suite": "Suite 351",
                    "city": "Roscoeview",
                    "zipcode": "33263",
                    "geo": {"lat": "-31.8129", "lng": "62.5342"},
                },
                "phone": "(254)954-1289",
                "website": "demarco.info",
                "company": {
                    "name": "Keebler LLC",
                    "catchPhrase": "User-centric fault-tolerant solution",
                    "bs": "revolutionize end-to-end systems",
                },
            },
        ]


# ==============================================================================
# INTERVIEW NOTES & API CONCEPTS:
#
# Q1: What is the difference between Synchronous and Asynchronous network calls?
#     - Synchronous: The executing thread blocks and goes idle waiting for the
#       network socket to return data. No other operations occur on that thread
#       during wait times.
#     - Asynchronous: Yields control back to the event loop. While waiting for
#       the socket read to finish, the single thread can execute other routines.
#
# Q2: Why must we always set 'timeout' in HTTP requests?
#     By default, python requests has NO timeout limit. If a remote server hangs
#     or drops packets without closing the socket, the application thread will
#     wait forever (deadlock). Always set a reasonable timeout (e.g. 5-10 seconds).
#
# Q3: What is Connection Pooling?
#     Creating TCP sockets for HTTP handshakes is expensive ($O(N)$ handshakes).
#     Connection pooling keeps HTTP connections open to the target domain, enabling
#     re-use and dramatically increasing speed of subsequent requests.
# ==============================================================================
