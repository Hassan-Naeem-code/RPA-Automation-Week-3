"""
Metrics Module for RPA Inventory Management System

This module provides functionality for tracking, measuring, and reporting
performance metrics and KPIs for the inventory management automation system.

Author: Hassan Naeem
Date: July 2025
"""

import time
import json
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Any, Optional
import pandas as pd
import numpy as np

# Configure logging
logger = logging.getLogger(__name__)


class MetricsCollector:
    """
    Collects and manages performance metrics for the RPA system.

    Tracks runtime performance, business metrics, error rates, and generates
    reports for continuous improvement and ROI measurement.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the metrics collector.

        Args:
            config: Configuration dictionary
        """
        self.config = config or {}
        self.metrics_file = self.config.get("metrics_file", "logs/metrics.json")

        # Initialize metrics storage
        self.session_metrics: Dict[str, Any] = {
            "session_id": f"session_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "start_time": None,
            "end_time": None,
            "total_runtime_seconds": 0,
            "stages": {},
            "business_metrics": {},
            "errors": [],
            "performance_indicators": {},
        }

        # Performance baselines (for comparison)
        self.baselines = {
            "manual_processing_time_minutes": 45,  # Baseline: 45 min per warehouse per day
            "manual_error_rate_percent": 15,  # Baseline: 15% error rate
            "manual_cost_per_hour": 25.0,  # Baseline: $25/hour labor cost
            "target_runtime_seconds": 60,  # Target: complete in under 1 minute
            "target_error_rate_percent": 2,  # Target: under 2% error rate
        }

        logger.info("MetricsCollector initialized")

    def start_session(self) -> str:
        """
        Start a new metrics collection session.

        Returns:
            Session ID
        """
        self.session_metrics["start_time"] = time.time()
        self.session_metrics["start_timestamp"] = datetime.now().isoformat()

        logger.info(f"Started metrics session: {self.session_metrics['session_id']}")
        return self.session_metrics["session_id"]

    def end_session(self) -> None:
        """
        End the current metrics collection session.
        """
        if self.session_metrics["start_time"]:
            self.session_metrics["end_time"] = time.time()
            self.session_metrics["end_timestamp"] = datetime.now().isoformat()
            self.session_metrics["total_runtime_seconds"] = round(
                self.session_metrics["end_time"] - self.session_metrics["start_time"], 2
            )

        logger.info(f"Ended metrics session: {self.session_metrics['session_id']}")

    def record_stage_time(
        self, stage_name: str, start_time: float, end_time: float
    ) -> None:
        """
        Record timing for a processing stage.

        Args:
            stage_name: Name of the processing stage
            start_time: Stage start time (from time.time())
            end_time: Stage end time (from time.time())
        """
        duration = round(end_time - start_time, 2)
        self.session_metrics["stages"][stage_name] = {
            "start_time": start_time,
            "end_time": end_time,
            "duration_seconds": duration,
            "start_timestamp": datetime.fromtimestamp(start_time).isoformat(),
            "end_timestamp": datetime.fromtimestamp(end_time).isoformat(),
        }

        logger.info(f"Recorded stage '{stage_name}': {duration}s")

    def record_business_metrics(
        self,
        processed_data: pd.DataFrame,
        summary_stats: Dict[str, Any],
        violations: List[Dict[str, Any]],
    ) -> None:
        """
        Record business-related metrics from processed data.

        Args:
            processed_data: Processed inventory DataFrame
            summary_stats: Summary statistics
            violations: Business rule violations
        """
        business_metrics = {
            "total_records_processed": len(processed_data),
            "unique_skus": (
                processed_data["SKU"].nunique()
                if "SKU" in processed_data.columns
                else 0
            ),
            "total_inventory_value": float(
                summary_stats.get("total_inventory_value", 0)
            ),
            "low_stock_items": (
                len(processed_data[processed_data["StockStatus"] == "Low Stock"])
                if "StockStatus" in processed_data.columns
                else 0
            ),
            "critical_items": (
                len(
                    processed_data[
                        processed_data["StockStatus"].isin(["Critical", "Out of Stock"])
                    ]
                )
                if "StockStatus" in processed_data.columns
                else 0
            ),
            "items_needing_reorder": (
                len(processed_data[processed_data["ReorderQty"] > 0])
                if "ReorderQty" in processed_data.columns
                else 0
            ),
            "business_rule_violations": len(violations),
            "data_quality_score": self._calculate_data_quality_score(
                processed_data, violations
            ),
            "processing_accuracy": self._calculate_processing_accuracy(
                processed_data, violations
            ),
        }

        self.session_metrics["business_metrics"] = business_metrics
        logger.info(
            f"Recorded business metrics: {business_metrics['total_records_processed']} records processed"
        )

    def record_error(
        self, error_type: str, error_message: str, stage: Optional[str] = None
    ) -> None:
        """
        Record an error that occurred during processing.

        Args:
            error_type: Type/category of error
            error_message: Error message
            stage: Processing stage where error occurred
        """
        error_record = {
            "timestamp": datetime.now().isoformat(),
            "error_type": error_type,
            "error_message": error_message,
            "stage": stage,
        }

        self.session_metrics["errors"].append(error_record)
        logger.warning(f"Recorded error: {error_type} in {stage}: {error_message}")

    def _calculate_data_quality_score(
        self, df: pd.DataFrame, violations: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate a data quality score based on various factors.

        Args:
            df: Processed DataFrame
            violations: Business rule violations

        Returns:
            Data quality score (0-100)
        """
        if df.empty:
            return 0.0

        # Factors for data quality score
        total_records = len(df)
        violation_penalty = min(
            50, (len(violations) / total_records) * 100
        )  # Max 50 point penalty

        # Check for missing critical data
        critical_columns = ["SKU", "OnHandQty", "ReorderPoint"]
        missing_data_penalty = 0

        for col in critical_columns:
            if col in df.columns:
                missing_count = df[col].isna().sum()
                missing_data_penalty += (
                    missing_count / total_records
                ) * 10  # Max 10 points per column

        # Calculate score
        base_score = 100
        final_score = max(0, base_score - violation_penalty - missing_data_penalty)

        return round(final_score, 2)

    def _calculate_processing_accuracy(
        self, df: pd.DataFrame, violations: List[Dict[str, Any]]
    ) -> float:
        """
        Calculate processing accuracy percentage.

        Args:
            df: Processed DataFrame
            violations: Business rule violations

        Returns:
            Processing accuracy percentage
        """
        if df.empty:
            return 0.0

        total_records = len(df)
        error_records = len(violations)

        accuracy = ((total_records - error_records) / total_records) * 100
        return round(max(0, accuracy), 2)

    def calculate_performance_indicators(self) -> Dict[str, Any]:
        """
        Calculate KPIs and performance indicators.

        Returns:
            Dictionary of performance indicators
        """
        indicators = {}

        # Runtime efficiency
        actual_runtime = self.session_metrics.get("total_runtime_seconds", 0)
        target_runtime = self.baselines["target_runtime_seconds"]

        indicators["runtime_efficiency_percent"] = round(
            (target_runtime / max(actual_runtime, 0.1)) * 100, 2
        )

        # Time savings compared to manual process
        manual_time_seconds = self.baselines["manual_processing_time_minutes"] * 60
        time_saved_seconds = manual_time_seconds - actual_runtime

        indicators["time_saved_seconds"] = max(0, time_saved_seconds)
        indicators["time_saved_minutes"] = round(time_saved_seconds / 60, 2)
        indicators["time_savings_percent"] = (
            round((time_saved_seconds / manual_time_seconds) * 100, 2)
            if manual_time_seconds > 0
            else 0
        )

        # Cost savings
        hourly_rate = self.baselines["manual_cost_per_hour"]
        cost_saved = (time_saved_seconds / 3600) * hourly_rate

        indicators["cost_saved_dollars"] = round(max(0, cost_saved), 2)

        # Error rate improvement
        actual_error_rate = 100 - self.session_metrics.get("business_metrics", {}).get(
            "processing_accuracy", 100
        )
        manual_error_rate = self.baselines["manual_error_rate_percent"]

        indicators["error_rate_improvement_percent"] = round(
            manual_error_rate - actual_error_rate, 2
        )

        # Processing throughput
        records_processed = self.session_metrics.get("business_metrics", {}).get(
            "total_records_processed", 0
        )

        indicators["records_per_second"] = round(
            records_processed / max(actual_runtime, 0.1), 2
        )
        indicators["records_per_minute"] = round(
            (records_processed / max(actual_runtime, 0.1)) * 60, 2
        )

        # ROI calculation (simple)
        processing_cost = (
            actual_runtime / 3600
        ) * 5  # Assume $5/hour for automated processing
        manual_processing_cost = (manual_time_seconds / 3600) * hourly_rate

        indicators["roi_percent"] = (
            round(
                ((manual_processing_cost - processing_cost) / processing_cost) * 100, 2
            )
            if processing_cost > 0
            else 0
        )

        self.session_metrics["performance_indicators"] = indicators

        logger.info(f"Calculated performance indicators: {len(indicators)} metrics")
        return indicators

    def generate_metrics_summary(self) -> Dict[str, Any]:
        """
        Generate a comprehensive metrics summary.

        Returns:
            Complete metrics summary dictionary
        """
        # Ensure performance indicators are calculated
        if not self.session_metrics.get("performance_indicators"):
            self.calculate_performance_indicators()

        summary = {
            "session_info": {
                "session_id": self.session_metrics["session_id"],
                "start_time": self.session_metrics.get("start_timestamp"),
                "end_time": self.session_metrics.get("end_timestamp"),
                "total_runtime_seconds": self.session_metrics.get(
                    "total_runtime_seconds", 0
                ),
            },
            "stage_performance": self.session_metrics.get("stages", {}),
            "business_metrics": self.session_metrics.get("business_metrics", {}),
            "performance_indicators": self.session_metrics.get(
                "performance_indicators", {}
            ),
            "error_summary": {
                "total_errors": len(self.session_metrics.get("errors", [])),
                "errors_by_type": self._group_errors_by_type(),
                "error_details": self.session_metrics.get("errors", []),
            },
            "baseline_comparison": self._compare_to_baselines(),
        }

        return summary

    def _group_errors_by_type(self) -> Dict[str, int]:
        """Group errors by type for summary reporting."""
        error_counts: Dict[str, int] = {}
        for error in self.session_metrics.get("errors", []):
            error_type = error.get("error_type", "Unknown")
            error_counts[error_type] = error_counts.get(error_type, 0) + 1
        return error_counts

    def _compare_to_baselines(self) -> Dict[str, Any]:
        """Compare current performance to established baselines."""
        comparison = {}
        indicators = self.session_metrics.get("performance_indicators", {})

        # Runtime comparison
        actual_runtime = self.session_metrics.get("total_runtime_seconds", 0)
        target_runtime = self.baselines["target_runtime_seconds"]

        comparison["runtime_vs_target"] = {
            "actual_seconds": actual_runtime,
            "target_seconds": target_runtime,
            "performance": (
                "EXCELLENT" if actual_runtime <= target_runtime else "NEEDS_IMPROVEMENT"
            ),
            "difference_seconds": actual_runtime - target_runtime,
        }

        # Error rate comparison
        actual_error_rate = 100 - self.session_metrics.get("business_metrics", {}).get(
            "processing_accuracy", 100
        )
        target_error_rate = self.baselines["target_error_rate_percent"]

        comparison["error_rate_vs_target"] = {
            "actual_error_rate_percent": actual_error_rate,
            "target_error_rate_percent": target_error_rate,
            "performance": (
                "EXCELLENT"
                if actual_error_rate <= target_error_rate
                else "NEEDS_IMPROVEMENT"
            ),
            "difference_percent": actual_error_rate - target_error_rate,
        }

        return comparison

    def save_metrics(self, file_path: Optional[str] = None) -> bool:
        """
        Save metrics to file.

        Args:
            file_path: Optional custom file path

        Returns:
            True if successful, False otherwise
        """
        file_path = file_path or self.metrics_file

        try:
            # Ensure directory exists
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)

            # Generate complete metrics summary
            metrics_summary = self.generate_metrics_summary()

            # Save to file
            with open(file_path, "w") as f:
                json.dump(metrics_summary, f, indent=2, default=str)

            logger.info(f"Metrics saved to {file_path}")
            return True

        except Exception as e:
            logger.error(f"Error saving metrics: {e}")
            return False

    def load_historical_metrics(
        self, file_path: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Load historical metrics from file.

        Args:
            file_path: Optional custom file path

        Returns:
            List of historical metrics sessions
        """
        file_path = file_path or self.metrics_file

        try:
            if Path(file_path).exists():
                with open(file_path, "r") as f:
                    data = json.load(f)

                # Handle both single session and multiple sessions
                if isinstance(data, list):
                    return data
                else:
                    return [data]
            else:
                return []

        except Exception as e:
            logger.error(f"Error loading historical metrics: {e}")
            return []

    def generate_trend_analysis(self, days: int = 30) -> Dict[str, Any]:
        """
        Generate trend analysis from historical metrics.

        Args:
            days: Number of days to analyze

        Returns:
            Trend analysis summary
        """
        historical_data = self.load_historical_metrics()

        if not historical_data:
            return {"message": "No historical data available for trend analysis"}

        # Filter recent data
        cutoff_date = datetime.now() - timedelta(days=days)
        recent_data = []

        for session in historical_data:
            session_date = datetime.fromisoformat(
                session["session_info"]["start_time"].replace("Z", "+00:00")
            )
            if session_date >= cutoff_date:
                recent_data.append(session)

        if not recent_data:
            return {"message": f"No data available for the last {days} days"}

        # Calculate trends
        runtimes = [s["session_info"]["total_runtime_seconds"] for s in recent_data]
        error_rates = [
            100 - s["business_metrics"].get("processing_accuracy", 100)
            for s in recent_data
        ]
        records_processed = [
            s["business_metrics"].get("total_records_processed", 0) for s in recent_data
        ]

        trends = {
            "analysis_period_days": days,
            "total_sessions": len(recent_data),
            "runtime_trends": {
                "average_seconds": round(np.mean(runtimes), 2),
                "min_seconds": round(np.min(runtimes), 2),
                "max_seconds": round(np.max(runtimes), 2),
                "std_deviation": round(np.std(runtimes), 2),
                "trend": (
                    "IMPROVING"
                    if len(runtimes) > 1 and runtimes[-1] < runtimes[0]
                    else "STABLE"
                ),
            },
            "error_rate_trends": {
                "average_error_rate_percent": round(np.mean(error_rates), 2),
                "min_error_rate_percent": round(np.min(error_rates), 2),
                "max_error_rate_percent": round(np.max(error_rates), 2),
                "trend": (
                    "IMPROVING"
                    if len(error_rates) > 1 and error_rates[-1] < error_rates[0]
                    else "STABLE"
                ),
            },
            "throughput_trends": {
                "average_records_processed": round(np.mean(records_processed), 2),
                "total_records_processed": sum(records_processed),
            },
        }

        return trends


def track_performance(func):
    """
    Decorator for tracking function performance.

    Args:
        func: Function to track

    Returns:
        Wrapped function with performance tracking
    """

    def wrapper(*args, **kwargs):
        start_time = time.time()

        try:
            result = func(*args, **kwargs)
            end_time = time.time()

            logger.info(
                f"Function '{func.__name__}' completed in {end_time - start_time:.2f}s"
            )
            return result

        except Exception as e:
            end_time = time.time()
            logger.error(
                f"Function '{func.__name__}' failed after {end_time - start_time:.2f}s: {e}"
            )
            raise

    return wrapper


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # Create metrics collector
    collector = MetricsCollector()

    # Start session
    session_id = collector.start_session()

    # Simulate some processing stages
    time.sleep(0.01)  # Reduced simulation time for extraction
    collector.record_stage_time("extraction", time.time() - 0.01, time.time())

    time.sleep(0.02)  # Reduced simulation time for processing
    collector.record_stage_time("processing", time.time() - 0.02, time.time())

    # Create sample data for business metrics
    sample_data = pd.DataFrame(
        {
            "SKU": ["SKU001", "SKU002", "SKU003"],
            "StockStatus": ["Normal", "Low Stock", "Critical"],
            "ReorderQty": [0, 10, 25],
        }
    )

    summary_stats = {"total_inventory_value": 1000.0}
    violations = [{"SKU": "SKU003", "issue": "Critical stock"}]

    # Record business metrics
    collector.record_business_metrics(sample_data, summary_stats, violations)

    # End session
    collector.end_session()

    # Generate and display metrics
    metrics_summary = collector.generate_metrics_summary()
    print("Metrics Summary:")
    print(json.dumps(metrics_summary, indent=2, default=str))

    # Save metrics
    collector.save_metrics()
