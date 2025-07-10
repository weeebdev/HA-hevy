"""Adds config flow for Hevy."""

from __future__ import annotations

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.helpers import selector
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .api import (
    HevyApiClient,
    HevyApiClientAuthenticationError,
    HevyApiClientCommunicationError,
    HevyApiClientError,
)
from .const import CONF_AUTH_TOKEN, CONF_USERNAME, CONF_NAME, CONF_X_API_KEY, DEFAULT_X_API_KEY, DOMAIN, LOGGER


class HevyFlowHandler(config_entries.ConfigFlow, domain=DOMAIN):
    """Config flow for Hevy."""

    VERSION = 1

    async def async_step_user(
        self,
        user_input: dict | None = None,
    ) -> config_entries.ConfigFlowResult:
        """Handle a flow initialized by the user."""
        _errors = {}
        if user_input is not None:
            # Set default x_api_key if not provided
            if CONF_X_API_KEY not in user_input or not user_input[CONF_X_API_KEY]:
                user_input[CONF_X_API_KEY] = DEFAULT_X_API_KEY
                
            try:
                await self._test_credentials(
                    auth_token=user_input[CONF_AUTH_TOKEN],
                    username=user_input[CONF_USERNAME],
                    x_api_key=user_input[CONF_X_API_KEY],
                )
            except HevyApiClientAuthenticationError as exception:
                LOGGER.warning(exception)
                _errors["base"] = "auth"
            except HevyApiClientCommunicationError as exception:
                LOGGER.error(exception)
                _errors["base"] = "connection"
            except HevyApiClientError as exception:
                LOGGER.exception(exception)
                _errors["base"] = "unknown"
            else:
                await self.async_set_unique_id(f"{user_input[CONF_USERNAME]}_{user_input[CONF_AUTH_TOKEN][:8]}")
                self._abort_if_unique_id_configured()
                return self.async_create_entry(
                    title=f"Hevy - {user_input[CONF_NAME]}",
                    data=user_input,
                )

        return self.async_show_form(
            step_id="user",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_NAME,
                        default=(user_input or {}).get(CONF_NAME, vol.UNDEFINED),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT,
                        ),
                    ),
                    vol.Required(
                        CONF_USERNAME,
                        default=(user_input or {}).get(CONF_USERNAME, vol.UNDEFINED),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT,
                        ),
                    ),
                    vol.Required(
                        CONF_AUTH_TOKEN,
                        default=(user_input or {}).get(CONF_AUTH_TOKEN, vol.UNDEFINED),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.PASSWORD,
                        ),
                    ),
                    vol.Optional(
                        CONF_X_API_KEY,
                        default=(user_input or {}).get(CONF_X_API_KEY, DEFAULT_X_API_KEY),
                    ): selector.TextSelector(
                        selector.TextSelectorConfig(
                            type=selector.TextSelectorType.TEXT,
                        ),
                    ),
                },
            ),
            errors=_errors,
        )

    async def _test_credentials(self, auth_token: str, username: str, x_api_key: str = DEFAULT_X_API_KEY) -> None:
        """Validate authentication credentials."""
        client = HevyApiClient(
            auth_token=auth_token,
            username=username,
            session=async_create_clientsession(self.hass),
            x_api_key=x_api_key,
        )
        await client.async_get_workouts()
