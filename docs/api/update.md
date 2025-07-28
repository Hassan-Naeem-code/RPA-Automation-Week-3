# Data Update Module

The `update.py` module handles data persistence and output generation in multiple formats.

## Functions

### `update_inventory(data: List[Dict]) -> None`

Updates inventory data and generates output files in multiple formats.

**Parameters:**
- `data`: List of processed inventory records to persist

**Output Files Generated:**
- **CSV**: `processed_inventory.csv`
- **Excel**: `processed_inventory.xlsx`
- **JSON**: `processed_inventory.json`
- **Report**: `inventory_report.txt`

## Features

- **Multi-Format Output**: Supports CSV, Excel, JSON, and text formats
- **Timestamped Backups**: Creates archival copies with timestamps
- **Data Integrity**: Ensures data consistency across all formats
- **Error Recovery**: Robust error handling and recovery mechanisms

## Usage Example

```python
from src.update import update_inventory
from src.process import process_data
from src.extract import extract_data

# Complete workflow
raw_data = extract_data()
processed_data = process_data(raw_data)
update_inventory(processed_data)
print("Inventory updated successfully")
```

## Recent Updates

**Fixed Critical Bug**: Resolved `NameError: 'df' not defined` issue by correcting variable references in the `update_inventory` method.

## Performance Metrics

- **Write Speed**: Optimized for large datasets
- **Format Support**: Native support for multiple output formats
- **Backup Strategy**: Automatic timestamped backup creation
- **Recovery**: Built-in error recovery and rollback capabilities
