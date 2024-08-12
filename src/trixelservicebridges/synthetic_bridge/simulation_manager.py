"""Manages the synthetic bridge by simulating multiple clients according to the configuration file."""

import asyncio
import os
import pathlib
import pickle
from typing import Tuple

from trixelserviceclient import ClientConfig

from ..logging_helper import get_logger, update_log_level
from .config_schema import BridgeConfig, ClientSimulationConfig
from .simulation_class_lookup import SimulationClient, get_simulation_class

logger = get_logger(__name__)


class SimulationManager:
    """Manager which instantiates multiple clients and stores their configuration in bulk using pickle."""

    clients: list[SimulationClient]

    bridge_config: BridgeConfig

    def __init__(
        self,
        bridge_config: BridgeConfig,
        generate_clients: bool = True,
    ) -> None:
        """
        Initialize the manager by loading existing clients and/or generating new ones.

        :param bridge_config: simulation configuration model
        :param generate_clients: if set to true, new clients will be generated, otherwise only existing clients are used
        """
        global logger
        logger = update_log_level(logger)
        self.bridge_config = bridge_config
        self.clients = list()
        self.load()
        if generate_clients:
            self.generate()

    def generate(self):
        """Generate remaining clients based on the simulation configuration file."""
        logger.debug(f"Generating {self.bridge_config.target_client_count-len(self.clients)} new clients.")
        client_simulation_class = get_simulation_class(self.bridge_config.client_simulation_config.client_class)
        for i in range(len(self.clients), self.bridge_config.target_client_count):
            client_simulation_config: ClientSimulationConfig = self.bridge_config.client_simulation_config.model_copy(
                deep=True
            )
            client_simulation_config.client_index = i
            client_simulation_config.max_client_index = self.bridge_config.target_client_count
            self.clients.append(client_simulation_class(client_simulation_config=client_simulation_config))

    def load(self):
        """
        Load client configurations from pickle and instantiate existing clients.

        Existing clients are instantiated to the type and with the configuration which was used when they were created.
        """
        logger.info("Loading existing client and configurations")
        try:
            file = open(pathlib.Path(self.bridge_config.pickle_file_path), "rb")
            configs = pickle.load(file)

            client_type_overview: dict[str, int] = dict()
            self.clients = list()

            config: ClientConfig
            client_simulation_config: ClientSimulationConfig
            for config, client_simulation_config in configs:
                client_class = get_simulation_class(client_simulation_config.client_class)
                client_type_overview[client_class.__name__] = client_type_overview.get(client_class.__name__, 0) + 1
                self.clients.append(client_class(config=config, client_simulation_config=client_simulation_config))
            logger.info(f"Loaded existing clients: {client_type_overview}")
        except FileNotFoundError:
            logger.warning("Existing pickle file not found, instantiating new clients!")
            pass

    def store(self):
        """Store all client configurations in a single pickle file."""
        logger.info("Storing existing clients and configurations.")
        client_configs: list[Tuple[ClientConfig, ClientSimulationConfig]] = list()
        client: SimulationClient
        for client in self.clients:
            client_configs.append((client._config, client._client_simulation_config))

        pickle_path = pathlib.Path(self.bridge_config.pickle_file_path)
        pathlib.Path.mkdir(pathlib.Path(os.path.dirname(pickle_path)), parents=True, exist_ok=True)
        file = open(pickle_path, "wb")
        pickle.dump(client_configs, file)
        file.close()

    async def run(self, delete: bool = False):
        """Run the simulation manager, which spawns the desired number of clients.

        Must be called once client have been loaded or generated.
        :param delete: if set to true, clients will be gracefully deleted from the network once they are ready
        """
        tasks: list[asyncio.Task] = list()
        running_tasks: list[asyncio.Task] = list()

        client: SimulationClient
        for i, client in enumerate(self.clients):
            if i >= self.bridge_config.target_client_count:
                continue
            tasks.append(client.run(delete=delete))

        async with asyncio.TaskGroup() as tg:
            logger.debug(f"Starting {len(tasks)} clients!")
            for task in tasks:
                running_tasks.append(tg.create_task(task))
                if self.bridge_config.client_spawn_delay is not None:
                    await asyncio.sleep(self.bridge_config.client_spawn_delay.total_seconds())
            logger.info(f"Started {len(tasks)} client!")

        if delete:
            deleted_clients: list[SimulationClient] = list()
            for client in self.clients:
                if client._config.ms_config is None:
                    deleted_clients.append(client)

            for client in deleted_clients:
                self.clients.remove(client)

        self.store()

    def stop(self):
        """Stop the manager gracefully by killing all clients and persisting their configuration."""
        for client in self.clients:
            client.kill()
