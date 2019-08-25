"""Support for Dyson Pure Cool Link devices."""
import logging

import voluptuous as vol

import homeassistant.helpers.config_validation as cv
from homeassistant.const import CONF_DEVICES, CONF_PASSWORD, CONF_TIMEOUT, CONF_USERNAME
from homeassistant.helpers import discovery

_LOGGER = logging.getLogger(__name__)

CONF_LANGUAGE = "language"
CONF_RETRY = "retry"

DEFAULT_TIMEOUT = 5
DEFAULT_RETRY = 10
DYSON_DEVICES = "dyson_devices"
DYSON_PLATFORMS = ["sensor", "fan", "vacuum", "climate", "air_quality"]

DOMAIN = "better_dyson"

CONFIG_SCHEMA = vol.Schema(
    {
        DOMAIN: vol.Schema(
            {
                vol.Required(CONF_USERNAME): cv.string,
                vol.Required(CONF_PASSWORD): cv.string,
                vol.Required(CONF_LANGUAGE): cv.string,
                vol.Optional(CONF_TIMEOUT, default=DEFAULT_TIMEOUT): cv.positive_int,
                vol.Optional(CONF_RETRY, default=DEFAULT_RETRY): cv.positive_int,
                vol.Optional(CONF_DEVICES, default=[]): vol.All(cv.ensure_list, [dict]),
            }
        )
    },
    extra=vol.ALLOW_EXTRA,
)


def setup(hass, config):
    """Set up the Dyson parent component."""
    _LOGGER.info("Creating new Dyson component")

    if DYSON_DEVICES not in hass.data:
        hass.data[DYSON_DEVICES] = []

    from libdyson.dyson import DysonAccount

    dyson_account = DysonAccount(
        config[DOMAIN].get(CONF_USERNAME),
        config[DOMAIN].get(CONF_PASSWORD),
        config[DOMAIN].get(CONF_LANGUAGE),
    )

    logged = dyson_account.login()

    timeout = config[DOMAIN].get(CONF_TIMEOUT)
    retry = config[DOMAIN].get(CONF_RETRY)

    if not logged:
        _LOGGER.error("Not connected to Dyson account. Unable to add devices")
        return False

    _LOGGER.info("Connected to Dyson account")
    dyson_devices = dyson_account.devices()
    if CONF_DEVICES in config[DOMAIN] and config[DOMAIN].get(CONF_DEVICES):
        configured_devices = config[DOMAIN].get(CONF_DEVICES)
        for device in configured_devices:
            dyson_device = next(
                (d for d in dyson_devices if d.serial == device["device_id"]), None
            )
            if dyson_device:
                try:
                    connected = dyson_device.connect(device["device_ip"])
                    if connected:
                        _LOGGER.info("Connected to device %s", dyson_device)
                    else:
                        _LOGGER.warning("Unable to connect to device %s", dyson_device)
                    # Add device in either case (connected or not)
                    hass.data[DYSON_DEVICES].append(dyson_device)
                except OSError as ose:
                    _LOGGER.error(
                        "Unable to connect to device %s: %s",
                        str(dyson_device.network_device),
                        str(ose),
                    )
            else:
                _LOGGER.warning(
                    "Unable to find device %s in Dyson account", device["device_id"]
                )
    else:
        # Not yet reliable
        for device in dyson_devices:
            _LOGGER.info(
                "Trying to connect to device %s with timeout=%i " "and retry=%i",
                device,
                timeout,
                retry,
            )
            connected = device.auto_connect(timeout, retry)
            if connected:
                _LOGGER.info("Connected to device %s", device)
            else:
                _LOGGER.warning("Unable to connect to device %s", device)
            # Add device in either case (connected or not)
            hass.data[DYSON_DEVICES].append(device)

    # Start fan/sensors components
    if hass.data[DYSON_DEVICES]:
        _LOGGER.debug("Starting sensor/fan components")
        for platform in DYSON_PLATFORMS:
            discovery.load_platform(hass, platform, DOMAIN, {}, config)

    return True
