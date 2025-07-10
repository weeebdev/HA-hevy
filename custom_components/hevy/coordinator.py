"""DataUpdateCoordinator for hevy."""

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any

from homeassistant.exceptions import ConfigEntryAuthFailed
from homeassistant.helpers.update_coordinator import DataUpdateCoordinator, UpdateFailed

from .api import (
    HevyApiClientAuthenticationError,
    HevyApiClientError,
)
from .const import DEFAULT_WORKOUTS_COUNT, DOMAIN, LOGGER

if TYPE_CHECKING:
    from homeassistant.core import HomeAssistant

    from .data import HevyConfigEntry


class HevyDataUpdateCoordinator(DataUpdateCoordinator):
    """Class to manage fetching data from the API."""

    config_entry: HevyConfigEntry

    def __init__(
        self,
        hass: HomeAssistant,
        name: str,
        update_interval: timedelta,
    ) -> None:
        """Initialize the coordinator."""
        super().__init__(
            hass=hass,
            logger=LOGGER,
            name=DOMAIN,
            update_interval=update_interval,
        )
        self.name = name
        self.data: dict[str, Any] = {}

    async def _async_update_data(self) -> dict[str, Any]:
        """Update data via library."""
        try:
            # Get workout count
            workout_count_data = await self.config_entry.runtime_data.client.async_get_workout_count()
            
            # Get workouts data
            workouts_data = (
                await self.config_entry.runtime_data.client.async_get_workouts(
                    limit=DEFAULT_WORKOUTS_COUNT, offset=0
                )
            )

            # Process workouts into a more usable format
            processed_workouts = {}

            # Track counts for different time periods
            today_count = 0
            week_count = 0
            month_count = 0
            year_count = 0

            today = datetime.now().date()
            total_workout_count = 0

            for workout in workouts_data.get("workouts", []):
                total_workout_count += 1
                workout_id = workout["id"]
                workout_start_time = datetime.fromtimestamp(workout["start_time"])
                workout_name = workout["name"]

                workout_date = workout_start_time.date()
                if workout_date == today:
                    today_count += 1

                days_diff = (today - workout_date).days
                if days_diff < 7:
                    week_count += 1

                if (
                    workout_date.year == today.year
                    and workout_date.month == today.month
                ):
                    month_count += 1

                if workout_date.year == today.year:
                    year_count += 1

                exercises_data = {}
                for exercise in workout["exercises"]:
                    exercise_title = exercise["title"]
                    exercise_data = {
                        "title": exercise_title,
                        "sets": len(exercise["sets"]),
                        "total_reps": sum(
                            s.get("reps", 0)
                            for s in exercise["sets"]
                            if s.get("reps") is not None
                        ),
                        "max_weight_kg": max(
                            (
                                s.get("weight_kg", 0)
                                for s in exercise["sets"]
                                if s.get("weight_kg") is not None
                            ),
                            default=0,
                        ),
                    }
                    # Using exercise id as key instead of index_title
                    exercises_data[exercise["id"]] = exercise_data

                processed_workouts[workout_id] = {
                    "id": workout_id,
                    "title": workout_name,
                    "start_time": workout_start_time,
                    "exercises": exercises_data,
                    "estimated_volume_kg": workout.get("estimated_volume_kg", 0),
                }

            # Get total workout count from the dedicated API endpoint
            total_workout_count = workout_count_data.get("workout_count", 0)
            
            # Combine data
            return {
                "workout_count": total_workout_count,  # Use the dedicated workout_count endpoint
                "workouts": processed_workouts,
                "name": self.name,
                "today_count": today_count,
                "week_count": week_count,
                "month_count": month_count,
                "year_count": year_count,
            }

        except HevyApiClientAuthenticationError as exception:
            raise ConfigEntryAuthFailed(exception) from exception
        except HevyApiClientError as exception:
            raise UpdateFailed(exception) from exception
