"""Config flow for Allsvenskan integration."""
from __future__ import annotations

from homeassistant import config_entries

from .const import DOMAIN


class AllsvenskanConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for Allsvenskan."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle the initial step – no credentials needed for Sofascore."""
        if user_input is not None:
            await self.async_set_unique_id(DOMAIN)
            self._abort_if_unique_id_configured()
            return self.async_create_entry(title="Allsvenskan", data={})

        return self.async_show_form(step_id="user")
