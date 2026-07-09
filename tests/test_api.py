"""
================================================================================
RetailMax Enterprise Data Platform

Module:      tests/test_api.py
Purpose:     Unit tests for APIServiceClient utilizing unittest.mock.
Author:      Himanshu Sardana
Copyright:   (c) 2026 RetailMax Corp. All rights reserved.
================================================================================
"""

from unittest.mock import MagicMock, patch

import pytest
import requests

from api_service import APIServiceClient
from exceptions import APIPayloadError


def test_fetch_employees_success() -> None:
    """Verifies that a successful HTTP response deserializes into JSON list rows."""
    client = APIServiceClient()
    mock_payload = [
        {
            "id": 1,
            "name": "Test User",
            "username": "testuser",
            "email": "test@retailmax.com",
            "address": {},
            "company": {},
        }
    ]

    # Patch requests.get
    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_payload
        mock_get.return_value = mock_response

        records = client.fetch_raw_employees()
        assert len(records) == 1
        assert records[0]["name"] == "Test User"
        mock_get.assert_called_once()


def test_fetch_employees_invalid_json_raises_payload_error() -> None:
    """Verifies that corrupted non-JSON payloads raise APIPayloadError."""
    client = APIServiceClient()

    with patch("requests.get") as mock_get:
        mock_response = MagicMock()
        mock_response.status_code = 200
        # Raise JSON decoding error
        mock_response.json.side_effect = ValueError("Invalid JSON token")
        mock_get.return_value = mock_response

        with pytest.raises(APIPayloadError):
            client.fetch_raw_employees()


def test_fetch_employees_offline_fallback() -> None:
    """Checks that network timeouts trigger fallback to pre-defined offline mock datasets."""
    client = APIServiceClient()

    with patch("requests.get") as mock_get:
        # Simulate connection timeout exception
        mock_get.side_effect = requests.exceptions.Timeout("Connection timed out")

        # In offline environments, client must NOT crash, but fallback to offline dicts
        records = client.fetch_raw_employees()
        assert len(records) > 0
        # First mock record is Leanne Graham
        assert records[0]["name"] == "Leanne Graham"
