"""Logging helper which provides a logger with custom formatting and user-defined log-level."""

import logging

import colorlog
from colorlog import ColoredFormatter

__log_level = logging.NOTSET


formatter = ColoredFormatter(
    "%(asctime)s %(log_color)s%(levelname)s%(fg_white)s:%(name)s: %(log_color)s%(message)s",
    reset=True,
    style="%",
)


def set_logging_level(log_level: int):
    """Set the log level which is ued when calling `get_logger`."""
    global __log_level
    __log_level = log_level


def update_log_level(logger: logging.Logger) -> logging.Logger:
    """Update the logging level of a logger at runtime to the global value of this module."""
    logger.setLevel(__log_level)
    return logger


def get_logger(name: str | None):
    """
    Get a pre-configured logger.

    :param: name of the logger, if None the root logger is used
    :return: pre-configured logger
    """
    handler = colorlog.StreamHandler()
    handler.setFormatter(formatter)
    logger = logging.getLogger(name)
    logger.addHandler(handler)
    logger.setLevel(__log_level)
    return logger
