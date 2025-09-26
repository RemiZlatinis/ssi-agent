import logging.config
from importlib.metadata import PackageNotFoundError, version

import sentry_sdk
from sentry_sdk.integrations.logging import LoggingIntegration

from .constants import LOG_DIR, PUBLIC_DSN

try:
    # Get version from installed package metadata
    release_version = version("ssi-agent")
except PackageNotFoundError:
    # Fallback for when the package is not installed (e.g., in development)
    release_version = "dev"

# Initialize Sentry/BugSink first
# (before configuring Python logging, to ensure integration captures everything)
sentry_sdk.init(
    PUBLIC_DSN,
    integrations=[
        LoggingIntegration(
            # Capture INFO and above as breadcrumbs (contextual info)
            level=logging.INFO,
            # Send ERROR and above as full events to BugSink
            event_level=logging.ERROR,
        )
    ],
    send_default_pii=False,  # Personally Identifiable Information
    max_request_body_size="always",
    traces_sample_rate=0,
    release=release_version,
    environment="production",
)

logging_config = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "%(asctime)s - %(levelname)s - %(message)s",
        },
        "detailed": {
            "format": "%(asctime)s - "
            "%(name)s - %(levelname)s - "
            "%(module)s:%(lineno)d - %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "WARNING",
            "formatter": "simple",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": LOG_DIR / "_agent.log",
            "maxBytes": 10_485_760,  # 10MB
            "backupCount": 5,
            "encoding": "utf8",
        },
    },
    "loggers": {
        "daemon": {
            "level": "DEBUG",
            "handlers": ["console", "file"],
            "propagate": False,
        },
    },
}

logging.config.dictConfig(config=logging_config)
daemon_logger = logging.getLogger("daemon")
