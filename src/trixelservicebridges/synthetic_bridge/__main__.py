"""Run the synthetic bridge using the provided configuration file."""

import argparse
import asyncio
import os
import signal
import sys
from pathlib import Path

from pydantic_settings import SettingsConfigDict

from ..logging_helper import get_logger, set_logging_level
from .config_schema import BridgeConfig
from .simulation_manager import SimulationManager


async def main(config_path: Path, ignore_pickle: bool = False):
    """
    Load the user provided configuration file and run the synthetic bridge.

    :param config_path: Path which points to the bridge configuration file
    :param ignore_pickle: if True, an existing pickle file will be deleted
    """

    class CustomBridgeConfig(BridgeConfig):
        """Custom configuration file path bridge configuration."""

        model_config = SettingsConfigDict(toml_file=config_path)

    bridge_config = CustomBridgeConfig()

    set_logging_level(bridge_config.log_level)
    logger = get_logger(__name__)

    pickle_path = Path(bridge_config.pickle_file_path)
    if ignore_pickle and os.path.exists(pickle_path):
        os.remove(pickle_path)

    manager = SimulationManager(bridge_config=bridge_config)

    terminated: bool = False

    def signal_handler(sig, frame):
        """Terminate the synthetic bridge gracefully."""
        nonlocal terminated
        nonlocal manager

        if terminated:
            logger.critical("Forceful synthetic bridge termination!")
            sys.exit(0)
        else:
            logger.info("Gracefully terminating simulation manager and related clients.")

        manager.stop()
        terminated = True

    signal.signal(signal.SIGINT, signal_handler)
    await manager.run()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        prog="Synthetic Bridge",
        description="Adds simulated clients to the trixel sensor network.",
    )
    parser.add_argument(
        "-c",
        "--config_file",
        type=str,
        default="config/config.toml",
        help="Path which points the to the configuration file which should be used!",
    )
    parser.add_argument(
        "-r",
        "--reset",
        action="store_true",
        help="If set to true, an existing pickle file will be ignored.",
    )
    args = parser.parse_args()

    asyncio.run(main(config_path=args.config_file, ignore_pickle=args.reset))
