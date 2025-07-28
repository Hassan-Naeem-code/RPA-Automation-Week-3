"""
Intelligent Configuration Management System for RPA Inventory Management

This module provides dynamic configuration management, environment-specific settings,
and intelligent parameter optimization.

Author: Hassan Naeem
Date: July 2025
"""

import json
import yaml
import os
from pathlib import Path
from typing import Dict, Any, Union, List, Optional
import logging
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum

logger = logging.getLogger(__name__)


class ConfigFormat(Enum):
    """Supported configuration file formats."""

    JSON = "json"
    YAML = "yaml"
    ENV = "env"


class Environment(Enum):
    """Deployment environments."""

    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class EmailConfig:
    """Email configuration settings."""

    smtp_server: str = "smtp.gmail.com"
    smtp_port: int = 587
    sender_email: str = ""
    sender_password: str = ""
    recipients: Optional[List[str]] = None
    enable_tls: bool = True
    timeout: int = 30
    retry_attempts: int = 3

    def __post_init__(self):
        if self.recipients is None:
            self.recipients = []


@dataclass
class ProcessingConfig:
    """Data processing configuration."""

    batch_size: int = 1000
    max_file_size_mb: int = 100
    supported_formats: Optional[List[str]] = None
    duplicate_handling: str = "keep_latest"  # keep_latest, keep_first, combine
    validation_level: str = "strict"  # strict, moderate, lenient
    enable_backups: bool = True
    backup_retention_days: int = 30

    def __post_init__(self):
        if self.supported_formats is None:
            self.supported_formats = ["csv", "xlsx", "xls"]


@dataclass
class AlertConfig:
    """Alert system configuration."""

    critical_threshold: int = 5
    low_stock_threshold_percent: float = 20.0
    high_value_threshold: float = 1000.0
    enable_email_alerts: bool = True
    enable_console_alerts: bool = True
    enable_file_logging: bool = True
    alert_frequency: str = "immediate"  # immediate, hourly, daily
    consolidate_alerts: bool = False


@dataclass
class PerformanceConfig:
    """Performance monitoring configuration."""

    enable_metrics: bool = True
    metrics_retention_days: int = 90
    performance_baseline_minutes: float = 45.0
    target_processing_time_seconds: float = 60.0
    memory_limit_mb: int = 512
    enable_profiling: bool = False
    log_level: str = "INFO"


@dataclass
class SecurityConfig:
    """Security and privacy configuration."""

    encrypt_sensitive_data: bool = True
    mask_personal_info: bool = True
    audit_trail: bool = True
    max_login_attempts: int = 3
    session_timeout_minutes: int = 30
    require_ssl: bool = True
    api_rate_limit: int = 100  # requests per minute


class SmartConfigManager:
    """
    Intelligent configuration management system with environment-specific settings,
    automatic validation, and dynamic parameter optimization.
    """

    def __init__(
        self, config_dir: str = "config", environment: Optional[Environment] = None
    ):
        """
        Initialize the configuration manager.

        Args:
            config_dir: Directory containing configuration files
            environment: Target environment (auto-detected if None)
        """
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)

        self.environment = environment or self._detect_environment()
        self.config: Dict[str, Any] = {}
        self.schema: Dict[str, Any] = {}
        self.watchers: List[Any] = []

        logger.info(
            f"SmartConfigManager initialized for {self.environment.value} environment"
        )

        # Load configuration
        self._load_default_config()
        self._load_environment_config()
        self._apply_environment_overrides()

    def _detect_environment(self) -> Environment:
        """Auto-detect the current environment."""
        env_var = os.getenv("RPA_ENVIRONMENT", "").lower()

        if env_var in ["prod", "production"]:
            return Environment.PRODUCTION
        elif env_var in ["staging", "stage"]:
            return Environment.STAGING
        elif env_var in ["test", "testing"]:
            return Environment.TESTING
        else:
            return Environment.DEVELOPMENT

    def _load_default_config(self):
        """Load default configuration settings."""
        self.config = {
            "email": asdict(EmailConfig()),
            "processing": asdict(ProcessingConfig()),
            "alerts": asdict(AlertConfig()),
            "performance": asdict(PerformanceConfig()),
            "security": asdict(SecurityConfig()),
            "general": {
                "app_name": "RPA Inventory Management System",
                "version": "2.0.0",
                "author": "Hassan Naeem",
                "created_date": datetime.now().isoformat(),
                "debug_mode": self.environment == Environment.DEVELOPMENT,
                "data_directory": "data",
                "log_directory": "logs",
                "output_directory": "data/processed",
                "archive_directory": "data/archive",
            },
        }

        logger.info("Default configuration loaded")

    def _load_environment_config(self):
        """Load environment-specific configuration."""
        config_file = self.config_dir / f"{self.environment.value}.yaml"

        if config_file.exists():
            try:
                with open(config_file, "r") as f:
                    env_config = yaml.safe_load(f)

                # Deep merge with default config
                self.config = self._deep_merge(self.config, env_config)
                logger.info(f"Environment configuration loaded from {config_file}")

            except Exception as e:
                logger.warning(f"Failed to load environment config: {e}")
        else:
            # Create default environment config file
            self._create_default_env_config(config_file)

    def _apply_environment_overrides(self):
        """Apply environment variable overrides."""
        overrides = {
            "RPA_EMAIL_SERVER": ("email", "smtp_server"),
            "RPA_EMAIL_PORT": ("email", "smtp_port"),
            "RPA_EMAIL_USER": ("email", "sender_email"),
            "RPA_EMAIL_PASS": ("email", "sender_password"),
            "RPA_BATCH_SIZE": ("processing", "batch_size"),
            "RPA_LOG_LEVEL": ("performance", "log_level"),
            "RPA_DEBUG": ("general", "debug_mode"),
        }

        for env_var, (section, key) in overrides.items():
            value = os.getenv(env_var)
            if value is not None:
                # Type conversion
                if key in ["smtp_port", "batch_size"]:
                    value = int(value)
                elif key == "debug_mode":
                    value = value.lower() in ["true", "1", "yes", "on"]

                self.config[section][key] = value
                logger.info(
                    f"Applied environment override: {env_var} -> {section}.{key}"
                )

    def _deep_merge(self, base: Dict, override: Dict) -> Dict:
        """Deep merge two dictionaries."""
        result = base.copy()

        for key, value in override.items():
            if (
                key in result
                and isinstance(result[key], dict)
                and isinstance(value, dict)
            ):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def _create_default_env_config(self, config_file: Path):
        """Create a default environment configuration file."""
        env_specific_config = {}

        if self.environment == Environment.PRODUCTION:
            env_specific_config = {
                "general": {"debug_mode": False},
                "performance": {"log_level": "WARNING", "enable_profiling": False},
                "security": {"encrypt_sensitive_data": True, "require_ssl": True},
                "alerts": {"alert_frequency": "immediate", "consolidate_alerts": True},
            }
        elif self.environment == Environment.DEVELOPMENT:
            env_specific_config = {
                "general": {"debug_mode": True},
                "performance": {"log_level": "DEBUG", "enable_profiling": True},
                "processing": {"batch_size": 100},  # Smaller batches for testing
            }

        try:
            with open(config_file, "w") as f:
                yaml.dump(env_specific_config, f, default_flow_style=False)
            logger.info(f"Created default environment config: {config_file}")
        except Exception as e:
            logger.error(f"Failed to create environment config: {e}")

    def get(self, key: str, default: Any = None) -> Any:
        """
        Get a configuration value using dot notation.

        Args:
            key: Configuration key in dot notation (e.g., 'email.smtp_server')
            default: Default value if key is not found

        Returns:
            Configuration value or default
        """
        keys = key.split(".")
        value = self.config

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default

    def set(self, key: str, value: Any, persist: bool = False):
        """
        Set a configuration value using dot notation.

        Args:
            key: Configuration key in dot notation
            value: Value to set
            persist: Whether to save the change to file
        """
        keys = key.split(".")
        config = self.config

        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        # Set the value
        old_value = config.get(keys[-1])
        config[keys[-1]] = value

        logger.info(f"Configuration updated: {key} = {value} (was: {old_value})")

        if persist:
            self.save_config()

        # Notify watchers
        self._notify_watchers(key, value, old_value)

    def validate_config(self) -> Dict[str, List[str]]:
        """
        Validate the current configuration.

        Returns:
            Dictionary of validation errors by section
        """
        errors = {}

        # Email validation
        email_errors = []
        if not self.get("email.sender_email"):
            email_errors.append("sender_email is required")
        if not self.get("email.sender_password"):
            email_errors.append("sender_password is required")
        if not self.get("email.recipients"):
            email_errors.append("At least one recipient is required")

        if email_errors:
            errors["email"] = email_errors

        # Processing validation
        processing_errors = []
        batch_size = self.get("processing.batch_size", 0)
        if batch_size <= 0:
            processing_errors.append("batch_size must be positive")

        max_file_size = self.get("processing.max_file_size_mb", 0)
        if max_file_size <= 0:
            processing_errors.append("max_file_size_mb must be positive")

        if processing_errors:
            errors["processing"] = processing_errors

        # Performance validation
        perf_errors = []
        memory_limit = self.get("performance.memory_limit_mb", 0)
        if memory_limit < 128:
            perf_errors.append("memory_limit_mb should be at least 128MB")

        if perf_errors:
            errors["performance"] = perf_errors

        if not errors:
            logger.info("Configuration validation passed")
        else:
            logger.warning(f"Configuration validation found {len(errors)} issues")

        return errors

    def optimize_for_environment(self):
        """Automatically optimize configuration for the current environment."""
        optimizations = []

        if self.environment == Environment.PRODUCTION:
            # Production optimizations
            if self.get("general.debug_mode", True):
                self.set("general.debug_mode", False)
                optimizations.append("Disabled debug mode for production")

            if self.get("performance.log_level") == "DEBUG":
                self.set("performance.log_level", "WARNING")
                optimizations.append("Set log level to WARNING for production")

            if not self.get("security.encrypt_sensitive_data", False):
                self.set("security.encrypt_sensitive_data", True)
                optimizations.append("Enabled sensitive data encryption")

        elif self.environment == Environment.DEVELOPMENT:
            # Development optimizations
            if not self.get("general.debug_mode", False):
                self.set("general.debug_mode", True)
                optimizations.append("Enabled debug mode for development")

            if self.get("processing.batch_size", 1000) > 500:
                self.set("processing.batch_size", 100)
                optimizations.append("Reduced batch size for development testing")

        if optimizations:
            logger.info(f"Applied {len(optimizations)} environment optimizations")
            for opt in optimizations:
                logger.info(f"  - {opt}")

        return optimizations

    def save_config(self, format_type: ConfigFormat = ConfigFormat.YAML):
        """Save current configuration to file."""
        config_file = self.config_dir / f"current.{format_type.value}"

        try:
            with open(config_file, "w") as f:
                if format_type == ConfigFormat.JSON:
                    json.dump(self.config, f, indent=2, default=str)
                elif format_type == ConfigFormat.YAML:
                    yaml.dump(self.config, f, default_flow_style=False)

            logger.info(f"Configuration saved to {config_file}")

        except Exception as e:
            logger.error(f"Failed to save configuration: {e}")

    def load_config(self, config_file: Union[str, Path]):
        """Load configuration from file."""
        config_file = Path(config_file)

        if not config_file.exists():
            logger.error(f"Configuration file not found: {config_file}")
            return False

        try:
            with open(config_file, "r") as f:
                if config_file.suffix.lower() == ".json":
                    loaded_config = json.load(f)
                else:
                    loaded_config = yaml.safe_load(f)

            self.config = self._deep_merge(self.config, loaded_config)
            logger.info(f"Configuration loaded from {config_file}")
            return True

        except Exception as e:
            logger.error(f"Failed to load configuration: {e}")
            return False

    def add_watcher(self, callback):
        """Add a configuration change watcher."""
        self.watchers.append(callback)
        logger.info("Configuration watcher added")

    def _notify_watchers(self, key: str, new_value: Any, old_value: Any):
        """Notify all watchers of configuration changes."""
        for watcher in self.watchers:
            try:
                watcher(key, new_value, old_value)
            except Exception as e:
                logger.error(f"Error in configuration watcher: {e}")

    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the current configuration."""
        return {
            "environment": self.environment.value,
            "config_sections": list(self.config.keys()),
            "total_settings": sum(
                len(section) if isinstance(section, dict) else 1
                for section in self.config.values()
            ),
            "validation_status": (
                "valid" if not self.validate_config() else "has_errors"
            ),
            "last_modified": datetime.now().isoformat(),
        }

    def export_template(self, include_sensitive: bool = False) -> Dict[str, Any]:
        """Export configuration as a template for other environments."""
        template: Dict[str, Any] = {}

        for section, settings in self.config.items():
            if isinstance(settings, dict):
                template[section] = {}
                for key, value in settings.items():
                    # Skip sensitive values unless explicitly included
                    if not include_sensitive and any(
                        sensitive in key.lower()
                        for sensitive in ["password", "key", "secret", "token"]
                    ):
                        template[section][key] = "<REDACTED>"
                    else:
                        template[section][key] = value
            else:
                template[section] = settings

        return template


# Configuration factory for easy access
def create_config_manager(environment: Optional[str] = None) -> SmartConfigManager:
    """Factory function to create a configuration manager."""
    env = None
    if environment:
        env = Environment(environment.lower())

    return SmartConfigManager(environment=env)


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # Create configuration manager
    config = create_config_manager()

    # Print configuration summary
    print("Configuration Summary:")
    print(json.dumps(config.get_summary(), indent=2))

    # Optimize for environment
    optimizations = config.optimize_for_environment()
    print(f"\nApplied {len(optimizations)} optimizations:")
    for opt in optimizations:
        print(f"  - {opt}")

    # Validate configuration
    errors = config.validate_config()
    if errors:
        print("\nConfiguration Errors:")
        for section, section_errors in errors.items():
            print(f"  {section}:")
            for error in section_errors:
                print(f"    - {error}")
    else:
        print("\n✅ Configuration is valid!")

    # Save configuration
    config.save_config()
    print("\nConfiguration saved successfully!")
