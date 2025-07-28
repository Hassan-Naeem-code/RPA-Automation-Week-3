#!/usr/bin/env python3
"""
Main Orchestrator for RPA Inventory Management System

This is the main entry point that coordinates all components of the inventory
management automation system. It handles command-line arguments, loads configuration,
and orchestrates the complete workflow from data extraction to alert generation.

Author: Hassan Naeem
Date: July 2025

Usage:
    python main.py --input data/inventory_raw.csv --output data/processed/
    python main.py --config config.json --send-alert
    python main.py --help
"""

import argparse
import logging
import sys
import time
from pathlib import Path
from typing import Dict, Any, Optional
import json
import os
from datetime import datetime

# Load environment variables
from dotenv import load_dotenv

load_dotenv()

# Configure global logger
logger = logging.getLogger(__name__)

# Import our modules
from src.extract import InventoryExtractor
from src.process import InventoryProcessor
from src.update import InventoryUpdater
from src.alert import InventoryAlerter

# Import new advanced modules
try:
    from src.analytics import InventoryAnalytics

    ANALYTICS_AVAILABLE = True
except ImportError:
    ANALYTICS_AVAILABLE = False
    logger.warning(
        "Advanced analytics module not available - install matplotlib, seaborn, scikit-learn"
    )

try:
    from src.config_manager import SmartConfigManager

    CONFIG_MANAGER_AVAILABLE = True
except ImportError:
    CONFIG_MANAGER_AVAILABLE = False
    logger.warning("Smart configuration manager not available - install pyyaml")

try:
    from src.performance_monitor import PerformanceMonitor, performance_timer

    PERFORMANCE_MONITOR_AVAILABLE = True
except ImportError:
    PERFORMANCE_MONITOR_AVAILABLE = False
    logger.warning("Performance monitor not available - install psutil")


class InventoryRPAOrchestrator:
    """
    Main orchestrator class that coordinates the entire RPA workflow.

    Manages the complete pipeline from data extraction through alert generation,
    with comprehensive logging, error handling, and performance metrics.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the RPA orchestrator.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.start_time = None
        self.end_time = None

        # Initialize core components
        self.extractor = InventoryExtractor(self.config)
        self.processor = InventoryProcessor(self.config)
        self.updater = InventoryUpdater(self.config)
        self.alerter = InventoryAlerter(self.config)

        # Initialize advanced components (if available)
        self.analytics = None
        self.config_manager = None
        self.performance_monitor = None

        if ANALYTICS_AVAILABLE:
            self.analytics = InventoryAnalytics(self.config)
            logger.info("✨ Advanced Analytics Engine initialized")

        if CONFIG_MANAGER_AVAILABLE:
            self.config_manager = SmartConfigManager()
            logger.info("✨ Smart Configuration Manager initialized")

        if PERFORMANCE_MONITOR_AVAILABLE:
            self.performance_monitor = PerformanceMonitor()
            self.performance_monitor.start_monitoring()
            logger.info("✨ Performance Monitor initialized and started")

        # Performance metrics
        self.metrics = {
            "start_time": None,
            "end_time": None,
            "total_runtime_seconds": 0,
            "records_processed": 0,
            "processing_stages": {},
            "errors_encountered": 0,
            "alerts_sent": 0,
            "advanced_features_used": {
                "analytics": ANALYTICS_AVAILABLE,
                "config_manager": CONFIG_MANAGER_AVAILABLE,
                "performance_monitor": PERFORMANCE_MONITOR_AVAILABLE,
            },
        }

        logger.info("InventoryRPAOrchestrator initialized")

    def load_config_from_file(self, config_file: str) -> Dict[str, Any]:
        """
        Load configuration from JSON file.

        Args:
            config_file: Path to configuration file

        Returns:
            Configuration dictionary
        """
        try:
            with open(config_file, "r") as f:
                config = json.load(f)
            logger.info(f"Configuration loaded from {config_file}")
            return config
        except Exception as e:
            logger.error(f"Error loading configuration file: {e}")
            return {}

    def load_config_from_env(self) -> Dict[str, Any]:
        """
        Load configuration from environment variables.

        Returns:
            Configuration dictionary from environment
        """
        config = {
            # Email configuration
            "smtp_server": os.getenv("SMTP_SERVER", "smtp.gmail.com"),
            "smtp_port": int(os.getenv("SMTP_PORT", "587")),
            "email_user": os.getenv("EMAIL_USER"),
            "email_password": os.getenv("EMAIL_PASSWORD"),
            "alert_recipients": os.getenv("ALERT_RECIPIENTS", ""),
            # API configuration
            "api_url": os.getenv("INVENTORY_API_URL"),
            "api_key": os.getenv("API_KEY"),
            # Business rules
            "low_stock_multiplier": float(os.getenv("LOW_STOCK_MULTIPLIER", "1.2")),
            "critical_stock_threshold": int(os.getenv("CRITICAL_STOCK_THRESHOLD", "5")),
            # System configuration
            "max_retries": int(os.getenv("MAX_RETRIES", "3")),
            "timeout_seconds": int(os.getenv("TIMEOUT_SECONDS", "30")),
            "log_level": os.getenv("LOG_LEVEL", "INFO"),
        }

        # Remove None values
        config = {k: v for k, v in config.items() if v is not None and v != ""}

        logger.info("Configuration loaded from environment variables")
        return config

    def setup_logging(
        self, log_level: str = "INFO", log_file: str = "logs/rpa_run.log"
    ):
        """
        Set up comprehensive logging for the RPA system.

        Args:
            log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            log_file: Path to log file
        """
        # Ensure log directory exists
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)

        # Configure logging
        logging.basicConfig(
            level=getattr(logging, log_level.upper()),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            handlers=[logging.FileHandler(log_file), logging.StreamHandler(sys.stdout)],
        )

        logger.info(f"Logging configured: level={log_level}, file={log_file}")

    def validate_inputs(self, input_file: str, output_dir: str) -> bool:
        """
        Validate input parameters and file accessibility.

        Args:
            input_file: Path to input inventory file
            output_dir: Path to output directory

        Returns:
            True if inputs are valid, False otherwise
        """
        logger.info("Validating input parameters")

        # Check input file exists
        if not Path(input_file).exists():
            logger.error(f"Input file not found: {input_file}")
            return False

        # Check input file is readable
        try:
            with open(input_file, "r") as f:
                f.read(1)
        except Exception as e:
            logger.error(f"Cannot read input file: {e}")
            return False

        # Ensure output directory exists or can be created
        try:
            Path(output_dir).mkdir(parents=True, exist_ok=True)
        except Exception as e:
            logger.error(f"Cannot create output directory: {e}")
            return False

        logger.info("Input validation completed successfully")
        return True

    def run_workflow(
        self,
        input_file: str,
        output_dir: str = "data/processed",
        send_alerts: bool = True,
        create_backup: bool = True,
    ) -> Dict[str, Any]:
        """
        Execute the complete RPA workflow.

        Args:
            input_file: Path to input inventory file
            output_dir: Directory for output files
            send_alerts: Whether to send email alerts
            create_backup: Whether to create data backups

        Returns:
            Dictionary containing execution results and metrics
        """
        self.start_time = time.time()
        self.metrics["start_time"] = datetime.now().isoformat()

        logger.info("=" * 60)
        logger.info("STARTING RPA INVENTORY MANAGEMENT WORKFLOW")
        logger.info("=" * 60)

        results = {
            "success": False,
            "stages_completed": [],
            "errors": [],
            "metrics": {},
            "output_files": [],
            "alerts_sent": False,
        }

        try:
            # Stage 1: Data Extraction
            logger.info("Stage 1: Data Extraction")
            stage_start = time.time()

            try:
                raw_data = self.extractor.extract_data(input_file)
                self.metrics["records_processed"] = len(raw_data)
                results["stages_completed"].append("extraction")
                logger.info(f"Extracted {len(raw_data)} records from {input_file}")
            except Exception as e:
                error_msg = f"Data extraction failed: {e}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
                self.metrics["errors_encountered"] += 1
                return results

            self.metrics["processing_stages"]["extraction"] = time.time() - stage_start

            # Stage 2: Data Processing
            logger.info("Stage 2: Data Processing")
            stage_start = time.time()

            try:
                processed_data, summary_stats, violations = (
                    self.processor.process_inventory(raw_data)
                )
                results["stages_completed"].append("processing")
                logger.info(
                    f"Processed {len(processed_data)} records with {len(violations)} violations"
                )
            except Exception as e:
                error_msg = f"Data processing failed: {e}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
                self.metrics["errors_encountered"] += 1
                return results

            self.metrics["processing_stages"]["processing"] = time.time() - stage_start

            # Stage 3: Data Update/Save
            logger.info("Stage 3: Data Update and Save")
            stage_start = time.time()

            try:
                update_results = self.updater.update_inventory(
                    processed_data,
                    summary_stats,
                    violations,
                    output_formats=["csv", "excel", "json"],
                    output_dir=output_dir,
                )
                results["stages_completed"].append("update")

                # Track output files
                output_path = Path(output_dir)
                potential_files = [
                    output_path / "inventory_processed.csv",
                    output_path / "inventory_processed.xlsx",
                    output_path / "inventory_processed.json",
                    output_path / "processing_report.json",
                ]

                results["output_files"] = [
                    str(f) for f in potential_files if f.exists()
                ]

                logger.info(
                    f"Data saved to {len(results['output_files'])} output files"
                )
            except Exception as e:
                error_msg = f"Data update failed: {e}"
                logger.error(error_msg)
                results["errors"].append(error_msg)
                self.metrics["errors_encountered"] += 1
                # Continue to alerts even if update partially fails

            self.metrics["processing_stages"]["update"] = time.time() - stage_start

            # Stage 4: Alert Generation
            if send_alerts:
                logger.info("Stage 4: Alert Generation")
                stage_start = time.time()

                try:
                    alert_results = self.alerter.send_alerts(
                        processed_data,
                        summary_stats,
                        send_email=bool(self.config.get("email_user")),
                        save_log=True,
                        show_console=True,
                    )
                    results["stages_completed"].append("alerts")
                    results["alerts_sent"] = any(alert_results.values())

                    if results["alerts_sent"]:
                        self.metrics["alerts_sent"] = 1

                    logger.info(f"Alerts processed: {alert_results}")
                except Exception as e:
                    error_msg = f"Alert generation failed: {e}"
                    logger.error(error_msg)
                    results["errors"].append(error_msg)
                    self.metrics["errors_encountered"] += 1

                self.metrics["processing_stages"]["alerts"] = time.time() - stage_start

            # Calculate final metrics
            self.end_time = time.time()
            self.metrics["end_time"] = datetime.now().isoformat()
            self.metrics["total_runtime_seconds"] = round(
                self.end_time - self.start_time, 2
            )

            results["success"] = len(results["errors"]) == 0
            results["metrics"] = self.metrics.copy()

            # Log final results
            logger.info("=" * 60)
            logger.info("WORKFLOW COMPLETED")
            logger.info(f"Success: {results['success']}")
            logger.info(f"Stages completed: {results['stages_completed']}")
            logger.info(
                f"Total runtime: {self.metrics['total_runtime_seconds']} seconds"
            )
            logger.info(f"Records processed: {self.metrics['records_processed']}")
            logger.info(f"Errors encountered: {self.metrics['errors_encountered']}")
            logger.info("=" * 60)

            return results

        except Exception as e:
            error_msg = f"Unexpected workflow error: {e}"
            logger.error(error_msg)
            results["errors"].append(error_msg)
            self.metrics["errors_encountered"] += 1
            return results


def create_argument_parser() -> argparse.ArgumentParser:
    """
    Create and configure the command-line argument parser.

    Returns:
        Configured ArgumentParser instance
    """
    parser = argparse.ArgumentParser(
        description="RPA Inventory Management System - Automates inventory processing and alerts",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --input data/inventory_raw.csv
  %(prog)s --input data/inventory_raw.csv --output results/ --send-alerts
  %(prog)s --config config.json --log-level DEBUG
  %(prog)s --input data/inventory_raw.csv --no-backup --no-alerts
        """,
    )

    # Required arguments
    parser.add_argument(
        "--input", "-i", required=True, help="Path to input inventory CSV/Excel file"
    )

    # Optional arguments
    parser.add_argument(
        "--output",
        "-o",
        default="data/processed",
        help="Output directory for processed files (default: data/processed)",
    )

    parser.add_argument("--config", "-c", help="Path to configuration JSON file")

    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="Logging level (default: INFO)",
    )

    parser.add_argument(
        "--log-file",
        default="logs/rpa_run.log",
        help="Path to log file (default: logs/rpa_run.log)",
    )

    # Boolean flags
    parser.add_argument(
        "--send-alerts",
        action="store_true",
        default=True,
        help="Send email alerts for low stock items (default: True)",
    )

    parser.add_argument("--no-alerts", action="store_true", help="Disable email alerts")

    parser.add_argument(
        "--no-backup", action="store_true", help="Disable automatic backup creation"
    )

    parser.add_argument(
        "--version", action="version", version="RPA Inventory Management System v1.0.0"
    )

    return parser


def main():
    """
    Main entry point for the RPA Inventory Management System.
    """
    # Parse command-line arguments
    parser = create_argument_parser()
    args = parser.parse_args()

    # Handle conflicting arguments
    send_alerts = args.send_alerts and not args.no_alerts
    create_backup = not args.no_backup

    try:
        # Initialize orchestrator
        orchestrator = InventoryRPAOrchestrator()

        # Setup logging
        orchestrator.setup_logging(args.log_level, args.log_file)

        # Load configuration
        config = orchestrator.load_config_from_env()

        if args.config:
            file_config = orchestrator.load_config_from_file(args.config)
            config.update(file_config)

        # Update orchestrator with final config
        orchestrator.config = config
        orchestrator.extractor.config = config
        orchestrator.processor.config = config
        orchestrator.updater.config = config
        orchestrator.alerter.config = config

        # Validate inputs
        if not orchestrator.validate_inputs(args.input, args.output):
            sys.exit(1)

        # Run the workflow
        results = orchestrator.run_workflow(
            input_file=args.input,
            output_dir=args.output,
            send_alerts=send_alerts,
            create_backup=create_backup,
        )

        # Print final summary
        print("\n" + "=" * 60)
        print("EXECUTION SUMMARY")
        print("=" * 60)
        print(f"Success: {'✅' if results['success'] else '❌'} {results['success']}")
        print(f"Stages completed: {', '.join(results['stages_completed'])}")
        print(f"Runtime: {results['metrics'].get('total_runtime_seconds', 0)} seconds")
        print(f"Records processed: {results['metrics'].get('records_processed', 0)}")
        print(f"Output files: {len(results['output_files'])}")
        print(
            f"Alerts sent: {'✅' if results['alerts_sent'] else '❌'} {results['alerts_sent']}"
        )

        if results["errors"]:
            print(f"\n❌ Errors ({len(results['errors'])}):")
            for error in results["errors"]:
                print(f"  • {error}")

        if results["output_files"]:
            print(f"\n📁 Output files:")
            for file_path in results["output_files"]:
                print(f"  • {file_path}")

        print("=" * 60)

        # Exit with appropriate code
        sys.exit(0 if results["success"] else 1)

    except KeyboardInterrupt:
        logger.info("Process interrupted by user")
        print("\n⚠️ Process interrupted by user")
        sys.exit(130)
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        print(f"\n❌ Fatal error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
