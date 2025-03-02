# Cloudflare Speed Test

## Overview
The **Cloudflare Speed Test** custom component for Home Assistant 
allows users to monitor internet speed performance by conducting periodic 
speed tests using Cloudflare's test endpoint https://speed.cloudflare.com/. Users can configure 
the frequency of tests, the number of test runs, and the data limits 
to ensure optimal monitoring.

**Note**: **The latency reported by this integration is only for
connecting GET requests. It has nothing to do with the traditional ping latency.**

## Installation

### Manual Installation
1. Download the custom component files and place them in the following directory:
   ```
   <home_assistant_config>/custom_components/cloudflare_speedtest/
   ```
2. Restart Home Assistant to recognize the new component.

### HACS (Home Assistant Community Store)
1. Add the repository as a custom repository in HACS.
2. Install the component from HACS.
3. Restart Home Assistant.

## Configuration
To configure the component:
1. Go to **Settings > Devices & Services > Integrations**.
2. Search for **Cloudflare Speed Test** and add the integration.
3. Configure the following options:
   - **Scan Interval**: Time interval (in minutes) between speed tests (Min: 5, Max: 60)
   - **Traffic Limit**: Maximum data consumption per test (Min: 10 MB, Max: 100 MB)
   - **Test Count**: Number of speed test runs per execution (Min: 1, Max: 10)
4. Review estimated data usage before confirming setup.
.

## Support
For issues or feature requests, please create a GitHub issue in the repository.

