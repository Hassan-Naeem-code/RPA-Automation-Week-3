"""
Advanced Performance Monitoring and Benchmarking System

This module provides comprehensive performance monitoring, benchmarking,
and optimization recommendations for the RPA system.

Author: Hassan Naeem
Date: July 2025
"""

import time
import psutil
import threading
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any, Callable, Optional
from dataclasses import dataclass, field
from collections import deque
import json
from pathlib import Path
import functools
import gc

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Single performance measurement."""

    timestamp: datetime
    metric_name: str
    value: float
    unit: str
    context: Dict[str, Any] = field(default_factory=dict)


@dataclass
class BenchmarkResult:
    """Results from a benchmark test."""

    test_name: str
    start_time: datetime
    end_time: datetime
    duration_seconds: float
    memory_used_mb: float
    cpu_percent: float
    records_processed: int = 0
    throughput: float = 0.0
    success: bool = True
    error_message: str = ""

    @property
    def records_per_second(self) -> float:
        """Calculate records processed per second."""
        if self.duration_seconds > 0:
            return self.records_processed / self.duration_seconds
        return 0.0


class PerformanceMonitor:
    """
    Advanced performance monitoring system with real-time metrics collection,
    benchmarking, and optimization recommendations.
    """

    def __init__(self, max_history: int = 1000):
        """
        Initialize the performance monitor.

        Args:
            max_history: Maximum number of metrics to keep in memory
        """
        self.max_history = max_history
        self.metrics_history: deque = deque(maxlen=max_history)
        self.benchmarks: List[BenchmarkResult] = []
        self.monitoring_active = False
        self.monitoring_thread: Optional[threading.Thread] = None
        self.monitoring_interval = 1.0  # seconds

        # Performance baselines
        self.baselines = {
            "processing_time_seconds": 60.0,  # Target: under 1 minute
            "memory_usage_mb": 512.0,  # Target: under 512MB
            "cpu_usage_percent": 80.0,  # Target: under 80%
            "records_per_second": 1000.0,  # Target: 1000+ records/sec
        }

        # Alert thresholds
        self.alert_thresholds = {
            "memory_usage_mb": 1024.0,  # Alert if > 1GB
            "cpu_usage_percent": 90.0,  # Alert if > 90%
            "processing_time_seconds": 300.0,  # Alert if > 5 minutes
        }

        logger.info("PerformanceMonitor initialized")

    def start_monitoring(self, interval: float = 1.0):
        """Start continuous performance monitoring."""
        if self.monitoring_active:
            logger.warning("Performance monitoring is already active")
            return

        self.monitoring_interval = interval
        self.monitoring_active = True
        self.monitoring_thread = threading.Thread(
            target=self._monitoring_loop, daemon=True
        )
        self.monitoring_thread.start()

        logger.info(f"Performance monitoring started (interval: {interval}s)")

    def stop_monitoring(self):
        """Stop continuous performance monitoring."""
        if not self.monitoring_active:
            return

        self.monitoring_active = False
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5.0)

        logger.info("Performance monitoring stopped")

    def _monitoring_loop(self):
        """Main monitoring loop running in separate thread."""
        while self.monitoring_active:
            try:
                self._collect_system_metrics()
                time.sleep(self.monitoring_interval)
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
                time.sleep(5.0)  # Wait longer on error

    def _collect_system_metrics(self):
        """Collect current system performance metrics."""
        try:
            # Memory metrics
            memory = psutil.virtual_memory()
            process = psutil.Process()

            metrics = [
                PerformanceMetric(
                    timestamp=datetime.now(),
                    metric_name="system_memory_percent",
                    value=memory.percent,
                    unit="percent",
                ),
                PerformanceMetric(
                    timestamp=datetime.now(),
                    metric_name="process_memory_mb",
                    value=process.memory_info().rss / 1024 / 1024,
                    unit="MB",
                ),
                PerformanceMetric(
                    timestamp=datetime.now(),
                    metric_name="system_cpu_percent",
                    value=psutil.cpu_percent(interval=0.01),  # Reduced from 0.1 to 0.01
                    unit="percent",
                ),
                PerformanceMetric(
                    timestamp=datetime.now(),
                    metric_name="process_cpu_percent",
                    value=process.cpu_percent(),
                    unit="percent",
                ),
            ]

            # Add disk I/O if available
            try:
                disk_io = psutil.disk_io_counters()
                if disk_io:
                    metrics.extend(
                        [
                            PerformanceMetric(
                                timestamp=datetime.now(),
                                metric_name="disk_read_bytes",
                                value=disk_io.read_bytes,
                                unit="bytes",
                            ),
                            PerformanceMetric(
                                timestamp=datetime.now(),
                                metric_name="disk_write_bytes",
                                value=disk_io.write_bytes,
                                unit="bytes",
                            ),
                        ]
                    )
            except Exception as e:
                # Disk I/O metrics not available on all systems
                logger.debug(f"Disk I/O metrics unavailable: {e}")

            # Store metrics
            for metric in metrics:
                self.metrics_history.append(metric)

                # Check for alerts
                self._check_alert_thresholds(metric)

        except Exception as e:
            logger.error(f"Error collecting system metrics: {e}")

    def _check_alert_thresholds(self, metric: PerformanceMetric):
        """Check if metric exceeds alert thresholds."""
        threshold_key = None

        if metric.metric_name == "process_memory_mb":
            threshold_key = "memory_usage_mb"
        elif metric.metric_name in ["system_cpu_percent", "process_cpu_percent"]:
            threshold_key = "cpu_usage_percent"

        if threshold_key and threshold_key in self.alert_thresholds:
            threshold = self.alert_thresholds[threshold_key]
            if metric.value > threshold:
                logger.warning(
                    f"PERFORMANCE ALERT: {metric.metric_name} = {metric.value:.2f}{metric.unit} "
                    f"exceeds threshold of {threshold}"
                )

    def record_metric(
        self,
        name: str,
        value: float,
        unit: str,
        context: Optional[Dict[str, Any]] = None,
    ):
        """Record a custom performance metric."""
        metric = PerformanceMetric(
            timestamp=datetime.now(),
            metric_name=name,
            value=value,
            unit=unit,
            context=context or {},
        )

        self.metrics_history.append(metric)
        logger.debug(f"Recorded metric: {name} = {value} {unit}")

    def benchmark_function(self, func: Callable, *args, **kwargs) -> BenchmarkResult:
        """
        Benchmark a function's performance.

        Args:
            func: Function to benchmark
            *args: Function arguments
            **kwargs: Function keyword arguments

        Returns:
            BenchmarkResult with performance metrics
        """
        test_name = (
            f"{func.__module__}.{func.__name__}"
            if hasattr(func, "__name__")
            else str(func)
        )

        # Collect initial metrics
        start_time = datetime.now()
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024

        # Force garbage collection for clean measurement
        gc.collect()

        try:
            # Execute function
            result = func(*args, **kwargs)
            success = True
            error_message = ""

        except Exception as e:
            result = None
            success = False
            error_message = str(e)
            logger.error(f"Benchmark function failed: {e}")

        # Collect final metrics
        end_time = datetime.now()
        final_memory = process.memory_info().rss / 1024 / 1024
        duration = (end_time - start_time).total_seconds()

        # Calculate CPU usage (approximate)
        cpu_percent = process.cpu_percent()

        benchmark = BenchmarkResult(
            test_name=test_name,
            start_time=start_time,
            end_time=end_time,
            duration_seconds=duration,
            memory_used_mb=final_memory - initial_memory,
            cpu_percent=cpu_percent,
            success=success,
            error_message=error_message,
        )

        self.benchmarks.append(benchmark)

        logger.info(
            f"Benchmark completed: {test_name} - {duration:.3f}s, "
            f"{benchmark.memory_used_mb:.2f}MB, Success: {success}"
        )

        return benchmark

    def benchmark_data_processing(
        self, data, processing_func: Callable
    ) -> BenchmarkResult:
        """
        Benchmark data processing with throughput metrics.

        Args:
            data: Data to process (must have len())
            processing_func: Function that processes the data

        Returns:
            BenchmarkResult with throughput metrics
        """
        record_count = len(data) if hasattr(data, "__len__") else 0

        benchmark = self.benchmark_function(processing_func, data)

        # Add throughput metrics
        benchmark.records_processed = record_count
        if benchmark.duration_seconds > 0:
            benchmark.throughput = record_count / benchmark.duration_seconds

        # Record throughput metric
        self.record_metric("records_per_second", benchmark.throughput, "records/sec")

        return benchmark

    def get_performance_summary(self, hours_back: int = 24) -> Dict[str, Any]:
        """
        Get a summary of performance metrics over the specified time period.

        Args:
            hours_back: Number of hours to look back for metrics

        Returns:
            Performance summary dictionary
        """
        cutoff_time = datetime.now() - timedelta(hours=hours_back)

        # Filter metrics within time window
        recent_metrics = [m for m in self.metrics_history if m.timestamp >= cutoff_time]

        # Group metrics by name
        metric_groups: Dict[str, List[float]] = {}
        for metric in recent_metrics:
            if metric.metric_name not in metric_groups:
                metric_groups[metric.metric_name] = []
            metric_groups[metric.metric_name].append(metric.value)

        # Calculate statistics for each metric
        summary: Dict[str, Any] = {
            "period_hours": hours_back,
            "total_metrics": len(recent_metrics),
            "metric_statistics": {},
            "recent_benchmarks": len(
                [b for b in self.benchmarks if b.start_time >= cutoff_time]
            ),
            "performance_score": 0.0,
            "recommendations": [],
        }

        metric_stats: Dict[str, Dict[str, Any]] = {}
        for metric_name, values in metric_groups.items():
            if values:
                metric_stats[metric_name] = {
                    "count": len(values),
                    "average": sum(values) / len(values),
                    "min": min(values),
                    "max": max(values),
                    "latest": values[-1],
                }

        summary["metric_statistics"] = metric_stats

        # Calculate performance score (0-100)
        summary["performance_score"] = self._calculate_performance_score(metric_stats)

        # Generate recommendations
        summary["recommendations"] = self._generate_performance_recommendations(
            metric_stats
        )

        return summary

    def _calculate_performance_score(self, stats: Dict[str, Dict]) -> float:
        """Calculate overall performance score (0-100)."""
        scores = []

        # Memory score
        if "process_memory_mb" in stats:
            memory_avg = stats["process_memory_mb"]["average"]
            memory_score = max(
                0, 100 - (memory_avg / self.baselines["memory_usage_mb"]) * 100
            )
            scores.append(memory_score)

        # CPU score
        if "process_cpu_percent" in stats:
            cpu_avg = stats["process_cpu_percent"]["average"]
            cpu_score = max(
                0, 100 - (cpu_avg / self.baselines["cpu_usage_percent"]) * 100
            )
            scores.append(cpu_score)

        # Benchmark score
        recent_benchmarks = [b for b in self.benchmarks[-10:] if b.success]
        if recent_benchmarks:
            avg_duration = sum(b.duration_seconds for b in recent_benchmarks) / len(
                recent_benchmarks
            )
            duration_score = max(
                0,
                100 - (avg_duration / self.baselines["processing_time_seconds"]) * 100,
            )
            scores.append(duration_score)

        return sum(scores) / len(scores) if scores else 50.0

    def _generate_performance_recommendations(
        self, stats: Dict[str, Dict]
    ) -> List[str]:
        """Generate performance optimization recommendations."""
        recommendations = []

        # Memory recommendations
        if "process_memory_mb" in stats:
            memory_avg = stats["process_memory_mb"]["average"]
            memory_max = stats["process_memory_mb"]["max"]

            if memory_avg > self.baselines["memory_usage_mb"]:
                recommendations.append(
                    f"🔧 HIGH MEMORY USAGE: Average {memory_avg:.1f}MB exceeds target "
                    f"{self.baselines['memory_usage_mb']}MB. Consider processing data in smaller batches."
                )

            if memory_max > self.alert_thresholds["memory_usage_mb"]:
                recommendations.append(
                    f"⚠️ MEMORY SPIKE: Peak usage {memory_max:.1f}MB exceeded alert threshold. "
                    f"Implement memory monitoring and garbage collection."
                )

        # CPU recommendations
        if "process_cpu_percent" in stats:
            cpu_avg = stats["process_cpu_percent"]["average"]

            if cpu_avg > self.baselines["cpu_usage_percent"]:
                recommendations.append(
                    f"🔧 HIGH CPU USAGE: Average {cpu_avg:.1f}% exceeds target "
                    f"{self.baselines['cpu_usage_percent']}%. Consider parallel processing or algorithm optimization."
                )

        # Benchmark recommendations
        failed_benchmarks = [b for b in self.benchmarks[-20:] if not b.success]
        if failed_benchmarks:
            failure_rate = len(failed_benchmarks) / min(20, len(self.benchmarks)) * 100
            recommendations.append(
                f"⚠️ RELIABILITY ISSUE: {failure_rate:.1f}% of recent operations failed. "
                f"Implement better error handling and retry logic."
            )

        # Throughput recommendations
        if "records_per_second" in stats:
            throughput_avg = stats["records_per_second"]["average"]
            if throughput_avg < self.baselines["records_per_second"]:
                recommendations.append(
                    f"🔧 LOW THROUGHPUT: Average {throughput_avg:.0f} records/sec below target "
                    f"{self.baselines['records_per_second']}. Consider vectorized operations or caching."
                )

        if not recommendations:
            recommendations.append(
                "✅ EXCELLENT: Performance metrics are within optimal ranges!"
            )

        return recommendations

    def export_metrics(
        self, file_path: Optional[str] = None, format_type: str = "json"
    ) -> bool:
        """
        Export performance metrics to file.

        Args:
            file_path: Output file path
            format_type: Export format ('json' or 'csv')

        Returns:
            True if export successful
        """
        if not file_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_path = f"data/processed/performance_metrics_{timestamp}.{format_type}"

        try:
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)

            if format_type.lower() == "json":
                # Export as JSON
                export_data = {
                    "export_timestamp": datetime.now().isoformat(),
                    "metrics_count": len(self.metrics_history),
                    "benchmarks_count": len(self.benchmarks),
                    "metrics": [
                        {
                            "timestamp": metric.timestamp.isoformat(),
                            "name": metric.metric_name,
                            "value": metric.value,
                            "unit": metric.unit,
                            "context": metric.context,
                        }
                        for metric in self.metrics_history
                    ],
                    "benchmarks": [
                        {
                            "test_name": b.test_name,
                            "start_time": b.start_time.isoformat(),
                            "end_time": b.end_time.isoformat(),
                            "duration_seconds": b.duration_seconds,
                            "memory_used_mb": b.memory_used_mb,
                            "cpu_percent": b.cpu_percent,
                            "records_processed": b.records_processed,
                            "throughput": b.throughput,
                            "success": b.success,
                            "error_message": b.error_message,
                        }
                        for b in self.benchmarks
                    ],
                    "summary": self.get_performance_summary(),
                }

                with open(file_path, "w") as f:
                    json.dump(export_data, f, indent=2)

            else:  # CSV format
                import csv

                with open(file_path, "w", newline="") as f:
                    writer = csv.writer(f)

                    # Write metrics
                    writer.writerow(
                        ["Type", "Timestamp", "Name", "Value", "Unit", "Context"]
                    )

                    for metric in self.metrics_history:
                        writer.writerow(
                            [
                                "metric",
                                metric.timestamp.isoformat(),
                                metric.metric_name,
                                metric.value,
                                metric.unit,
                                json.dumps(metric.context),
                            ]
                        )

                    # Write benchmarks
                    for benchmark in self.benchmarks:
                        writer.writerow(
                            [
                                "benchmark",
                                benchmark.start_time.isoformat(),
                                benchmark.test_name,
                                benchmark.duration_seconds,
                                "seconds",
                                json.dumps(
                                    {
                                        "memory_mb": benchmark.memory_used_mb,
                                        "cpu_percent": benchmark.cpu_percent,
                                        "records": benchmark.records_processed,
                                        "success": benchmark.success,
                                    }
                                ),
                            ]
                        )

            logger.info(f"Performance metrics exported to {file_path}")
            return True

        except Exception as e:
            logger.error(f"Failed to export metrics: {e}")
            return False

    def clear_history(self, keep_last_hours: int = 24):
        """
        Clear old performance metrics, keeping only recent data.

        Args:
            keep_last_hours: Number of hours of data to retain
        """
        cutoff_time = datetime.now() - timedelta(hours=keep_last_hours)

        # Filter metrics
        old_count = len(self.metrics_history)
        self.metrics_history = deque(
            (m for m in self.metrics_history if m.timestamp >= cutoff_time),
            maxlen=self.max_history,
        )

        # Filter benchmarks
        old_benchmark_count = len(self.benchmarks)
        self.benchmarks = [b for b in self.benchmarks if b.start_time >= cutoff_time]

        metrics_removed = old_count - len(self.metrics_history)
        benchmarks_removed = old_benchmark_count - len(self.benchmarks)

        logger.info(
            f"Cleared {metrics_removed} old metrics and {benchmarks_removed} old benchmarks"
        )


def performance_timer(monitor: Optional[PerformanceMonitor] = None):
    """
    Decorator to automatically benchmark function performance.

    Args:
        monitor: PerformanceMonitor instance (creates new if None)
    """
    if monitor is None:
        monitor = PerformanceMonitor()

    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            benchmark = monitor.benchmark_function(func, *args, **kwargs)

            # Log performance summary
            if benchmark.success:
                logger.info(
                    f"⚡ {func.__name__} completed in {benchmark.duration_seconds:.3f}s "
                    f"({benchmark.memory_used_mb:+.2f}MB memory)"
                )
            else:
                logger.error(
                    f"❌ {func.__name__} failed after {benchmark.duration_seconds:.3f}s: "
                    f"{benchmark.error_message}"
                )

            return benchmark if not benchmark.success else args, kwargs

        return wrapper

    return decorator


if __name__ == "__main__":
    # Example usage and testing
    logging.basicConfig(level=logging.INFO)

    # Create performance monitor
    monitor = PerformanceMonitor()

    # Start monitoring
    monitor.start_monitoring(interval=2.0)  # Increased interval to reduce overhead

    # Test function to benchmark
    @performance_timer(monitor)
    def test_processing_function(data_size: int = 1000):
        """Test function that simulates data processing."""
        import time

        # Simulate processing with predictable data (not cryptographic)
        data = [i * 0.1 for i in range(data_size)]  # nosec: B311 - not cryptographic

        # Simulate some computation
        result = []
        for i, value in enumerate(data):
            if i % 1000 == 0:  # Reduced frequency from every 100 to every 1000
                time.sleep(0.0001)  # Reduced from 0.001 to 0.0001
            result.append(value * 2 + 1)

        return result

    # Run benchmarks
    print("Running performance benchmarks...")

    for size in [100, 500, 1000, 2000]:
        print(f"\nTesting with {size} records...")
        result = test_processing_function(size)

    # Wait for monitoring data
    time.sleep(0.5)  # Reduced from 2 seconds to 0.5 seconds

    # Get performance summary
    summary = monitor.get_performance_summary(hours_back=1)
    print(f"\nPerformance Summary:")
    print(f"  Score: {summary['performance_score']:.1f}/100")
    print(f"  Total Metrics: {summary['total_metrics']}")
    print(f"  Recent Benchmarks: {summary['recent_benchmarks']}")

    print(f"\nRecommendations:")
    for i, rec in enumerate(summary["recommendations"], 1):
        print(f"  {i}. {rec}")

    # Export metrics
    monitor.export_metrics()

    # Stop monitoring
    monitor.stop_monitoring()

    print("\n✅ Performance monitoring demo completed!")
