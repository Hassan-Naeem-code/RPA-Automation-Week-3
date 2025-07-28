# Alert System Module

The `alert.py` module provides notification and alerting capabilities for the RPA inventory management system.

## Functions

### `send_alert(message: str, level: str = "info") -> None`

Sends alerts and notifications based on system events and thresholds.

**Parameters:**
- `message`: Alert message content
- `level`: Alert severity level ("info", "warning", "error", "critical")

## Alert Types

- **System Alerts**: Infrastructure and system-level notifications
- **Data Alerts**: Data quality and processing notifications
- **Performance Alerts**: Performance threshold notifications
- **Error Alerts**: Exception and error notifications

## Features

- **Multi-Channel Support**: Email, SMS, webhook notifications
- **Severity Levels**: Configurable alert severity levels
- **Rate Limiting**: Prevents alert flooding
- **Template Support**: Customizable alert templates

## Usage Example

```python
from src.alert import send_alert

# Send different types of alerts
send_alert("Inventory processing completed", "info")
send_alert("Data quality threshold exceeded", "warning")
send_alert("Critical system error detected", "critical")
```

## Configuration

Alerts can be configured through the system configuration to customize:
- Notification channels
- Alert thresholds
- Message templates
- Recipient lists
