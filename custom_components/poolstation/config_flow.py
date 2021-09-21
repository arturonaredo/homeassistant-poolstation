"""Config flow for PoolStation integration."""
from __future__ import annotations

from asyncio import TimeoutError
import logging
from typing import Any

from aiohttp import ClientResponseError, DummyCookieJar
from pypoolstation import Account, AuthenticationException
import voluptuous as vol

from homeassistant import config_entries
from homeassistant.const import CONF_EMAIL, CONF_PASSWORD
from homeassistant.data_entry_flow import FlowResult
from homeassistant.helpers.aiohttp_client import async_create_clientsession

from .const import DOMAIN, TOKEN

_LOGGER = logging.getLogger(__name__)

DATA_SCHEMA = vol.Schema(
    {
        vol.Required(CONF_EMAIL): str,
        vol.Required(CONF_PASSWORD): str,
    }
)


class ConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Poolstation."""

    VERSION = 1

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Handle the initial step."""
        errors: dict[str, str]

        if user_input is None:
            return self.async_show_form(step_id="user", data_schema=DATA_SCHEMA)
        errors = {}
        session = async_create_clientsession(self.hass, cookie_jar=DummyCookieJar)
        account = Account(
            session, username=user_input[CONF_EMAIL], password=user_input[CONF_PASSWORD]
        )

        try:
            token = await account.login()
        except (TimeoutError, ClientResponseError):
            errors["base"] = "cannot_connect"
        except AuthenticationException:
            errors["base"] = "invalid_auth"
        except Exception:  # pylint: disable=broad-except
            _LOGGER.exception("Unexpected exception")
            errors["base"] = "unknown"
        else:
            await self.async_set_unique_id(user_input[CONF_EMAIL].lower())
            self._abort_if_unique_id_configured()
            return self.async_create_entry(
                title=user_input[CONF_EMAIL].lower(),
                data={TOKEN: token},
            )

        return self.async_show_form(
            step_id="user", data_schema=DATA_SCHEMA, errors=errors
        )