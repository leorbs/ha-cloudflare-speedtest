import voluptuous as vol
from homeassistant import config_entries, exceptions
from .const import DOMAIN, CONF_SCAN_INTERVAL, CONF_TRAFFIC_LIMIT, CONF_TEST_COUNT, UNIQUE_STATIC_ID

data_schema = vol.Schema({
    vol.Required(CONF_SCAN_INTERVAL, description={CONF_SCAN_INTERVAL}, default=5): vol.All(vol.Coerce(int), vol.Range(min=5, max=60)),
    vol.Required(CONF_TRAFFIC_LIMIT, description={CONF_TRAFFIC_LIMIT}, default=20): vol.All(vol.Coerce(int), vol.Range(min=10, max=100)),
    vol.Required(CONF_TEST_COUNT, description={CONF_TEST_COUNT}, default=2): vol.All(vol.Coerce(int), vol.Range(min=1, max=10)),
})

class CloudflareSpeedTestConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Cloudflare Speed Test configuration flow."""

    VERSION = 1
    def __init__(self):
        self.user_input = {}
        self.callReconfigure = False
    async def async_step_reconfigure(self, user_input=None):
        if user_input is not None:
            await self.async_set_unique_id(UNIQUE_STATIC_ID)
            self._abort_if_unique_id_mismatch()

            self.user_input = user_input
            self.callReconfigure = True
            return await self.async_step_showusage()

        return self.async_show_form(
            step_id="reconfigure",
            data_schema=data_schema
        )

    async def async_step_user(self, user_input=None):
        """Handle a user-initiated flow."""
        if user_input is not None:
            await self.async_set_unique_id(UNIQUE_STATIC_ID)
            self._abort_if_unique_id_configured()

            self.user_input = user_input
            self.callReconfigure = False
            return await self.async_step_showusage()


        return self.async_show_form(
            step_id="user",
            data_schema=data_schema
        )

    async def async_step_showusage(self, user_input=None):

        if user_input is not None:
            # Finalize the flow and create an entry
            if self.callReconfigure:
                return self.async_update_reload_and_abort(
                    self._get_reconfigure_entry(),
                    data_updates=self.user_input,
                )
            else:
                return self.async_create_entry(
                    title="Cloudflare Speed Test",
                    data=self.user_input,
                )

        scan_interval = self.user_input[CONF_SCAN_INTERVAL]
        test_count = self.user_input[CONF_TEST_COUNT]
        traffic_limit = self.user_input[CONF_TRAFFIC_LIMIT]

        monthMinutes = 30 * 24 + 60

        testsPerMonth = monthMinutes / scan_interval

        calculated_result = ((traffic_limit * test_count) * testsPerMonth) / 1000

        return self.async_show_form(
            step_id="showusage",
            data_schema=vol.Schema({}),  # No inputs, just display info
            description_placeholders={"calculated_result": str(calculated_result)},
        )
