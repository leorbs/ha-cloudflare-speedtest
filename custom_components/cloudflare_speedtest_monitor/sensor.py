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

from .const import CONF_SCAN_INTERVAL, CONF_TRAFFIC_LIMIT, CONF_TEST_COUNT

from requests import Response

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
SIZE_5MB_int = 5000000
URL_DOWN = "https://speed.cloudflare.com/__down?bytes={}"
URL_META = "https://speed.cloudflare.com/meta"
TIMEOUT = 30


async def download(int_download_size_in_bytes=SIZE_10MB_int, amount_measurements=1, timeout=TIMEOUT, retries=1):
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
                servertime = float(response.headers['Server-Timing'].split(',')[0].split('=')[1]) / 1e3
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
            if retries > 0:
                _LOGGER.warning(f"Error fetching data: {err}; retrying...")
                return download(int_download_size_in_bytes, amount_measurements, timeout, retries - 1)

            raise UpdateFailed(f"Error fetching data: {err}; Could not update download data")

    return measurements

async def process_measurements(measurements):
    # Await the coroutine to get the actual data
    measurements_data = await measurements
    latencies = [(m["ttfb"] - m["servertime"]) * 1e3 for m in measurements_data]
    return latencies

def calculate_metrics(measurements):
    latencies = [(m["ttfb"] - m["servertime"]) * 1e3 for m in measurements]
    if len(latencies) > 1:
        jitter = statistics.median([abs(latencies[i] - latencies[i - 1]) for i in range(1, len(latencies))])
    else:
        jitter = None

    latency = statistics.median(latencies)

    downspeed = statistics.median([(m["size"] * 8 / (m["fulltime"] - m["ttfb"])) / 1e6 for m in measurements])

    return latency, jitter, downspeed


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



    @property
    def native_value(self):
        """Return the current sensor state."""
        if self._coordinator.data is None:
            _LOGGER.debug(f"No value available. Returning None")
            return None

        downspeed = self._coordinator.data["downspeed"]
        _LOGGER.debug(f"found latency: {downspeed}")
        return downspeed

    @property
    def available(self) -> bool:
        return self._coordinator.data is not None

    @property
    def suggested_display_precision(self) -> int | None:
        return 2



class CloudflareSpeedtestLatencySensor(CoordinatorEntity, SensorEntity):
    """Representation of a Cloudflare speedtest sensor."""

    def __init__(self, coordinator: DataUpdateCoordinator, config_entry_id: str):
        """Initialize the Cloudflare tunnel sensor."""
        super().__init__(coordinator)
        self._coordinator = coordinator
        self._attr_unique_id = f"{config_entry_id}_speedtest_sensor_latency"
        self._attr_name = "Cloudflare latency"
        self._attr_native_unit_of_measurement = "ms"
        self._attr_device_class = SensorDeviceClass.DURATION

    @property
    def native_value(self):
        """Return the current sensor state."""
        if self._coordinator.data is None:
            _LOGGER.debug(f"No value available. Returning None")
            return None

        latency = self._coordinator.data["latency"]
        _LOGGER.debug(f"found latency: {latency}")
        return latency

    @property
    def available(self) -> bool:
        return self._coordinator.data is not None



async def async_setup_entry(hass, config_entry: ConfigEntry, async_add_entities):
    """Set up the Cloudflare Speedtest sensor."""
    _LOGGER.debug(f"Got config.entry_id in async_setup_entry: {config_entry.entry_id}")
    _LOGGER.debug(f"Got config.data in async_setup_entry: {config_entry.data}")

    scan_interval = config_entry.data.get(CONF_SCAN_INTERVAL)  # Minutes
    traffic_limit = config_entry.data.get(CONF_TRAFFIC_LIMIT)  # MB
    test_count = config_entry.data.get(CONF_TEST_COUNT)

    async def async_update_data():
        """Fetch measurement data"""
        allCloudflareData = {}

        _LOGGER.debug(f"Taking a speed test from Cloudflare with traffic_limit={traffic_limit}MB, test_count={test_count}")
        measurements_download = await download(int_download_size_in_bytes=traffic_limit * 1024 * 1024, amount_measurements=test_count)
        _LOGGER.debug(f"Took speed test with data: {measurements_download}")
        _, _, downspeed = calculate_metrics(measurements_download)
        allCloudflareData["downspeed"] = downspeed

        _LOGGER.debug("Taking a latency test from Cloudflare")
        measurements_download = await download(int_download_size_in_bytes=1, amount_measurements=test_count)
        _LOGGER.debug(f"Took latency test with data: {measurements_download}")
        latency, jitter, _ = calculate_metrics(measurements_download)
        allCloudflareData["latency"] = latency
        allCloudflareData["jitter"] = jitter

        return allCloudflareData

    coordinator = DataUpdateCoordinator(
        hass=hass,
        logger=_LOGGER,
        name="cloudflare_speedtest",
        update_method=async_update_data,
        update_interval=timedelta(minutes=scan_interval),
    )

    # await coordinator.async_config_entry_first_refresh()

    download_sensor = CloudflareSpeedtestDownloadSensor(coordinator, config_entry.entry_id)
    latency_sensor = CloudflareSpeedtestLatencySensor(coordinator, config_entry.entry_id)

    async_add_entities([download_sensor, latency_sensor], True)



async def schedule_integration_reload(hass, entry_id):
    """Schedule a reload of the integration."""
    _LOGGER.info(f"Scheduling reload of integration with entry_id {entry_id}")
    await hass.config_entries.async_reload(entry_id)
