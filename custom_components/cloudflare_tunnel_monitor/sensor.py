import logging
import async_timeout
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed
from homeassistant.helpers.entity import Entity
from datetime import timedelta
from .const import DOMAIN
import aiohttp
from random import randint

import time

_LOGGER = logging.getLogger(__name__)

# User configuration
# main sensors (upload speed, download speed)
# additional metadata
# when update

# Constants

SIZE_25MB = "25000000"
SIZE_10MB = "10000000"
SIZE_10MB_int = 10000000
URL_DOWN = "https://speed.cloudflare.com/__down?bytes={}"
URL_META = "https://speed.cloudflare.com/meta"
TIMEOUT = 30


def create_headers(api_key):
    """Create headers for API requests."""
    return {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json',
    }


async def download(retries=0):
    # runs download tests

    url = URL_DOWN.format(SIZE_10MB)

    _LOGGER.debug(f"Attempt {retries + 1} to download from URL: {url}")
    async with aiohttp.ClientSession() as session:
        try:
            with async_timeout.timeout(TIMEOUT):
                start = time.time()
                async with session.get(url) as response:
                    end = time.time()
                    _LOGGER.debug(f"Response status: {response.status}")
                    if response.status == 200:
                        downtime = end - start
                        servertime = float(response.headers['Server-Timing'].split('=')[1]) / 1e3
                        measurement = {}
                        measurement["type"] = "download"
                        measurement["size"] = SIZE_10MB_int
                        measurement["servertime"] = servertime
                        measurement["downtime"] = downtime

                        _LOGGER.debug(f"downtime: {downtime}")
                        return measurement
                    else:
                        _LOGGER.error(f"Error downloading masurenebt data: {response.status}, {response.reason}")
                        raise UpdateFailed("Error creating Cloudflare download measurement")


        except Exception as err:
            _LOGGER.error(f"Error fetching data: {err}")
            raise UpdateFailed("Could not update download data")


class CloudflareSpeedtestDeviceEntity(Entity):
    """Representation of the Cloudflare speedtest device."""

    def __init__(self, domain):
        """Initialize the Cloudflare speedtest device."""
        self._domain = domain

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self._domain}_cloudflare_speedtest"

    @property
    def name(self):
        """Return the name of the device."""
        return "Cloudflare Speedtest"

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(self._domain, self.unique_id)},
            "name": self.name,
            "manufacturer": "Cloudflare",
        }


class CloudflareSpeedtestDownloadSensor(SensorEntity):
    """Representation of a Cloudflare speedtest sensor."""

    def __init__(self, deviceEntity: CloudflareSpeedtestDeviceEntity, coordinator: DataUpdateCoordinator):
        """Initialize the Cloudflare tunnel sensor."""
        self._coordinator = coordinator
        self._device = deviceEntity

    @property
    def name(self):
        """Return the name of the sensor."""
        return f"Cloudflare Speedtest sensor"

    @property
    def unique_id(self):
        """Return a unique ID."""
        return f"{self._device._domain}_speedtest_sensor_download"

    @property
    def native_value(self):
        """Return the state of the sensor."""
        downloadMeasurement = self._coordinator.data["measurements"][0]

        _LOGGER.debug(f"found download measurement: {downloadMeasurement}")

        speed = downloadMeasurement["size"] * 8 / downloadMeasurement["downtime"] / 1e6

        _LOGGER.debug(f"found speed: {speed}")
        return speed

    @property
    def native_unit_of_measurement(self):
        """Return the unit of measurement of the sensor, if any."""
        return "Mbps"

    @property
    def device_class(self):
        """Return the device class of the sensor."""
        return SensorDeviceClass.DATA_RATE

    @property
    def device_info(self):
        """Return device information."""
        return {
            "identifiers": {(self._device._domain, self._device.unique_id)},
            "name": self._device.name,
            "manufacturer": "Cloudflare",
        }


async def async_setup_entry(hass, config_entry, async_add_entities):
    """Set up the Cloudflare Speedtest sensor."""

    device_entity = CloudflareSpeedtestDeviceEntity(DOMAIN)

    async def async_update_data():
        """Fetch measurement data"""

        # create all data in here
        # whatever will be returned is stored later in the coordinater.data var

        _LOGGER.debug("Taking a speedtest from Cloudflare")
        measurement_download = await download()
        _LOGGER.debug(f"Took speedtest with data: {measurement_download}")

        allCloudflareData = {}
        allCloudflareData["measurements"] = [measurement_download]

        # todo add upload, latency, packetloss, metadata

        return allCloudflareData

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="cloudflare_speedtest",
        update_method=async_update_data,
        update_interval=timedelta(minutes=1),
    )

    await coordinator.async_config_entry_first_refresh()

    download_sensor = CloudflareSpeedtestDownloadSensor(device_entity, coordinator)

    async_add_entities([device_entity], True)
    async_add_entities([download_sensor], True)


async def schedule_integration_reload(hass, entry_id):
    """Schedule a reload of the integration."""
    _LOGGER.info(f"Scheduling reload of integration with entry_id {entry_id}")
    await hass.config_entries.async_reload(entry_id)
