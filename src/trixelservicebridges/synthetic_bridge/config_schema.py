"""Pydantic (configuration) schema which are related to the synthetic bridge."""

import logging
from datetime import timedelta
from pathlib import Path
from typing import Literal, Tuple, Type

from pydantic import BaseModel, NonNegativeInt, PositiveInt
from pydantic_settings import (
    BaseSettings,
    PydanticBaseSettingsSource,
    SettingsConfigDict,
    TomlConfigSettingsSource,
)

AvailableClients = Literal["blank"]


class ClientSimulationConfig(BaseModel):
    """
    Configuration options for simulated clients.

    This config model does not contain the individual specific client settings but rather settings related to how they
    are generated, this also includes potential parameters which can be used for value generation.
    """

    client_class: AvailableClients

    # polling client settings
    retry_interval: timedelta = timedelta(seconds=30)
    max_retries: PositiveInt | None = 10
    polling_interval: timedelta = timedelta(seconds=60)

    # client base settings
    tls_host: str
    tls_use_ssl: bool = True
    tms_use_ssl: bool = True
    tms_address_override: str | None = None


class BlankClientSimulationConfig(ClientSimulationConfig):
    """Blank simulation client specific configuration options."""

    client_class: Literal["blank"] = "blank"
    k: PositiveInt = 3


AvailableSimulationConfigs = BlankClientSimulationConfig


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
