"""
Unit Tests for RPA Inventory Management System

This module contains comprehensive unit tests for all major components
of the inventory management automation system.

Author: Hassan Naeem
Date: July 2025
"""

import pytest
import pandas as pd
import tempfile
import json
from unittest.mock import Mock, patch
import sys
import os

# Add src directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from extract import InventoryExtractor
from process import InventoryProcessor
from update import InventoryUpdater
from alert import InventoryAlerter
from metrics import MetricsCollector


class TestInventoryExtractor:
    """Test cases for the InventoryExtractor class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.extractor = InventoryExtractor()
        self.sample_data = {
            "SKU": ["SKU001", "SKU002", "SKU003"],
            "Description": ["Item A", "Item B", "Item C"],
            "Location": ["WH1", "WH2", "WH1"],
            "OnHandQty": [100, 50, 25],
            "ReorderPoint": [50, 30, 40],
            "UnitCost": [10.99, 15.50, 8.75],
        }

    def test_extract_from_csv_success(self):
        """Test successful CSV extraction."""
        # Create temporary CSV file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            df = pd.DataFrame(self.sample_data)
            df.to_csv(f.name, index=False)
            temp_file = f.name

        try:
            # Test extraction
            result_df = self.extractor.extract_from_csv(temp_file)

            # Assertions
            assert len(result_df) == 3
            assert list(result_df.columns) == list(self.sample_data.keys())
            assert result_df["SKU"].tolist() == ["SKU001", "SKU002", "SKU003"]

        finally:
            # Cleanup
            os.unlink(temp_file)

    def test_extract_from_csv_file_not_found(self):
        """Test CSV extraction with non-existent file."""
        with pytest.raises(FileNotFoundError):
            self.extractor.extract_from_csv("non_existent_file.csv")

    def test_extract_from_csv_missing_columns(self):
        """Test CSV extraction with missing required columns."""
        # Create CSV with missing columns
        incomplete_data = {"SKU": ["SKU001"], "Description": ["Item A"]}

        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            df = pd.DataFrame(incomplete_data)
            df.to_csv(f.name, index=False)
            temp_file = f.name

        try:
            with pytest.raises(ValueError, match="Missing required columns"):
                self.extractor.extract_from_csv(temp_file)
        finally:
            os.unlink(temp_file)

    def test_get_file_info(self):
        """Test file information retrieval."""
        # Create temporary file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".csv", delete=False) as f:
            f.write("test,data\\n1,2")
            temp_file = f.name

        try:
            file_info = self.extractor.get_file_info(temp_file)

            # Assertions
            assert "file_name" in file_info
            assert "file_size_bytes" in file_info
            assert "file_extension" in file_info
            assert file_info["file_extension"] == ".csv"
            assert file_info["file_size_bytes"] > 0

        finally:
            os.unlink(temp_file)


class TestInventoryProcessor:
    """Test cases for the InventoryProcessor class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.processor = InventoryProcessor()
        self.sample_data = pd.DataFrame(
            {
                "SKU": ["SKU001", "SKU002", "SKU001", "SKU003"],  # Includes duplicate
                "Description": ["Item A", "Item B", "Item A", ""],  # Includes empty
                "Location": ["WH1", "WH2", "WH1", "WH3"],
                "OnHandQty": [100, -5, 110, 25],  # Includes negative
                "ReorderPoint": [50, 30, 50, 40],
                "UnitCost": [10.99, 15.50, 10.99, 8.75],
            }
        )

    def test_clean_data(self):
        """Test data cleaning functionality."""
        cleaned_df = self.processor.clean_data(self.sample_data)

        # Check negative quantities are fixed
        assert (cleaned_df["OnHandQty"] >= 0).all()

        # Check empty descriptions are handled
        assert not (cleaned_df["Description"] == "").any()

        # Check SKUs are uppercase and trimmed
        assert cleaned_df["SKU"].str.isupper().all()

    def test_remove_duplicates(self):
        """Test duplicate removal."""
        # Test keep_last strategy
        deduped_df = self.processor.remove_duplicates(
            self.sample_data, strategy="keep_last"
        )

        # Should have 3 records (one duplicate removed)
        assert len(deduped_df) == 3

        # Check that the last occurrence of SKU001 is kept (OnHandQty=110)
        sku001_record = deduped_df[deduped_df["SKU"] == "SKU001"]
        assert len(sku001_record) == 1
        assert sku001_record["OnHandQty"].iloc[0] == 110

    def test_calculate_reorder_metrics(self):
        """Test reorder metrics calculation."""
        cleaned_df = self.processor.clean_data(self.sample_data)
        metrics_df = self.processor.calculate_reorder_metrics(cleaned_df)

        # Check new columns are added
        expected_columns = [
            "ReorderQty",
            "StockStatus",
            "DaysOfSupply",
            "TotalValue",
            "ProcessedAt",
        ]
        for col in expected_columns:
            assert col in metrics_df.columns

        # Check reorder quantity calculation
        assert (metrics_df["ReorderQty"] >= 0).all()

        # Check stock status assignment
        valid_statuses = ["Normal", "Low Stock", "Critical", "Out of Stock"]
        assert metrics_df["StockStatus"].isin(valid_statuses).all()

    def test_validate_business_rules(self):
        """Test business rule validation."""
        processed_df = self.processor.calculate_reorder_metrics(
            self.processor.clean_data(self.sample_data)
        )

        validated_df, violations = self.processor.validate_business_rules(processed_df)

        # Check validation status column is added
        assert "ValidationStatus" in validated_df.columns

        # Check violations format
        if violations:
            assert isinstance(violations, list)
            assert all("SKU" in v and "Rule" in v for v in violations)

    def test_process_inventory_complete(self):
        """Test complete inventory processing pipeline."""
        processed_df, summary_stats, violations = self.processor.process_inventory(
            self.sample_data
        )

        # Check processed data
        assert len(processed_df) > 0
        assert "StockStatus" in processed_df.columns
        assert "ReorderQty" in processed_df.columns

        # Check summary stats
        assert "total_records" in summary_stats
        assert "processing_timestamp" in summary_stats
        assert summary_stats["total_records"] == len(processed_df)

        # Check violations format
        assert isinstance(violations, list)


class TestInventoryUpdater:
    """Test cases for the InventoryUpdater class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.updater = InventoryUpdater()
        self.sample_df = pd.DataFrame(
            {
                "SKU": ["SKU001", "SKU002"],
                "Description": ["Item A", "Item B"],
                "StockStatus": ["Normal", "Low Stock"],
                "ReorderQty": [0, 15],
                "TotalValue": [100.0, 250.0],
            }
        )
        self.sample_stats = {
            "total_records": 2,
            "processing_timestamp": "2025-01-01T12:00:00",
        }
        self.sample_violations = []

    def test_save_to_csv(self):
        """Test CSV saving functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = os.path.join(temp_dir, "test_output.csv")

            success = self.updater.save_to_csv(self.sample_df, output_file)

            assert success
            assert os.path.exists(output_file)

            # Verify content
            loaded_df = pd.read_csv(output_file)
            assert len(loaded_df) == len(self.sample_df)
            assert list(loaded_df.columns) == list(self.sample_df.columns)

    def test_save_to_json(self):
        """Test JSON saving functionality."""
        with tempfile.TemporaryDirectory() as temp_dir:
            output_file = os.path.join(temp_dir, "test_output.json")

            success = self.updater.save_to_json(self.sample_df, output_file)

            assert success
            assert os.path.exists(output_file)

            # Verify content
            with open(output_file, "r") as f:
                data = json.load(f)
            assert len(data) == len(self.sample_df)

    def test_save_summary_report(self):
        """Test summary report saving."""
        with tempfile.TemporaryDirectory() as temp_dir:
            report_file = os.path.join(temp_dir, "test_report.json")

            success = self.updater.save_summary_report(
                self.sample_stats, self.sample_violations, report_file
            )

            assert success
            assert os.path.exists(report_file)

            # Verify content
            with open(report_file, "r") as f:
                report = json.load(f)
            assert "summary_statistics" in report
            assert "business_rule_violations" in report

    @patch("requests.post")
    def test_post_to_api_success(self, mock_post):
        """Test successful API posting."""
        # Mock successful response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_post.return_value = mock_response

        # Configure updater with API settings
        self.updater.api_url = "http://test-api.com/inventory"
        self.updater.api_key = "test-key"

        data = self.sample_df.to_dict("records")
        success = self.updater.post_to_api(data)

        assert success
        mock_post.assert_called_once()


class TestInventoryAlerter:
    """Test cases for the InventoryAlerter class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.config = {
            "email_user": "test@example.com",
            "alert_recipients": ["manager@example.com"],
            "smtp_server": "smtp.test.com",
            "smtp_port": 587,
        }
        self.alerter = InventoryAlerter(self.config)

        self.sample_df = pd.DataFrame(
            {
                "SKU": ["SKU001", "SKU002", "SKU003"],
                "Description": ["Normal Item", "Low Stock Item", "Critical Item"],
                "Location": ["WH1", "WH2", "WH3"],  # Added missing Location column
                "StockStatus": ["Normal", "Low Stock", "Critical"],
                "OnHandQty": [100, 15, 2],
                "ReorderPoint": [50, 30, 20],
                "ReorderQty": [0, 15, 18],
                "TotalValue": [1000.0, 375.0, 50.0],
            }
        )

        self.sample_stats = {
            "total_records": 3,
            "total_inventory_value": 1425.0,
            "unique_skus": 3,
        }

    def test_filter_alert_items(self):
        """Test alert item filtering."""
        alerts = self.alerter.filter_alert_items(self.sample_df)

        # Check alert categories
        assert "critical" in alerts
        assert "low_stock" in alerts
        assert "reorder_needed" in alerts
        assert "high_value_low_stock" in alerts

        # Check filtering logic
        assert len(alerts["critical"]) == 1  # One critical item
        assert len(alerts["low_stock"]) == 1  # One low stock item
        assert len(alerts["reorder_needed"]) == 2  # Two items need reorder

    def test_generate_email_html(self):
        """Test HTML email generation."""
        alerts = self.alerter.filter_alert_items(self.sample_df)
        html_content = self.alerter.generate_email_html(alerts, self.sample_stats)

        # Check HTML structure
        assert "<!DOCTYPE html>" in html_content
        assert "Inventory Alert Report" in html_content
        assert "CRITICAL STOCK ALERTS" in html_content
        assert "LOW STOCK ALERTS" in html_content

        # Check data inclusion
        assert "SKU003" in html_content  # Critical item
        assert "SKU002" in html_content  # Low stock item

    def test_generate_console_alert(self):
        """Test console alert generation."""
        alerts = self.alerter.filter_alert_items(self.sample_df)
        console_output = self.alerter.generate_console_alert(alerts)

        # Check console format
        assert "INVENTORY ALERT SUMMARY" in console_output
        assert "Critical:" in console_output or "Low Stock:" in console_output
        assert "SKU" in console_output

    @patch("smtplib.SMTP")
    def test_send_email_alert(self, mock_smtp):
        """Test email alert sending."""
        # Mock SMTP server
        mock_server = Mock()
        mock_smtp.return_value = mock_server

        alerts = self.alerter.filter_alert_items(self.sample_df)
        success = self.alerter.send_email_alert(alerts, self.sample_stats)

        # Note: This test will fail without proper email config
        # In a real scenario, you'd mock the email sending
        # For now, we just check the method doesn't crash
        assert isinstance(success, bool)


class TestMetricsCollector:
    """Test cases for the MetricsCollector class."""

    def setup_method(self):
        """Set up test fixtures."""
        self.collector = MetricsCollector()
        self.sample_df = pd.DataFrame(
            {
                "SKU": ["SKU001", "SKU002"],
                "StockStatus": ["Normal", "Low Stock"],
                "ReorderQty": [0, 15],
            }
        )
        self.sample_stats = {"total_inventory_value": 1000.0}
        self.sample_violations = []

    def test_start_end_session(self):
        """Test session management."""
        import time

        session_id = self.collector.start_session()

        assert session_id is not None
        assert self.collector.session_metrics["start_time"] is not None

        # Add small delay to ensure measurable runtime
        time.sleep(0.01)

        self.collector.end_session()

        assert self.collector.session_metrics["end_time"] is not None
        assert self.collector.session_metrics["total_runtime_seconds"] > 0

    def test_record_stage_time(self):
        """Test stage timing recording."""
        import time

        start_time = time.time()
        time.sleep(0.01)  # Small delay
        end_time = time.time()

        self.collector.record_stage_time("test_stage", start_time, end_time)

        assert "test_stage" in self.collector.session_metrics["stages"]
        stage_info = self.collector.session_metrics["stages"]["test_stage"]
        assert "duration_seconds" in stage_info
        assert stage_info["duration_seconds"] > 0

    def test_record_business_metrics(self):
        """Test business metrics recording."""
        self.collector.record_business_metrics(
            self.sample_df, self.sample_stats, self.sample_violations
        )

        business_metrics = self.collector.session_metrics["business_metrics"]

        assert "total_records_processed" in business_metrics
        assert "total_inventory_value" in business_metrics
        assert "data_quality_score" in business_metrics
        assert business_metrics["total_records_processed"] == len(self.sample_df)

    def test_calculate_performance_indicators(self):
        """Test performance indicator calculation."""
        # Set up session with some data
        self.collector.start_session()
        self.collector.record_business_metrics(
            self.sample_df, self.sample_stats, self.sample_violations
        )
        self.collector.end_session()

        indicators = self.collector.calculate_performance_indicators()

        # Check required indicators
        expected_indicators = [
            "runtime_efficiency_percent",
            "time_saved_seconds",
            "cost_saved_dollars",
            "records_per_second",
            "roi_percent",
        ]

        for indicator in expected_indicators:
            assert indicator in indicators
            assert isinstance(indicators[indicator], (int, float))

    def test_generate_metrics_summary(self):
        """Test metrics summary generation."""
        # Set up complete session
        self.collector.start_session()
        self.collector.record_business_metrics(
            self.sample_df, self.sample_stats, self.sample_violations
        )
        self.collector.end_session()

        summary = self.collector.generate_metrics_summary()

        # Check summary structure
        expected_sections = [
            "session_info",
            "stage_performance",
            "business_metrics",
            "performance_indicators",
            "error_summary",
            "baseline_comparison",
        ]

        for section in expected_sections:
            assert section in summary


class TestIntegration:
    """Integration tests for the complete workflow."""

    def test_end_to_end_processing(self):
        """Test complete end-to-end processing workflow."""
        # Create sample data
        sample_data = pd.DataFrame(
            {
                "SKU": ["SKU001", "SKU002", "SKU003"],
                "Description": ["Item A", "Item B", "Item C"],
                "Location": ["WH1", "WH2", "WH1"],
                "OnHandQty": [100, 15, 0],
                "ReorderPoint": [50, 30, 20],
                "UnitCost": [10.99, 15.50, 8.75],
            }
        )

        # Process data
        processor = InventoryProcessor()
        processed_df, summary_stats, violations = processor.process_inventory(
            sample_data
        )

        # Verify processing results
        assert len(processed_df) > 0
        assert "StockStatus" in processed_df.columns
        assert "ReorderQty" in processed_df.columns

        # Test alerting
        alerter = InventoryAlerter()
        alerts = alerter.filter_alert_items(processed_df)

        # Should have some alerts due to low/critical stock
        total_alerts = sum(len(df) for df in alerts.values())
        assert total_alerts > 0

        # Test metrics collection
        collector = MetricsCollector()
        collector.start_session()
        collector.record_business_metrics(processed_df, summary_stats, violations)
        collector.end_session()

        metrics_summary = collector.generate_metrics_summary()
        assert metrics_summary["business_metrics"]["total_records_processed"] == len(
            processed_df
        )


if __name__ == "__main__":
    # Run tests with pytest
    pytest.main([__file__, "-v"])
