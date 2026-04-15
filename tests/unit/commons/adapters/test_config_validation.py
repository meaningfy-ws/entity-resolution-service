import logging

import pytest

from ers import ERSConfigResolver
from ers.commons.adapters.config_validation import (
    INSECURE_DEFAULTS,
    InsecureConfigurationError,
    validate_production_config,
)


class TestValidateProductionConfig:
    def test_production_with_insecure_defaults_raises(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "production")
        config = ERSConfigResolver()

        with pytest.raises(InsecureConfigurationError) as exc_info:
            validate_production_config(config)

        msg = str(exc_info.value)
        assert "JWT_SECRET_KEY" in msg
        assert "ADMIN_PASSWORD" in msg

    def test_production_with_all_secure_values_passes(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("JWT_SECRET_KEY", "a-real-secret-key-that-is-secure")
        monkeypatch.setenv("ADMIN_PASSWORD", "Str0ng!P@ssw0rd")
        monkeypatch.setenv("ADMIN_EMAIL", "admin@company.com")
        config = ERSConfigResolver()

        validate_production_config(config)  # should not raise

    def test_production_lists_all_offending_properties(self, monkeypatch):
        monkeypatch.setenv("ENVIRONMENT", "production")
        # Override only JWT — the rest stay insecure
        monkeypatch.setenv("JWT_SECRET_KEY", "a-real-secret-key")
        config = ERSConfigResolver()

        with pytest.raises(InsecureConfigurationError) as exc_info:
            validate_production_config(config)

        msg = str(exc_info.value)
        assert "JWT_SECRET_KEY" not in msg
        assert "ADMIN_PASSWORD" in msg
        assert "ADMIN_EMAIL" in msg

    def test_development_with_insecure_defaults_warns_only(self, monkeypatch, caplog):
        monkeypatch.setenv("ENVIRONMENT", "development")
        config = ERSConfigResolver()

        with caplog.at_level(logging.WARNING):
            validate_production_config(config)  # should not raise

        assert "Insecure default values detected" in caplog.text
        assert "development" in caplog.text

    def test_development_with_all_secure_values_no_warning(self, monkeypatch, caplog):
        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.setenv("JWT_SECRET_KEY", "a-real-secret-key")
        monkeypatch.setenv("ADMIN_PASSWORD", "Str0ng!P@ssw0rd")
        monkeypatch.setenv("ADMIN_EMAIL", "admin@company.com")
        config = ERSConfigResolver()

        with caplog.at_level(logging.WARNING):
            validate_production_config(config)

        assert "Insecure default values" not in caplog.text

    def test_insecure_configuration_error_is_system_exit(self):
        assert issubclass(InsecureConfigurationError, SystemExit)

    def test_insecure_defaults_match_actual_config_defaults(self, monkeypatch):
        """Guard against drift between _INSECURE_DEFAULTS and the real config defaults."""
        for name in INSECURE_DEFAULTS:
            monkeypatch.delenv(name, raising=False)

        config = ERSConfigResolver()
        for name, expected in INSECURE_DEFAULTS.items():
            actual = getattr(config, name)
            assert actual == expected, (
                f"_INSECURE_DEFAULTS[{name!r}] is {expected!r} but the config "
                f"default resolved to {actual!r} — update one to match the other"
            )
