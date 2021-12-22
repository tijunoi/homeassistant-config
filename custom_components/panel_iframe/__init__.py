"""Register an iFrame front end panel."""
from homeassistant.const import CONF_ICON, CONF_URL, CONF_ID
from .const import CONF_TITLE, CONF_REQUIRE_ADMIN, DOMAIN

async def async_setup(hass, config):
    """Set up the iFrame frontend panels."""
    if config.get(DOMAIN) is not None:
        for url_path, info in config[DOMAIN].items():
            hass.components.frontend.async_register_built_in_panel(
                "iframe",
                info.get(CONF_TITLE),
                info.get(CONF_ICON),
                url_path,
                {"url": info[CONF_URL]},
                require_admin=info[CONF_REQUIRE_ADMIN],
            )

    return True


async def async_setup_entry(hass, entry):
    """Set up an iFrame panel from a config entry"""
    hass.components.frontend.async_register_built_in_panel(
        "iframe",
        entry.data.get(CONF_TITLE),
        entry.data.get(CONF_ICON),
        entry.data[CONF_ID],
        {"url": entry.data[CONF_URL]},
        require_admin=entry.data[CONF_REQUIRE_ADMIN]
    )
    return True


async def async_unload_entry(hass, entry):
    """Unload and remove panel"""
    hass.components.frontend.async_remove_panel(entry.data[CONF_ID])
    return True
