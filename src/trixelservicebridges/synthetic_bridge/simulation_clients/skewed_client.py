"""An extension for simulation clients which skews sensor updates."""

from datetime import datetime, timedelta
from typing import Tuple

import numpy as np
from trixelserviceclient.schema import ClientConfig

from ..base_simulation_client import SimulationClient
from ..config_schema import SkewedClientSimulationConfig
from .configuration_value_sampler import sample_value


class SkewedSimulationClient(SimulationClient):
    """An extension for simulation clients which skews the sensor updates according to the configuration file."""

    _client_simulation_config: SkewedClientSimulationConfig

    _dropout_end_time: dict[int, datetime]

    _value_retention_end_time: dict[int, datetime]

    _retained_values: dict[int, float | None]

    _last_day_age: int = timedelta(days=1).total_seconds()

    _daily_bias: float = 0

    def __init__(self, client_simulation_config: SkewedClientSimulationConfig, config: ClientConfig | None = None):
        """Determine static arguments during client initialization."""
        self._dropout_end_time = dict()
        self._value_retention_end_time = dict()
        self._retained_values = dict()
        if client_simulation_config.bias is None and client_simulation_config.bias_generation is not None:
            client_simulation_config.bias = sample_value(client_simulation_config.bias_generation)
        if (
            client_simulation_config.positive_daytime_bias_impact is None
            and client_simulation_config.positive_daytime_bias_impact_generation is not None
        ):
            client_simulation_config.positive_daytime_bias_impact = sample_value(
                client_simulation_config.positive_daytime_bias_impact_generation
            )

        super().__init__(client_simulation_config=client_simulation_config, config=config)

    def get_updates(self) -> dict[int, Tuple[datetime, float]]:
        """
        Skew existing sensor measurements according to the user configuration.

        Retrieve the simulated value for a sensor and apply transformations.
        A sensor can 'dropout' in which case further consecutive updates are suppressed for a period of time.
        A sensor can 'skip measurements' in which case a sensors measurement is not transmitted.
        A sensor can 'retain values' in which case the last measurement will be sent repeatedly for a period of time.

        Further value modifications include:
            * static value bias
            * additive noise
            * impulse noise

        Additionally, there are day-time dependent transformations:
            * a bias, which changes each day, but remains static otherwise
            * an additive bias which changes over the course of the day

            The additive bias is a quadratic function which is sampled based on the time of day. Negative values are
            ignored, while positive values are added to the measurement in proportion to (positive_daytime_bias_impact).
            The position and duration of the 'spike' are chosen at random around the middle of a day.
        """
        updates = super().get_updates()
        rng = np.random.default_rng()
        dropped_sensors: set[int] = set()
        now = datetime.now()
        day_age: timedelta = now - datetime(year=now.year, month=now.month, day=now.day)
        day_total_seconds = timedelta(days=1).total_seconds()
        squeeze_factor = day_total_seconds / self._client_simulation_config.day_squeeze
        day_age: int = day_age.total_seconds() % squeeze_factor
        day_age: float = day_age / squeeze_factor

        if day_age < self._last_day_age and self._client_simulation_config.daily_bias_generation is not None:
            self._daily_bias = sample_value(self._client_simulation_config.daily_bias_generation)

        for i, (timestamp, value) in updates.items():

            if self._client_simulation_config.dropout_chance is not None:
                if now < self._dropout_end_time.get(i, now - timedelta(seconds=1)):
                    dropped_sensors.add(i)
                    continue

                elif rng.uniform(0, 1) <= self._client_simulation_config.dropout_chance:
                    self._dropout_end_time[i] = now + timedelta(
                        seconds=sample_value(self._client_simulation_config.dropout_period)
                    )
                    dropped_sensors.add(i)
                    continue

            if self._client_simulation_config.skipped_measurement_chance is not None:
                if rng.uniform(0, 1) <= self._client_simulation_config.skipped_measurement_chance:
                    dropped_sensors.add(i)
                    continue

            value += self._daily_bias

            if self._client_simulation_config.bias is not None:
                value += self._client_simulation_config.bias

            if self._client_simulation_config.positive_daytime_bias_impact is not None:
                offset: float = rng.uniform(-0.1, 0.1)
                spread: float = rng.uniform(2, 15)
                strength: float = self._client_simulation_config.positive_daytime_bias_impact

                time_bias_factor = max(0, -np.power((day_age + offset) * spread - spread / 2, 2) + 1)

                value += value * (time_bias_factor * strength)

            if self._client_simulation_config.noise_generation is not None:
                value += sample_value(self._client_simulation_config.noise_generation)

            if (
                self._client_simulation_config.impulse_noise_chance is not None
                and rng.uniform(0, 1) <= self._client_simulation_config.impulse_noise_chance
            ):
                value += sample_value(self._client_simulation_config.impulse_generation) * (
                    1.0 if rng.uniform(0, 1) <= 0.5 else -1.0
                )

            if self._client_simulation_config.value_retain_chance is not None:
                if now < self._value_retention_end_time.get(i, now - timedelta(seconds=1)):
                    updates[i] = (timestamp, self._retained_values.get(i, None))
                elif rng.uniform(0, 1) <= self._client_simulation_config.value_retain_chance:
                    self._value_retention_end_time[i] = now + timedelta(
                        seconds=sample_value(self._client_simulation_config.value_retain_period)
                    )
                    self._retained_values[i] = value

            updates[i] = (timestamp, value)

        for sensor in dropped_sensors:
            del updates[sensor]

        self._last_day_age = day_age
        return updates
