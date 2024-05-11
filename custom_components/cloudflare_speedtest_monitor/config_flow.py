import voluptuous as vol
from homeassistant import config_entries, exceptions
from .const import DOMAIN, CONF_DL_SIZE, LABEL_DL_SIZE, CONF_DL_PER_MEASUREMENT, CONF_UL_SIZE, CONF_UL_PER_MEASUREMENT, \
    CONF_SEC_BETWEEN_MEASUREMENTS, LABEL_UL_SIZE, LABEL_UL_PER_MEASUREMENT, LABEL_SEC_BETWEEN_MEASUREMENTS, \
    LABEL_DL_PER_MEASUREMENT, PLACEHOLDER_DL_SIZE

DATA_SCHEMA = vol.Schema({
    vol.Required(CONF_DL_SIZE, description={LABEL_DL_SIZE}): str,
    vol.Required(CONF_DL_PER_MEASUREMENT, description={LABEL_DL_PER_MEASUREMENT}): str,
    vol.Required(CONF_UL_SIZE, description={LABEL_UL_SIZE}): str,
    vol.Required(CONF_UL_PER_MEASUREMENT, description={LABEL_UL_PER_MEASUREMENT}): str,
    vol.Required(CONF_SEC_BETWEEN_MEASUREMENTS, description={LABEL_SEC_BETWEEN_MEASUREMENTS}): str,
})


def validate_int_field(data, errors, key):
    str_value = data[key]
    try:
        int(str_value)
    except ValueError:
        errors[key] = "wrong_format"
        return False
    except Exception:
        errors[key] = "unknown"
        return False
    return True


def validate_data(data, errors):
    if (validate_int_field(data, errors, CONF_DL_SIZE) and
            validate_int_field(data, errors, CONF_DL_PER_MEASUREMENT) and
            validate_int_field(data, errors, CONF_UL_SIZE) and
            validate_int_field(data, errors, CONF_UL_PER_MEASUREMENT) and
            validate_int_field(data, errors, CONF_SEC_BETWEEN_MEASUREMENTS)):
        return True
    else:
        return False

class CloudflareSpeedtestConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Cloudflare config flow."""

    VERSION = 1
    MINOR_VERSION = 1

    async def async_step_user(self, user_input=None):
        """Handle a flow initiated by the user."""

        errors = {}

        if user_input is not None:
            validated = validate_data(user_input, errors)
            if validated:
                return self.async_create_entry(title="Cloudflare Speedtest Monitor", data=user_input)

        return self.async_show_form(
            step_id="user",
            data_schema=DATA_SCHEMA,
            errors=errors,
            description_placeholders={
                CONF_DL_SIZE: PLACEHOLDER_DL_SIZE,
            }
        )