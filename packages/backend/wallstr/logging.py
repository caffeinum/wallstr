import logging
import logging.config
import sys
from collections.abc import Iterable
from typing import Any, cast

import structlog
import uvicorn
from structlog.dev import DIM, RESET_ALL, ConsoleRenderer, Styles, plain_traceback
from structlog.stdlib import _FixedFindCallerLogger
from structlog.typing import EventDict, Processor, WrappedLogger

TRACE = 5

if not sys.warnoptions:
    import warnings

    # crypt is required by passlib
    warnings.filterwarnings(
        "ignore",
        category=DeprecationWarning,
        message="'crypt' is deprecated and slated for removal in Python 3.13",
    )


def truncate_log_event(
    _: WrappedLogger, method_name: str, event_dict: EventDict
) -> EventDict:
    if method_name in ["error", "critical", "exception"]:
        return event_dict
    MAX_EVENT_LEN = 80
    event = event_dict.get("event", "")
    if len(event) > (MAX_EVENT_LEN + 20):
        event_dict["event"] = (
            f"{event[:MAX_EVENT_LEN]}...{event[-20:]} [{len(event)} symbols]"
        )
    return event_dict


"""
https://www.structlog.org/en/stable/standard-library.html#rendering-within-structlog
"""
processors: Iterable[Processor] = [
    structlog.contextvars.merge_contextvars,
    structlog.stdlib.add_log_level,
    structlog.stdlib.add_logger_name,
    structlog.stdlib.PositionalArgumentsFormatter(),
    structlog.processors.StackInfoRenderer(),
    structlog.dev.set_exc_info,
    # structlog.processors.TimeStamper(fmt="%Y-%m-%d %H:%M:%S", utc=False),
    structlog.processors.TimeStamper(fmt="%H:%M:%S", utc=False),
    # truncate_log_event,
]

styles = {
    **ConsoleRenderer.get_default_level_styles(),
    "debug": RESET_ALL,
    "trace": DIM,
}

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "console": {
            "()": structlog.stdlib.ProcessorFormatter,
            "foreign_pre_chain": processors,
            "processors": [
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                structlog.dev.ConsoleRenderer(
                    level_styles=cast(Styles, styles),  # structlog bug
                    exception_formatter=plain_traceback,
                ),
            ],
        },
        "access1": {
            "()": structlog.stdlib.ProcessorFormatter,
            "foreign_pre_chain": [
                uvicorn.logging.AccessFormatter.formatMessage,
                *processors,
            ],
            "processors": [
                structlog.stdlib.ProcessorFormatter.remove_processors_meta,
                structlog.dev.ConsoleRenderer(
                    level_styles=cast(Styles, styles),  # structlog bug
                    exception_formatter=plain_traceback,
                ),
            ],
        },
        "access": {"()": uvicorn.logging.AccessFormatter},
    },
    "handlers": {
        "default": {
            "level": "NOTSET",
            "class": "logging.StreamHandler",
            "formatter": "console",
        },
        "access": {
            "level": "NOTSET",
            "class": "logging.StreamHandler",
            "formatter": "access",
        },
    },
    "loggers": {
        "root": {
            "handlers": ["default"],
            "level": "NOTSET",
        },
        "authlib": {"level": "DEBUG"},
        "uvicorn": {"level": "DEBUG"},
        "uvicorn.access": {
            "level": "DEBUG",
            "handlers": ["access"],
            "propagate": False,
        },
        "botocore": {"level": "INFO"},
        "pika": {"level": "WARNING"},
    },
}


class CustomLogger(_FixedFindCallerLogger):
    def trace(self: logging.Logger, message: str, *args: Any, **kwargs: Any) -> None:
        if self.isEnabledFor(TRACE):
            self._log(TRACE, message, args, **kwargs)


def configure_logging() -> None:
    logging.addLevelName(TRACE, "TRACE")

    logging.config.dictConfig(LOGGING_CONFIG)

    structlog.configure(
        processors=[
            *processors,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        wrapper_class=structlog.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    logging.setLoggerClass(CustomLogger)
