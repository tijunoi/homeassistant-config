"""Support for Dyson Pure Hot+Cool link fan."""
import logging

from libdyson.const import HeatMode, HeatState, FocusMode, HeatTarget
from libdyson.dyson_pure_state import DysonPureHotCoolState
from libdyson.dyson_pure_hotcool_link import DysonPureHotCoolLink

from homeassistant.components.climate import ClimateDevice
from homeassistant.components.climate.const import (
    CURRENT_HVAC_COOL,
    CURRENT_HVAC_HEAT,
    CURRENT_HVAC_IDLE,
    HVAC_MODE_HEAT,
    HVAC_MODE_OFF,
    SUPPORT_FAN_MODE,
    FAN_FOCUS,
    FAN_DIFFUSE,
    SUPPORT_TARGET_TEMPERATURE,
)
from homeassistant.const import ATTR_TEMPERATURE, TEMP_CELSIUS, ATTR_ENTITY_ID
from homeassistant.helpers.config_validation import (
    ENTITY_SERVICE_SCHEMA,
)

from . import DYSON_DEVICES
DYSON_DOMAIN = "dyson"

_LOGGER = logging.getLogger(__name__)

SUPPORT_FAN = [FAN_FOCUS, FAN_DIFFUSE]
SUPPORT_HVAG = [HVAC_MODE_OFF, HVAC_MODE_HEAT]
SUPPORT_FLAGS = SUPPORT_TARGET_TEMPERATURE | SUPPORT_FAN_MODE

DYSON_CLIMATE_DEVICES = "dyson_climate_devices"

SERVICE_RECONNECT = 'reconnect'

DYSON_RECONNECT_SCHEMA = ENTITY_SERVICE_SCHEMA


def setup_platform(hass, config, add_devices, discovery_info=None):

    from libdyson.dyson_pure_hotcool_link import DysonPureHotCoolLink

    """Set up the Dyson fan components."""
    if discovery_info is None:
        return

    has_hot_devices = False
    device_serials = [device.serial for device in hass.data[DYSON_CLIMATE_DEVICES]]
    if DYSON_CLIMATE_DEVICES not in hass.data:
        hass.data[DYSON_CLIMATE_DEVICES] = []
        for device in hass.data[DYSON_DEVICES]:
            if device.serial not in device_serials:
                if isinstance(device, DysonPureHotCoolLink):
                    has_hot_devices = True
                    dyson_entity = DysonPureHotCoolLinkDevice(device)
                    hass.data[DYSON_CLIMATE_DEVICES].append(dyson_entity)

    # Get Dyson Devices from parent component.
    add_devices(hass.data[DYSON_CLIMATE_DEVICES])

    def service_handle(service):
        entity_id = service.data[ATTR_ENTITY_ID]
        climate_device = next(
            (climate for climate in hass.data[DYSON_CLIMATE_DEVICES] if climate.entity_id == entity_id)
        )
        if climate_device is None:
            _LOGGER.warning("Unable to find Dyson heat fan device %s", str(entity_id))
            return
        if service.service == SERVICE_RECONNECT:
            climate_device.reconnect()

    if has_hot_devices:
        hass.services.register(
            DYSON_DOMAIN,
            SERVICE_RECONNECT,
            service_handle,
            schema=DYSON_RECONNECT_SCHEMA,
        )


class DysonPureHotCoolLinkDevice(ClimateDevice):
    """Representation of a Dyson climate fan."""

    def __init__(self, device):
        """Initialize the fan."""
        self._device = device
        self._current_temp = None

    async def async_added_to_hass(self):
        """Call when entity is added to hass."""
        self.hass.async_add_job(self._device.add_message_listener, self.on_message)
        self.hass.async_add_job(self._device.add_disconnect_listener, self.on_device_disconnect)

    def on_message(self, message):
        """Call when new messages received from the climate."""
        if not isinstance(message, DysonPureHotCoolState):
            return

        _LOGGER.debug("Message received for climate device %s : %s", self.name, message)
        self.schedule_update_ha_state()

    def on_device_disconnect(self):
        """When device is disconnected, update HA state"""
        self.schedule_update_ha_state()

    def reconnect(self):
        _LOGGER.debug("Reconnecting to device %s", self.name)
        try:
            connected = self._device.connect(self._device.network_device.address)
            self.schedule_update_ha_state()
            if connected:
                _LOGGER.info("Reconnected to device %s", self.name)
            else:
                _LOGGER.warning("Unable to connect to device %s", self._device)
        except OSError as ose:
            _LOGGER.error(
                "Unable to connect to device %s: %s",
                str(self._device.network_device),
                str(ose),
            )

    @property
    def available(self) -> bool:
        return self._device.device_available

    @property
    def should_poll(self):
        """No polling needed."""
        return False

    @property
    def supported_features(self):
        """Return the list of supported features."""
        return SUPPORT_FLAGS

    @property
    def name(self):
        """Return the display name of this climate."""
        return self._device.name

    @property
    def temperature_unit(self):
        """Return the unit of measurement."""
        return TEMP_CELSIUS

    @property
    def current_temperature(self):
        """Return the current temperature."""
        if self._device.environmental_state:
            temperature_kelvin = self._device.environmental_state.temperature
            if temperature_kelvin != 0:
                self._current_temp = float("{0:.1f}".format(temperature_kelvin - 273))
        return self._current_temp

    @property
    def target_temperature(self):
        """Return the target temperature."""
        heat_target = int(self._device.state.heat_target) / 10
        return int(heat_target - 273)

    @property
    def current_humidity(self):
        """Return the current humidity."""
        if self._device.environmental_state:
            if self._device.environmental_state.humidity == 0:
                return None
            return self._device.environmental_state.humidity
        return None

    @property
    def hvac_mode(self):
        """Return hvac operation ie. heat, cool mode.

        Need to be one of HVAC_MODE_*.
        """
        if self._device.state.heat_mode == HeatMode.HEAT_ON.value:
            return HVAC_MODE_HEAT
        return HVAC_MODE_OFF

    @property
    def hvac_modes(self):
        """Return the list of available hvac operation modes.

        Need to be a subset of HVAC_MODES.
        """
        return SUPPORT_HVAG

    @property
    def hvac_action(self):
        """Return the current running hvac operation if supported.

        Need to be one of CURRENT_HVAC_*.
        """
        if self._device.state.heat_mode == HeatMode.HEAT_ON.value:
            if self._device.state.heat_state == HeatState.HEAT_STATE_ON.value:
                return CURRENT_HVAC_HEAT
            return CURRENT_HVAC_IDLE
        return CURRENT_HVAC_COOL

    @property
    def fan_mode(self):
        """Return the fan setting."""
        if self._device.state.focus_mode == FocusMode.FOCUS_ON.value:
            return FAN_FOCUS
        return FAN_DIFFUSE

    @property
    def fan_modes(self):
        """Return the list of available fan modes."""
        return SUPPORT_FAN

    def set_temperature(self, **kwargs):
        """Set new target temperature."""
        target_temp = kwargs.get(ATTR_TEMPERATURE)
        if target_temp is None:
            return
        target_temp = int(target_temp)
        _LOGGER.debug("Set %s temperature %s", self.name, target_temp)
        # Limit the target temperature into acceptable range.
        target_temp = min(self.max_temp, target_temp)
        target_temp = max(self.min_temp, target_temp)
        self._device.set_configuration(
            heat_target=HeatTarget.celsius(target_temp), heat_mode=HeatMode.HEAT_ON
        )

    def set_fan_mode(self, fan_mode):
        """Set new fan mode."""
        _LOGGER.debug("Set %s focus mode %s", self.name, fan_mode)
        if fan_mode == FAN_FOCUS:
            self._device.set_configuration(focus_mode=FocusMode.FOCUS_ON)
        elif fan_mode == FAN_DIFFUSE:
            self._device.set_configuration(focus_mode=FocusMode.FOCUS_OFF)

    def set_hvac_mode(self, hvac_mode):
        """Set new target hvac mode."""
        _LOGGER.debug("Set %s heat mode %s", self.name, hvac_mode)
        if hvac_mode == HVAC_MODE_HEAT:
            # todo: check if necessary to switch on fan
            self._device.set_configuration(heat_mode=HeatMode.HEAT_ON)
        elif hvac_mode == HVAC_MODE_OFF:
            # todo: check if necessary to turn off fan
            self._device.set_configuration(heat_mode=HeatMode.HEAT_OFF)

    @property
    def min_temp(self):
        """Return the minimum temperature."""
        return 1

    @property
    def max_temp(self):
        """Return the maximum temperature."""
        return 37
