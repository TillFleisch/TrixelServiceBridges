"""Base simulation client class from which different simulation client can be derived."""

from datetime import datetime
from typing import Tuple

from trixelserviceclient import ClientConfig
from trixelserviceclient.extended_clients.polling_client import PollingClient

from .config_schema import ClientSimulationConfig


class SimulationClient(PollingClient):
    """Base class for simulated polling clients for use with bulk storage via pickling."""

    _client_simulation_config: ClientSimulationConfig

    def __init__(self, config: ClientConfig, client_simulation_config: ClientSimulationConfig):
        """
        Initialize the simulation client with the provided config and without persist callback.

        :param config: The client TCS client configuration
        :param client_simulation_config: client simulation related configuration
        """
        self._client_simulation_config = client_simulation_config
        super().__init__(config, None)

    async def run(self, delete: bool = False):
        """
        Run the polling based client using the user provided configuration.

        :param delete: If set, clients are instructed to delete themselves from their registered TMS
        """
        await super().run(
            get_updates=self.get_updates,
            retry_interval=self._client_simulation_config.retry_interval,
            polling_interval=self._client_simulation_config.polling_interval,
            max_retries=self._client_simulation_config.max_retries,
            delete=delete,
        )

    def get_updates(self) -> dict[int, Tuple[datetime, float]]:
        """
        Provide a single measurement for this client based on the provided simulation configuration.

        :returns: dictionary containing the new measurements for each sensors of this client
        """
        raise NotImplementedError
