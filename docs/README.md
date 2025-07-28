# RPA Inventory Management System

A comprehensive Python-based Robotic Process Automation (RPA) solution for automated inventory management, designed to replace manual Excel-based inventory tracking with intelligent, error-reducing automation.

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Installation](#installation)
- [Configuration](#configuration)
- [Usage](#usage)
- [Data Assumptions](#data-assumptions)
- [Modules](#modules)
- [Performance Metrics](#performance-metrics)
- [Testing](#testing)
- [Contributing](#contributing)
- [License](#license)

## Overview

Retail Innovations Inc.'s inventory management was previously handled manually through Excel spreadsheets, leading to frequent errors, delays, and out-of-stock situations. This RPA solution automates the entire workflow from data extraction to alert generation, providing:

- **90%+ runtime reduction** compared to manual processes
- **80%+ error elimination** through automated validation
- **Real-time alerts** for low stock and critical inventory levels
- **Comprehensive reporting** with business intelligence metrics

## Features

### Core Functionality
- **Automated Data Extraction**: Supports CSV, Excel, and extensible to other formats
- **Intelligent Data Processing**: Cleaning, validation, and business rule application
- **Multi-format Output**: CSV, Excel (formatted), and JSON export options
- **Smart Alerting**: Email notifications with HTML formatting and attachments
- **Performance Tracking**: Comprehensive metrics and KPI monitoring

### Business Intelligence
- **Low Stock Detection**: Configurable thresholds and reorder calculations
- **Critical Item Identification**: Priority alerts for high-value items
- **Data Quality Scoring**: Automated quality assessment and violation reporting
- **Trend Analysis**: Historical performance tracking and improvement metrics

### Enterprise Features
- **API Integration**: RESTful API support for external system updates
- **Configurable Workflows**: Environment-based configuration management
- **Comprehensive Logging**: Structured logging with multiple output formats
- **Error Handling**: Robust error management with detailed reporting
- **Backup Management**: Automated data backup with timestamping

## 🏗️ Architecture

The system follows a modular, pipeline-based architecture:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Data Source   │───▶│   Extraction    │───▶│   Processing    │───▶│     Update      │
│  (CSV/Excel)    │    │    Module       │    │     Module      │    │     Module      │
└─────────────────┘    └─────────────────┘    └─────────────────┘    └─────────────────┘
                                                        │
                       ┌─────────────────┐              │
                       │     Alert       │◀─────────────┘
                       │     Module      │
                       └─────────────────┘
                                │
                       ┌─────────────────┐
                       │    Metrics      │
                       │     Module      │
                       └─────────────────┘
```

### Module Responsibilities

- **`main.py`**: Orchestrates the complete workflow with command-line interface
- **`src/extract.py`**: Handles data extraction from various sources
- **`src/process.py`**: Performs data cleaning, validation, and business logic
- **`src/update.py`**: Manages data output and external system integration
- **`src/alert.py`**: Generates and sends notifications and reports
- **`src/metrics.py`**: Tracks performance and calculates KPIs

## 📦 Installation

### Prerequisites

- Python 3.11 or higher
- pip package manager
- Git (for version control)

### Quick Setup

1. **Clone the repository**:
   ```bash
   git clone https://github.com/Hassan-Naeem-code/RPA-Automation-Week-3.git
   cd RPA-Automation-Week-3
   ```

2. **Create virtual environment**:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
   ```

3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

4. **Generate synthetic test data**:
   ```bash
   python generate_fake_inventory.py
   ```

5. **Configure environment** (optional):
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

### Development Setup

For development with testing capabilities:

```bash
pip install -r requirements.txt
pip install pytest pytest-cov black flake8
```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```env
# Email Configuration
SMTP_SERVER=smtp.gmail.com
SMTP_PORT=587
EMAIL_USER=your_email@gmail.com
EMAIL_PASSWORD=your_app_password
ALERT_RECIPIENTS=manager@company.com,inventory@company.com

# Business Rules
LOW_STOCK_MULTIPLIER=1.2
CRITICAL_STOCK_THRESHOLD=5

# System Settings
LOG_LEVEL=INFO
MAX_RETRIES=3
TIMEOUT_SECONDS=30
```

### Configuration File

Alternatively, use a JSON configuration file:

```json
{
  \"email_user\": \"alerts@company.com\",
  \"alert_recipients\": [\"manager@company.com\"],
  \"low_stock_multiplier\": 1.2,
  \"critical_stock_threshold\": 5,
  \"api_url\": \"https://api.company.com/inventory\"
}
```

## 🚀 Usage

### Basic Usage

Process inventory data with default settings:

```bash
python main.py --input data/inventory_raw.csv
```

### Advanced Usage

```bash
# Custom output directory and configuration
python main.py --input data/inventory_raw.csv --output results/ --config config.json

# Debug mode with detailed logging
python main.py --input data/inventory_raw.csv --log-level DEBUG

# Disable alerts and backups
python main.py --input data/inventory_raw.csv --no-alerts --no-backup
```

### Command-Line Options

```
Required Arguments:
  --input, -i          Path to input inventory CSV/Excel file

Optional Arguments:
  --output, -o         Output directory (default: data/processed)
  --config, -c         Path to configuration JSON file
  --log-level          Logging level: DEBUG, INFO, WARNING, ERROR, CRITICAL
  --log-file           Path to log file (default: logs/rpa_run.log)
  --send-alerts        Send email alerts (default: True)
  --no-alerts          Disable email alerts
  --no-backup          Disable automatic backup creation
  --version            Show version information
```

### Output Files

The system generates several output files:

- `inventory_processed.csv`: Clean data in CSV format
- `inventory_processed.xlsx`: Formatted Excel file with conditional formatting
- `inventory_processed.json`: JSON format for API integration
- `processing_report.json`: Detailed processing summary and violations
- `logs/alerts.log`: Alert history and notifications
- `logs/rpa_run.log`: Complete system logs
- `backups/inventory_backup_[timestamp].csv`: Timestamped backups

## 📊 Data Assumptions

The synthetic data generator creates realistic test scenarios including:

### Standard Data Structure
```csv
SKU,Description,Location,OnHandQty,ReorderPoint,UnitCost
SKU00001,Sample Item,WH1,150,50,25.99
```

### Edge Cases for Testing
- **Negative Quantities**: Simulates data entry errors
- **Duplicate SKUs**: Tests deduplication logic
- **Empty Descriptions**: Validates data cleaning
- **High-Value Items**: Tests priority alerting

### Business Rules Applied
- Quantities < 0 are treated as 0
- Reorder Quantity = max(0, ReorderPoint - OnHandQty)
- Stock Status: Normal | Low Stock | Critical | Out of Stock
- Data quality scoring based on completeness and accuracy

## 🔧 Modules

### Extract Module (`src/extract.py`)
```python
from src.extract import extract_inventory_data

# Extract data from CSV
df = extract_inventory_data('data/inventory_raw.csv')
```

**Features**:
- Multi-format support (CSV, Excel)
- File validation and error handling
- Extensible architecture for new formats

### Process Module (`src/process.py`)
```python
from src.process import process_inventory_data

# Process and clean data
processed_df, stats, violations = process_inventory_data(raw_df)
```

**Features**:
- Data cleaning and normalization
- Business rule validation
- Reorder calculations and stock status
- Quality scoring

### Update Module (`src/update.py`)
```python
from src.update import update_inventory_data

# Save processed data
results = update_inventory_data(df, stats, violations, 
                               output_formats=['csv', 'excel', 'json'])
```

**Features**:
- Multiple output formats
- Excel formatting with conditional colors
- API integration capabilities
- Automated backup creation

### Alert Module (`src/alert.py`)
```python
from src.alert import send_inventory_alerts

# Send alerts for low stock items
alert_results = send_inventory_alerts(df, stats, config)
```

**Features**:
- HTML email formatting
- Priority-based alerting
- Multiple notification channels
- Alert history logging

### Metrics Module (`src/metrics.py`)
```python
from src.metrics import MetricsCollector

# Track performance metrics
collector = MetricsCollector()
collector.start_session()
# ... processing ...
collector.end_session()
metrics = collector.generate_metrics_summary()
```

**Features**:
- Performance tracking
- KPI calculation
- ROI measurement
- Trend analysis

## 📈 Performance Metrics

### Key Performance Indicators (KPIs)

| Metric | Baseline (Manual) | Target (Automated) | Typical Achievement |
|--------|-------------------|-------------------|-------------------|
| Processing Time | 45 minutes | < 1 minute | 30-45 seconds |
| Error Rate | 15% | < 2% | < 1% |
| Cost per Process | $18.75 | < $1.00 | $0.25 |
| Data Quality Score | 70% | > 95% | 97-99% |

### Success Metrics Tracked

- **Runtime Efficiency**: Actual vs. target processing time
- **Error Reduction**: Comparison to manual error rates
- **Cost Savings**: Labor cost reduction calculations
- **Throughput**: Records processed per second/minute
- **ROI**: Return on investment percentage
- **Data Quality**: Automated quality scoring

## 🧪 Testing

### Unit Tests

Run the test suite:

```bash
pytest tests/ -v
pytest tests/ --cov=src --cov-report=html
```

### Sample Test Execution

```bash
# Test with synthetic data
python generate_fake_inventory.py
python main.py --input data/inventory_raw.csv --log-level DEBUG

# Verify outputs
ls -la data/processed/
cat logs/rpa_run.log
```

### Test Data Generation

The system includes comprehensive test data generation:

```python
# Generate test data with edge cases
python generate_fake_inventory.py

# Creates:
# - 500+ inventory records
# - Duplicate SKUs for testing
# - Negative quantities
# - Missing descriptions
# - Various stock levels
```

## 📝 Logging

### Log Levels and Outputs

- **DEBUG**: Detailed execution information
- **INFO**: General process information (default)
- **WARNING**: Non-critical issues
- **ERROR**: Error conditions
- **CRITICAL**: System failures

### Log Files

- `logs/rpa_run.log`: Main application logs
- `logs/alerts.log`: Alert-specific logs  
- `logs/metrics.json`: Performance metrics
- Console output for real-time monitoring

## 🔄 Continuous Improvement

### Monitoring and Optimization

1. **Performance Monitoring**: Track runtime and error trends
2. **Business Rule Tuning**: Adjust thresholds based on historical data
3. **Alert Optimization**: Refine notification criteria
4. **Data Quality Improvement**: Enhanced validation rules

### Metrics Dashboard

The system provides comprehensive metrics for continuous improvement:

```json
{
  \"performance_indicators\": {
    \"runtime_efficiency_percent\": 150.0,
    \"time_saved_minutes\": 44.5,
    \"cost_saved_dollars\": 18.54,
    \"error_rate_improvement_percent\": 14.2,
    \"roi_percent\": 1854.0
  }
}
```

## 🚀 Future Enhancements

### Planned Features

- **Machine Learning**: Predictive analytics for demand forecasting
- **Real-time Processing**: Stream processing capabilities
- **Mobile Alerts**: SMS and mobile app notifications
- **Dashboard**: Web-based monitoring and control interface
- **Multi-tenant**: Support for multiple organizations

### Integration Roadmap

- **ERP Systems**: SAP, Oracle, Microsoft Dynamics integration
- **Cloud Platforms**: AWS, Azure, GCP deployment options
- **BI Tools**: Power BI, Tableau, QlikView connectors
- **Workflow Automation**: Integration with workflow engines

## 🤝 Contributing

### Development Guidelines

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Follow PEP 8 style guidelines
4. Add comprehensive tests
5. Update documentation
6. Submit a pull request

### Code Style

```bash
# Format code
black src/
black tests/

# Lint code
flake8 src/
flake8 tests/

# Type checking
mypy src/
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 👥 Authors

- **Hassan Naeem** - *Initial work* - [Hassan-Naeem-code](https://github.com/Hassan-Naeem-code)

## 🙏 Acknowledgments

- **Dr. Trippel** - Course instructor and project guidance
- **Concordia University** - RPA course framework
- **Retail Innovations Inc.** - Business case study inspiration

## 📞 Support

For questions, issues, or support:

- Create an issue on GitHub
- Contact: hassan.naeem@example.com
- Documentation: [Project Wiki](https://github.com/Hassan-Naeem-code/RPA-Automation-Week-3/wiki)

---

**Built with ❤️ for automated inventory management**
