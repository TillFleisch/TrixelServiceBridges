"""Crude approximation of environmental properties based on the time of day for simulation/test purposes."""

from datetime import datetime, timedelta
from typing import Tuple

import numpy as np
from trixelserviceclient import ClientConfig, MeasurementType, Sensor

from ..config_schema import DiurnalApproximationClientSimulationConfig
from .configuration_value_sampler import sample_value
from .random_base_client import RandomBaseSimulationClient
from .skewed_client import SkewedSimulationClient


class DiurnalApproximationSimulationClient(RandomBaseSimulationClient):
    """Crude approximation of environmental properties based on the time of day for simulation/test purposes."""

    _client_simulation_config: DiurnalApproximationClientSimulationConfig

    def __init__(
        self, client_simulation_config: DiurnalApproximationClientSimulationConfig, config: ClientConfig | None = None
    ):
        """Generate a random base client with a single ambient temperature sensor."""

        if client_simulation_config.sensor_accuracy is None:
            rng = np.random.default_rng()
            if (
                client_simulation_config.sensor_undefined_accuracy_chance is None
                or rng.uniform(low=0, high=1) > client_simulation_config.sensor_undefined_accuracy_chance
            ):
                client_simulation_config.sensor_accuracy = -1
            else:
                client_simulation_config.sensor_accuracy = max(
                    0,
                    round(
                        sample_value(client_simulation_config.sensor_accuracy_generation),
                        client_simulation_config.sensor_accuracy_decimals,
                    ),
                )

        accuracy = None if client_simulation_config.sensor_accuracy < 0 else client_simulation_config.sensor_accuracy
        sensors = [Sensor(measurement_type=MeasurementType.AMBIENT_TEMPERATURE, accuracy=accuracy)]

        if client_simulation_config.peak_time is None:
            client_simulation_config.peak_time = sample_value(client_simulation_config.peak_time_generation)
        if client_simulation_config.min_temperature is None:
            client_simulation_config.min_temperature = sample_value(client_simulation_config.min_temperature_generation)
        if client_simulation_config.max_temperature is None:
            client_simulation_config.max_temperature = sample_value(client_simulation_config.max_temperature_generation)

        super().__init__(client_simulation_config=client_simulation_config, sensors=sensors, config=config)

    def get_updates(self) -> dict[int, Tuple[datetime, float]]:
        """Generate approximate environmental properties based on the time of day."""
        updates: dict[int, Tuple[datetime, float]] = dict()

        min_temperature = self._client_simulation_config.min_temperature
        max_temperature = self._client_simulation_config.max_temperature
        peak_time = self._client_simulation_config.peak_time
        equator_distance = np.abs(self._config.location.latitude) / 90.0

        now = datetime.now()
        day_age: timedelta = now - datetime(year=now.year, month=now.month, day=now.day)
        day_total_seconds = timedelta(days=1).total_seconds()
        squeeze_factor = day_total_seconds / self._client_simulation_config.day_squeeze
        day_age: int = day_age.total_seconds() % squeeze_factor

        # Day progress between 0..1 compensated for day_squeeze property
        day_age: float = day_age / squeeze_factor

        sin_value = (np.sin(day_age * 2 * np.pi - (np.pi * (peak_time * 2 - 0.5))) + 1) / 2

        value = sin_value * (max_temperature - min_temperature) + min_temperature

        value += (1 - equator_distance) * self._client_simulation_config.equator_temperature_bias

        for sensor in self.sensors:
            if sensor.measurement_type == MeasurementType.AMBIENT_TEMPERATURE:
                updates[sensor.sensor_id] = (datetime.now(), value)
            elif sensor.measurement_type == MeasurementType.RELATIVE_HUMIDITY:
                updates[sensor.sensor_id] = (datetime.now(), 1 - value)

        return updates


class SkewedDiurnalApproximationSimulationClient(SkewedSimulationClient, DiurnalApproximationSimulationClient):
    """Extended implementation which skews measurements according to the user-configuration."""

    pass
