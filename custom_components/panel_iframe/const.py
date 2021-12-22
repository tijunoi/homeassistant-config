import voluptuous as vol

from homeassistant.const import CONF_ICON, CONF_URL, CONF_ID
from homeassistant.helpers import config_validation as cv

DOMAIN = "panel_iframe"
CONF_TITLE = "title"
CONF_RELATIVE_URL_ERROR_MSG = "Invalid relative URL. Absolute path required."
CONF_RELATIVE_URL_REGEX = r"\A/"
CONF_REQUIRE_ADMIN = "require_admin"
CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: cv.schema_with_slug_keys(
            vol.Schema(
                {
                    # pylint: disable=no-value-for-parameter
                    vol.Optional(CONF_TITLE): cv.string,
                    vol.Optional(CONF_ICON): cv.icon,
                    vol.Optional(CONF_REQUIRE_ADMIN, default=False): cv.boolean,
                    vol.Required(CONF_URL): vol.Any(
                        vol.Match(
                            CONF_RELATIVE_URL_REGEX, msg=CONF_RELATIVE_URL_ERROR_MSG
                        ),
                        vol.Url(),
                    ),
                }
            )
        )
    },
    extra=vol.ALLOW_EXTRA,
)

CONFIG_ENTRY_SCHEMA = vol.Schema({
    # pylint: disable=no-value-for-parameter
    vol.Required(CONF_ID): str,
    vol.Optional(CONF_TITLE): str,
    vol.Optional(CONF_ICON): str,
    vol.Optional(CONF_REQUIRE_ADMIN, default=False): bool,
    vol.Required(CONF_URL): str,
})
