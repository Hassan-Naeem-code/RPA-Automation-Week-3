# Configuration Manager Module

The `config_manager.py` module handles system configuration management and environment settings.

## Functions

### `load_config() -> Dict[str, Any]`

Loads system configuration from various sources.

**Returns:**
- `Dict[str, Any]`: Complete system configuration dictionary

### `get_setting(key: str, default: Any = None) -> Any`

Retrieves a specific configuration setting.

**Parameters:**
- `key`: Configuration key to retrieve
- `default`: Default value if key not found

**Returns:**
- `Any`: Configuration value or default

## Configuration Sources

### File-based Configuration
- **YAML Files**: Primary configuration format
- **JSON Files**: Alternative configuration format
- **INI Files**: Legacy configuration support
- **Environment Variables**: Runtime configuration overrides

### Dynamic Configuration
- **Runtime Updates**: Live configuration updates
- **Remote Configuration**: Configuration from remote sources
- **Database Configuration**: Configuration stored in database
- **API Configuration**: Configuration via REST API

## Configuration Categories

### System Settings
- **Database Configuration**: Connection strings and settings
- **API Endpoints**: Service endpoint configurations
- **Security Settings**: Authentication and authorization settings
- **Logging Configuration**: Log levels and output settings

### Business Settings
- **Processing Rules**: Business logic configuration
- **Thresholds**: Alert and processing thresholds
- **Schedules**: Automated task scheduling
- **Integration Settings**: Third-party integration settings

## Features

- **Hot Reload**: Configuration changes without restart
- **Validation**: Configuration validation and verification
- **Encryption**: Sensitive configuration encryption
- **Versioning**: Configuration version management

## Usage Example

```python
from src.config_manager import load_config, get_setting

# Load complete configuration
config = load_config()

# Get specific settings
db_host = get_setting("database.host", "localhost")
api_timeout = get_setting("api.timeout", 30)
log_level = get_setting("logging.level", "INFO")

print(f"Database host: {db_host}")
print(f"API timeout: {api_timeout}s")
```

## Environment Support

The module supports multiple environments:
- Development
- Testing
- Staging
- Production

## Security

Configuration security features include:
- Encrypted sensitive values
- Access control for configuration files
- Audit logging for configuration changes
- Secret management integration
