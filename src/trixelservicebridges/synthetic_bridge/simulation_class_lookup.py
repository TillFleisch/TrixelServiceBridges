"""Helper module which contains functionality to determine the client simulation class based on the config file."""

from typing import Type

from .base_simulation_client import SimulationClient
from .blank_client import BlankSimulationClient
from .config_schema import AvailableClients

# Lookup table which holds the client class indicated by the configuration literal
simulation_client_class_lookup: dict[AvailableClients, Type[SimulationClient]] = {
    "blank": BlankSimulationClient,
}


def get_simulation_class(config_str: AvailableClients) -> Type[SimulationClient]:
    """
    Get the simulation class based on the configuration literal.

    :param config_str: The configuration literal which indicated the simulation client type
    :returns: The client simulation class which should be used
    """
    return simulation_client_class_lookup[config_str]
