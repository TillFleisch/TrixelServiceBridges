"""Pydantic (configuration) schema which are related to the synthetic bridge."""

import logging
from datetime import timedelta
from pathlib import Path
from typing import Literal, Tuple, Type

from pydantic import BaseModel, NonNegativeInt, PositiveInt
from pydantic_extra_types.coordinate import Coordinate, Latitude, Longitude
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)

AvailableClients = Literal["blank", "coordinate_gradient"]


class ClientSimulationConfig(BaseModel):
    """
    Configuration options for simulated clients.

    This config model does not contain the individual specific client settings but rather settings related to how they
    are generated, this also includes potential parameters which can be used for value generation.
    """

    client_class: AvailableClients

    # General client generation attributes
    client_index: NonNegativeInt = 0
    max_client_index: NonNegativeInt = 0

    # polling client settings
    retry_interval: timedelta = timedelta(seconds=30)
    max_retries: PositiveInt | None = 10
    polling_interval: timedelta = timedelta(seconds=60)

    # client base settings
    tls_host: str
    tls_use_ssl: bool = True
    tms_use_ssl: bool = True
    tms_address_override: str | None = None


class FixedLocation(BaseModel):
    """Fixed location configuration."""

    type: Literal["fixed"] = "fixed"
    latitude: Latitude
    longitude: Longitude


class GridLocation(BaseModel):
    """Grid based location generation settings."""

    type: Literal["grid"] = "grid"
    area: Tuple[Coordinate, Coordinate] = (Coordinate(-90, -180), Coordinate(90, 180))


class UniformRandomLocation(BaseModel):
    """Uniformly distributed location generation settings."""

    type: Literal["uniform_random"] = "uniform_random"
    area: Tuple[Coordinate, Coordinate] = (Coordinate(-90, -180), Coordinate(90, 180))


class NormalRandomLocation(BaseModel):
    """Location generation settings using normal distribution."""

    type: Literal["normal_random"] = "normal_random"
    latitude: Latitude
    longitude: Longitude
    latitude_deviation: float
    longitude_deviation: float


class FixedValue(BaseModel):
    """Fixed value configuration."""

    type: Literal["fixed"] = "fixed"
    value: int


class NormalRandom(BaseModel):
    """Normal distribution random value generation settings."""

    type: Literal["normal_random"] = "normal_random"
    mean: float
    deviation: float


class UniformRandom(BaseModel):
    """Uniformly distributed random value generation settings."""

    type: Literal["uniform_random"] = "uniform_random"
    min: float
    max: float


class RandomBaseClientSimulationConfig(ClientSimulationConfig):
    """Client configuration settings related to the base random client."""

    client_class: Literal["random_base"] = "random_base"

    # Note that the random generation of lat/lng does not compensate for the earth curvature
    location_generation: FixedLocation | GridLocation | UniformRandomLocation | NormalRandomLocation = FixedLocation(
        latitude=0, longitude=0
    )
    k_generation: FixedValue | NormalRandom | UniformRandom = FixedValue(value=3)
    max_depth_generation: FixedValue | NormalRandom | UniformRandom = FixedValue(value=24)


class BlankClientSimulationConfig(ClientSimulationConfig):
    """Blank simulation client specific configuration options."""

    client_class: Literal["blank"] = "blank"
    k: PositiveInt = 3


class CoordinateGradientClientSimulationConfig(RandomBaseClientSimulationConfig):
    """Configuration options related to the coordinate gradient client simulation."""

    client_class: Literal["coordinate_gradient"] = "coordinate_gradient"

    use_latitude: bool = True
    deviation: float = 0.1
    decimal_accuracy: NonNegativeInt = 2


AvailableSimulationConfigs = BlankClientSimulationConfig | CoordinateGradientClientSimulationConfig


class BridgeConfig(BaseSettings):
    """Base bridge configuration, which contains general bridge configurations as well client specific options."""

    client_simulation_config: AvailableSimulationConfigs

    model_config = SettingsConfigDict(toml_file="config/config.toml")

    log_level: NonNegativeInt = logging.NOTSET
    pickle_file_path: Path = "config/multi.pkl"
    target_client_count: PositiveInt = 1
    client_spawn_delay: timedelta | None = timedelta(microseconds=0.1)

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: PydanticBaseSettingsSource,
        env_settings: PydanticBaseSettingsSource,
        dotenv_settings: PydanticBaseSettingsSource,
        file_secret_settings: PydanticBaseSettingsSource,
    ) -> Tuple[PydanticBaseSettingsSource, ...]:
        """Load config from TOML resource."""
        return (TomlConfigSettingsSource(settings_cls),)
