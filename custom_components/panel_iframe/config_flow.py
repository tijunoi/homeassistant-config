from homeassistant import config_entries
from homeassistant.const import CONF_ID
from .const import DOMAIN, CONFIG_ENTRY_SCHEMA, CONF_TITLE, CONF_ICON, CONF_REQUIRE_ADMIN, CONF_URL
from homeassistant.core import callback


@callback
def configured_panels(hass):
    """Return a set of the configured hosts."""
    return set(entry.data[CONF_ID] for entry
               in hass.config_entries.async_entries(DOMAIN))

@config_entries.HANDLERS.register(DOMAIN)
class PanelIframeConfigFlow(config_entries.ConfigFlow):
    # The schema version of the entries that it creates
    # Home Assistant will call your migrate method if the version changes
    # (this is not implemented yet)
    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle form step."""

        if user_input is not None:
        #     if user_input.get(CONF_ID) in configured_panels(self.hass):
        #         return self.async_abort("id_already_exists")

            return await self._create_panel_entry(user_input)

        return self.async_show_form(
            step_id="user", data_schema=CONFIG_ENTRY_SCHEMA
        )

    async def _create_panel_entry(self, user_input):
        panel_id = user_input.get(CONF_ID)
        title = user_input.get(CONF_TITLE)
        icon = user_input.get(CONF_ICON)
        require_admin = user_input.get(CONF_REQUIRE_ADMIN, False)
        url = user_input.get(CONF_URL)

        return self.async_create_entry(
            title=title if title is not None else panel_id,
            data={
                CONF_ID: panel_id,
                CONF_TITLE: title,
                CONF_ICON: icon,
                CONF_REQUIRE_ADMIN: require_admin,
                CONF_URL: url,
            }
        )
