import logging
import statistics
import array

import async_timeout
from homeassistant.components.sensor import SensorEntity, SensorDeviceClass
from homeassistant.config_entries import ConfigEntry
from homeassistant.core import callback
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed, CoordinatorEntity
from homeassistant.helpers.entity import Entity
from datetime import timedelta

from requests import Session, Response

from .const import DOMAIN

import asyncio
import requests

import time

_LOGGER = logging.getLogger(__name__)

# User configuration
# main sensors (upload speed, download speed)
# additional metadata
# when update

# Constants

SIZE_25MB_int = 25000000
SIZE_10MB_int = 10000000
URL_DOWN = "https://speed.cloudflare.com/__down?bytes={}"
URL_META = "https://speed.cloudflare.com/meta"
TIMEOUT = 30


async def download(int_download_size_in_bytes=SIZE_10MB_int, amount_measurements=4, timeout=TIMEOUT,
                   retries=1):
    url = URL_DOWN.format(str(int_download_size_in_bytes))

    measurements = []

    for i in range(0, amount_measurements):
        _LOGGER.debug(f"Attempt {i + 1} to download from URL: {url}")
        try:
            with async_timeout.timeout(timeout):
                start = time.time()
                response: Response = await asyncio.to_thread(requests.get, url)
                end = time.time()

                fulltime = end - start
                servertime = float(response.headers['Server-Timing'].split('=')[1]) / 1e3
                ttfb = response.elapsed.total_seconds()

                measurement = {"type": "download",
                               "size": int_download_size_in_bytes,
                               "servertime": servertime,
                               "fulltime": fulltime,
                               "ttfb": ttfb}

                _LOGGER.debug(f"start to end request time: {fulltime}, time to first byte: {ttfb}, "
                              f"time reported by server: {servertime}, bytes requested: {str(int_download_size_in_bytes)}")
                measurements.append(measurement)

        except Exception as err:
            _LOGGER.error(f"Error fetching data: {err}")
            if retries > 0:
                _LOGGER.error(f"retrying...")
                return download(int_download_size_in_bytes, amount_measurements, timeout, retries - 1)

            raise UpdateFailed("Could not update download data")

    return measurements


def calculate_metrics(measurements):
    latencies = [(m["ttfb"] - m["servertime"]) * 1e3 for m in measurements]
    if len(latencies) > 1:
        jitter = statistics.median([abs(latencies[i] - latencies[i - 1]) for i in range(1, len(latencies))])
    else:
        jitter = None

    latency = statistics.median(latencies)

    downspeed = statistics.median([(m["size"] * 8 / (m["fulltime"] - m["ttfb"])) / 1e6 for m in measurements])

    return latency, jitter, downspeed


# class CloudflareSpeedtestDeviceEntity(Entity):
#     """Representation of the Cloudflare speedtest device."""
#
#     def __init__(self, domain):
#         """Initialize the Cloudflare speedtest device."""
#         self._domain = domain
#
#     @property
#     def unique_id(self):
#         """Return a unique ID."""
#         return f"{self._domain}_cloudflare_speedtest"
#
#     @property
#     def name(self):
#         """Return the name of the device."""
#         return "Cloudflare Speedtest"
#
#     @property
#     def device_info(self):
#         """Return device information."""
#         return {
#             "identifiers": {(self._domain, self.unique_id)},
#             "name": self.name,
#             "manufacturer": "Cloudflare",
#         }


class CloudflareSpeedtestDownloadSensor(CoordinatorEntity, SensorEntity):
    """Representation of a Cloudflare speedtest sensor."""

    def __init__(self, coordinator: DataUpdateCoordinator, config_entry_id: str):
        """Initialize the Cloudflare tunnel sensor."""
        super().__init__(coordinator)
        self._coordinator = coordinator
        # self._device = deviceEntity
        self._attr_unique_id = f"{config_entry_id}_speedtest_sensor_download"
        self._attr_name = "Cloudflare download speed"
        self._attr_native_unit_of_measurement = "Mbit/s"
        self._attr_device_class = SensorDeviceClass.DATA_RATE

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        _LOGGER.debug("Handle coordinator update")
        # self._attr_state = self.native_value
        self.async_write_ha_state()

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self._coordinator.data is None:
            _LOGGER.debug(f"No value available. Returning None")
            return None

        downspeed = self._coordinator.data["downspeed"]
        _LOGGER.debug(f"found speed: {downspeed}")
        return downspeed

    @property
    def suggested_display_precision(self) -> int | None:
        return 2

    # @property
    # def device_info(self):
    #     """Return device information."""
    #     return {
    #         "identifiers": {(self._device._domain, self._device.unique_id)},
    #         "name": self._device.name,
    #         "manufacturer": "Cloudflare",
    #     }


class CloudflareSpeedtestLatencySensor(CoordinatorEntity, SensorEntity):
    """Representation of a Cloudflare speedtest sensor."""

    #todo add description that the latency is only for creating get requests. It has nothing to do with the ping latency
    def __init__(self, coordinator: DataUpdateCoordinator, config_entry_id: str):
        """Initialize the Cloudflare tunnel sensor."""
        super().__init__(coordinator)
        self._coordinator = coordinator
        # self._device = deviceEntity
        self._attr_unique_id = f"{config_entry_id}_speedtest_sensor_latency"
        self._attr_name = "Cloudflare latency"
        self._attr_native_unit_of_measurement = "ms"
        self._attr_device_class = SensorDeviceClass.DURATION

    @callback
    def _handle_coordinator_update(self) -> None:
        """Handle updated data from the coordinator."""
        _LOGGER.debug("Handle coordinator update")
        # self._attr_state = self.native_value
        self.async_write_ha_state()

    @property
    def native_value(self):
        """Return the state of the sensor."""
        if self._coordinator.data is None:
            _LOGGER.debug(f"No value available. Returning None")
            return None

        latency = self._coordinator.data["latency"]
        _LOGGER.debug(f"found latency: {latency}")
        return latency


async def async_setup_entry(hass, config_entry: ConfigEntry, async_add_entities):
    """Set up the Cloudflare Speedtest sensor."""

    _LOGGER.debug(f"got following config.entry_id in async_setup_entry: {config_entry.entry_id}")
    _LOGGER.debug(f"got following config.data in async_setup_entry: {config_entry.data}")


    # download size in MB
    # upload size in MB
    # how often within one measurement -> default 4
    # how many seconds between requests


    # device_entity = CloudflareSpeedtestDeviceEntity(DOMAIN)

    async def async_update_data():
        """Fetch measurement data"""

        # create all data in here
        # whatever will be returned is stored later in the coordinater.data var

        allCloudflareData = {}

        _LOGGER.debug("Taking a speedtest from Cloudflare with ")#todo add parameters
        measurements_download = await download()
        _LOGGER.debug(f"Took speedtest with data: {measurements_download}")
        _, _, downspeed = calculate_metrics(measurements_download)
        allCloudflareData["downspeed"] = downspeed

        _LOGGER.debug("Taking a latency test from Cloudflare with ")
        measurements_download = await download(int_download_size_in_bytes=1)
        _LOGGER.debug(f"Took latency with data: {measurements_download}")
        latency, jitter, _ = calculate_metrics(measurements_download)
        allCloudflareData["latency"] = latency
        allCloudflareData["jitter"] = jitter

        # todo add upload, packetloss, metadata
        # todo remove data in case of error

        return allCloudflareData

    coordinator = DataUpdateCoordinator(
        hass,
        _LOGGER,
        name="cloudflare_speedtest",
        update_method=async_update_data,
        update_interval=timedelta(minutes=1),
    )

    # await coordinator.async_config_entry_first_refresh()

    download_sensor = CloudflareSpeedtestDownloadSensor(coordinator, config_entry.entry_id)
    latency_sensor = CloudflareSpeedtestLatencySensor(coordinator, config_entry.entry_id)

    async_add_entities([download_sensor], True)
    async_add_entities([latency_sensor], True)


async def schedule_integration_reload(hass, entry_id):
    """Schedule a reload of the integration."""
    _LOGGER.info(f"Scheduling reload of integration with entry_id {entry_id}")
    await hass.config_entries.async_reload(entry_id)
