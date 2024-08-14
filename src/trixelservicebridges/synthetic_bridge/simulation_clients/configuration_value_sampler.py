"""Module which contains functionality to sample specific values based on user-provided configurations."""

import numpy as np
from pydantic_extra_types.coordinate import Coordinate

from ..config_schema import (
    FixedLocation,
    FixedValue,
    GridLocation,
    NormalRandom,
    NormalRandomLocation,
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
