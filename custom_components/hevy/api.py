"""Hevy API Client."""

from __future__ import annotations

import socket
from typing import Any

import aiohttp
import async_timeout

from .const import BASE_URL, DEFAULT_WORKOUTS_COUNT


class HevyApiClientError(Exception):
    """Exception to indicate a general API error."""


class HevyApiClientCommunicationError(
    HevyApiClientError,
):
    """Exception to indicate a communication error."""


class HevyApiClientAuthenticationError(
    HevyApiClientError,
):
    """Exception to indicate an authentication error."""


def _verify_response_or_raise(response: aiohttp.ClientResponse) -> None:
    """Verify that the response is valid."""
    if response.status in (401, 403):
        msg = "Invalid authentication token"
        raise HevyApiClientAuthenticationError(
            msg,
        )
    response.raise_for_status()


class HevyApiClient:
    """Hevy API Client."""

    def __init__(
        self,
        auth_token: str,
        username: str,
        session: aiohttp.ClientSession,
        x_api_key: str = "shelobs_hevy_web",
    ) -> None:
        """Initialize Hevy API Client.
        
        Args:
            auth_token: The authentication token for the Hevy API.
            username: The Hevy username.
            session: The aiohttp ClientSession.
            x_api_key: The x-api-key value to use for API requests.
        """
        self._auth_token = auth_token
        self._username = username
        self._session = session
        self._headers = {
            "Accept": "application/json, text/plain, */*",
            "Hevy-Platform": "web",
            "auth-token": auth_token,
            "x-api-key": x_api_key,
        }

    async def async_get_workout_count(self) -> dict[str, Any]:
        """Get workout count.

        Returns:
            The JSON response from the API containing the workout count.
        """
        return await self._api_wrapper(
            method="get",
            url=f"{BASE_URL}/workout_count",
            params={},
        )

    async def async_get_workouts(
        self, limit: int = DEFAULT_WORKOUTS_COUNT, offset: int = 0
    ) -> dict[str, Any]:
        """Get workouts.

        Args:
            limit: The number of workouts to get.
            offset: The offset to start from.

        Returns:
            The JSON response from the API.
        """
        return await self._api_wrapper(
            method="get",
            url=f"{BASE_URL}/user_workouts_paged",
            params={"username": self._username, "limit": limit, "offset": offset},
        )

    async def _api_wrapper(
        self,
        method: str,
        url: str,
        params: dict | None = None,
        data: dict | None = None,
    ) -> Any:
        """Get information from the API."""
        try:
            async with async_timeout.timeout(10):
                response = await self._session.request(
                    method=method,
                    url=url,
                    headers=self._headers,
                    params=params,
                    json=data,
                )
                _verify_response_or_raise(response)
                return await response.json()

        except TimeoutError as exception:
            msg = f"Timeout error fetching information - {exception}"
            raise HevyApiClientCommunicationError(
                msg,
            ) from exception
        except (aiohttp.ClientError, socket.gaierror) as exception:
            msg = f"Error fetching information - {exception}"
            raise HevyApiClientCommunicationError(
                msg,
            ) from exception
        except Exception as exception:  # pylint: disable=broad-except
            msg = f"Something really wrong happened! - {exception}"
            raise HevyApiClientError(
                msg,
            ) from exception
