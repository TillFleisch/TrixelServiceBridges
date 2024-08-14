"""A extended simulation client base class which provides a random generated client config based on the config file."""

from trixelserviceclient import ClientConfig, Sensor

from ..base_simulation_client import SimulationClient
from ..config_schema import RandomBaseClientSimulationConfig
from .configuration_value_sampler import sample_location, sample_value


class RandomBaseSimulationClient(SimulationClient):
    """
    Base simulation client which generates a random client-configuration based on the provided user-configuration.

    This simulation client does not provide any value generating functionality, hence the name 'base'.
    """

    _client_simulation_config: RandomBaseClientSimulationConfig

    def __init__(
        self,
        client_simulation_config: RandomBaseClientSimulationConfig,
        sensors: list[Sensor],
        config: ClientConfig | None = None,
    ):
        """
        Use an existing client-configuration or generate a new client based on the provided simulation configuration.

        :param client_simulation_config: client simulation config which describes how clients should be generated.
        :param sensors: list of sensors configurations which is used when a new client is instantiated
        :param config: an existing client configuration
        """
        if config is None:

            config = ClientConfig(
                location=sample_location(
                    client_simulation_config.location_generation,
                    index=client_simulation_config.client_index,
                    max_index=client_simulation_config.max_client_index,
                ),
                # Prevent single measurement station trixel population
                k=max(int(round(sample_value(client_simulation_config.k_generation))), 2),
                # Limit to allowed range
                max_depth=max(1, min(24, int(round(sample_value(client_simulation_config.max_depth_generation))))),
                tls_host=client_simulation_config.tls_host,
                tls_use_ssl=client_simulation_config.tls_use_ssl,
                tms_use_ssl=client_simulation_config.tms_use_ssl,
                tms_address_override=client_simulation_config.tms_address_override,
                sensors=sensors,
            )
        super().__init__(client_simulation_config=client_simulation_config, config=config)
