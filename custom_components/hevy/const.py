"""Constants for Hevy integration."""

from logging import Logger, getLogger

LOGGER: Logger = getLogger(__package__)

DOMAIN = "hevy"
ATTRIBUTION = "Data provided by Hevy"
CONF_AUTH_TOKEN = "auth_token"
CONF_USERNAME = "username"
CONF_NAME = "name"
CONF_X_API_KEY = "x_api_key"
BASE_URL = "https://api.hevyapp.com"

DEFAULT_X_API_KEY = "shelobs_hevy_web"

DEFAULT_WORKOUTS_COUNT = 5
DEFAULT_SCAN_INTERVAL = 60  # minutes
