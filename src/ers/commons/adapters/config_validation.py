"""Startup validation that blocks insecure default secrets in production."""

import logging

logger = logging.getLogger(__name__)

_INSECURE_DEFAULTS: dict[str, str] = {
    "JWT_SECRET_KEY": "change-me-in-production",
    "ADMIN_PASSWORD": "changeme",
    "ADMIN_EMAIL": "admin@ers.local",
}


class InsecureConfigurationError(SystemExit):
    """Raised when production starts with known insecure default values.

    Inherits ``SystemExit`` so it cannot be swallowed by broad
    ``except Exception`` handlers in framework internals.
    """


def validate_production_config(config: object) -> None:
    """Check config properties against a blocklist of known insecure defaults.

    Args:
        config: The application config object (``ERSConfigResolver`` instance).

    Raises:
        InsecureConfigurationError: If any insecure defaults are detected and
            ``ENVIRONMENT`` is ``"production"``.
    """
    violations = [
        name
        for name, insecure_value in _INSECURE_DEFAULTS.items()
        if getattr(config, name) == insecure_value
    ]
    if not violations:
        return

    environment = config.ENVIRONMENT

    if environment == "production":
        listing = ", ".join(violations)
        raise InsecureConfigurationError(
            f"Insecure default values detected in production for: {listing}. "
            f"Set these environment variables to secure values, or set "
            f"ENVIRONMENT=development for local development."
        )

    logger.warning(
        "Insecure default values detected for: %s. "
        "This is acceptable in '%s' but must be fixed before production.",
        ", ".join(violations),
        environment,
    )
