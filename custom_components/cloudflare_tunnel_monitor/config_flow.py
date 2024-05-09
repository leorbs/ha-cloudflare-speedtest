import aiohttp
import async_timeout
import voluptuous as vol
from homeassistant import config_entries, exceptions
from .const import DOMAIN, CONF_DL_SIZE,PLACEHOLDER_DL_SIZE,LABEL_DL_SIZE


# Custom exceptions
class WrongFormat(exceptions.HomeAssistantError):
    """Error for wrong input."""

DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_DL_SIZE, description={LABEL_DL_SIZE}): str,
})

async def validate_data(hass, data):
    """Validate the provided credentials are correct."""
    size = data[CONF_DL_SIZE]

    try:
        int(size)
    except ValueError:
        raise WrongFormat

    return True

class CloudflareSpeedtestConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Cloudflare config flow."""

    VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle a flow initiated by the user."""
        errors = {}

        if user_input is not None:
            try:
                await validate_data(self.hass, user_input)
            except WrongFormat:
                errors["base"] = "wrong_format"
            except Exception:
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(title="Cloudflare Speedtest Monitor", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
            description_placeholders={
                CONF_DL_SIZE: PLACEHOLDER_DL_SIZE,
            }
        )