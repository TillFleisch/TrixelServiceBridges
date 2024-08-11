"""A simple simulation client implementation which provides useless (non-contributing) virtual measurement stations."""

from datetime import datetime
from typing import Tuple

from pydantic_extra_types.coordinate import Coordinate
from trixelserviceclient import ClientConfig
from trixelserviceclient.schema import MeasurementType, Sensor

from ..base_simulation_client import SimulationClient
from ..config_schema import BlankClientSimulationConfig


class BlankSimulationClient(SimulationClient):
    """A blank client which does not have any sensors and therefore does not generate any measurements."""

    _client_simulation_config: BlankClientSimulationConfig

    def __init__(self, client_simulation_config: BlankClientSimulationConfig, config: ClientConfig | None = None):
        """Initialize a blank client measurement station which has a single temperature sensors."""
        if config is None:
            config = ClientConfig(
                location=Coordinate(0, 0),
                k=client_simulation_config.k,
                tls_host=client_simulation_config.tls_host,
                tls_use_ssl=client_simulation_config.tls_use_ssl,
                tms_use_ssl=client_simulation_config.tms_use_ssl,
                tms_address_override=client_simulation_config.tms_address_override,
                sensors=[Sensor(measurement_type=MeasurementType.AMBIENT_TEMPERATURE)],
            )
        super().__init__(client_simulation_config=client_simulation_config, config=config)

    def get_updates(self) -> dict[int, Tuple[datetime, float]]:
        """Provide no updates for any sensors."""
        return dict()
