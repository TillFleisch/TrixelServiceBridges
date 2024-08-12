"""Simple simulation client which generates random clients which contribute measurements according to their position."""

from datetime import datetime
from typing import Tuple

import numpy as np
from trixelserviceclient import ClientConfig, MeasurementType, Sensor

from ..config_schema import CoordinateGradientClientSimulationConfig
from .random_base_client import RandomBaseSimulationClient


class CoordinateGradientSimulationClient(RandomBaseSimulationClient):
    """Simple client which generates values based on it's position."""

    _client_simulation_config: CoordinateGradientClientSimulationConfig

    def __init__(
        self, client_simulation_config: CoordinateGradientClientSimulationConfig, config: ClientConfig | None = None
    ):
        """Generate a random base client with a single ambient temperature sensor."""
        sensors = [Sensor(measurement_type=MeasurementType.AMBIENT_TEMPERATURE)]
        super().__init__(client_simulation_config=client_simulation_config, sensors=sensors, config=config)

    def get_updates(self) -> dict[int, Tuple[datetime, float]]:
        """Provide normally distributed 'measurements' which reflect the sensors position."""
        rng = np.random.default_rng()
        deviation: float = self._client_simulation_config.deviation
        decimal_accuracy: int = self._client_simulation_config.decimal_accuracy
        updates = dict()

        for sensor in self.sensors:
            value: float
            if self._client_simulation_config.use_latitude:
                value = self._config.location.latitude
            else:
                value = self._config.location.longitude

            value = float(round(rng.normal(loc=value, scale=deviation, size=1)[0], decimal_accuracy))
            updates[sensor.sensor_id] = (datetime.now(), value)
        return updates
