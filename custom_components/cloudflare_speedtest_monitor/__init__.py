from homeassistant.config_entries import ConfigEntry
from homeassistant.core import HomeAssistant
from .const import DOMAIN

PLATFORMS = ["sensor"]
async def async_setup(hass: HomeAssistant, config: dict):
    """Set up the Cloudflare speedtest component."""
    return True

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Set up Cloudflare speedtest from a config entry."""
    hass.data.setdefault(DOMAIN, {})
    hass.data[DOMAIN][entry.entry_id] = entry.data

    await hass.config_entries.async_forward_entry_setups(entry, PLATFORMS)

    return True

async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry):
    """Unload a config entry."""
    unloadResult = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)

    hass.data[DOMAIN].pop(entry.entry_id)

    return unloadResult
