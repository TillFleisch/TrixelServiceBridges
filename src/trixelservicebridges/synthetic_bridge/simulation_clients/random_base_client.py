"""A extended simulation client base class which provides a random generated client config based on the config file."""

import numpy as np
from pydantic_extra_types.coordinate import Coordinate
from trixelserviceclient import ClientConfig, Sensor

from ..base_simulation_client import SimulationClient
from ..config_schema import (
    FixedLocation,
    FixedValue,
    GridLocation,
    NormalRandom,
    NormalRandomLocation,
    RandomBaseClientSimulationConfig,
    UniformRandom,
    UniformRandomLocation,
)


def sample_value(config: FixedValue | NormalRandom | UniformRandom) -> float:
    """
    Sample a value according to the configuration restrictions.

    :param config: A value generation configuration
    :returns: A sampled value based on the provided configuration
    """
    rng = np.random.default_rng()
    if isinstance(config, FixedValue):
        return config.value
    elif isinstance(config, UniformRandom):
        return rng.uniform(low=config.min, high=config.max)
    elif isinstance(config, NormalRandom):
        return rng.normal(loc=config.mean, scale=config.deviation, size=1)[0]


def sample_location(
    config: FixedLocation | GridLocation | UniformRandomLocation | NormalRandomLocation,
    index: int,
    max_index: int,
) -> Coordinate:
    """
    Sample a location configuration based on the provided restrictions.

    :param config: A location value generation configuration
    :param index: The generation index of this client (0..max_index)
    :param max_index: The largest index form generated clients
    :returns: A sampled location based on the provided configuration.
    """
    rng = np.random.default_rng()
    if isinstance(config, FixedLocation):
        return Coordinate(latitude=config.latitude, longitude=config.longitude)
    elif isinstance(config, UniformRandomLocation):
        latitude = rng.uniform(low=config.area[0].latitude, high=config.area[1].latitude)
        longitude = rng.uniform(low=config.area[0].longitude, high=config.area[1].longitude)
        return Coordinate(latitude=latitude, longitude=longitude)
    elif isinstance(config, NormalRandomLocation):
        latitude = rng.normal(loc=config.latitude, scale=config.latitude_deviation, size=1)[0]
        longitude = rng.normal(loc=config.longitude, scale=config.longitude_deviation, size=1)[0]

        if latitude > 90.0:
            latitude = -90 + (latitude % 90)
        elif latitude < -90.0:
            latitude = 90 + (latitude % -90)

        if longitude > 180.0:
            longitude = -180 + (longitude % 180)
        elif longitude < -180.0:
            longitude = 180 + (longitude % -180)
        return Coordinate(latitude=latitude, longitude=longitude)
    elif isinstance(config, GridLocation):
        latitude_linspace = np.linspace(
            config.area[0].latitude, config.area[1].latitude, int(np.ceil(np.sqrt(max_index)))
        )
        longitude_linspace = np.linspace(
            config.area[0].longitude, config.area[1].longitude, int(np.ceil(np.sqrt(max_index)))
        )
        latitudes, longitudes = np.meshgrid(latitude_linspace, longitude_linspace)
        coordinates = np.vstack([latitudes.ravel(), longitudes.ravel()])
        return Coordinate(coordinates[0][index], coordinates[1][index])


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
