"""
Alert Module for RPA Inventory Management System

This module handles sending notifications and alerts for low stock items,
critical inventory levels, and processing reports via email and other channels.

Author: Hassan Naeem
Date: July 2025
"""

import pandas as pd
import smtplib
import logging
import json
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)


class InventoryAlerter:
    """
    Handles sending alerts and notifications for inventory management system.

    Supports email notifications with formatted reports and can be extended
    for other notification channels like Slack, SMS, etc.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the inventory alerter.

        Args:
            config: Configuration dictionary with email and alert settings
        """
        self.config = config or {}

        # Email configuration
        self.smtp_server = self.config.get("smtp_server", "smtp.gmail.com")
        self.smtp_port = self.config.get("smtp_port", 587)
        self.email_user = self.config.get("email_user")
        self.email_password = self.config.get("email_password")
        self.alert_recipients = self.config.get("alert_recipients", [])

        if isinstance(self.alert_recipients, str):
            self.alert_recipients = [
                email.strip() for email in self.alert_recipients.split(",")
            ]

        # Alert thresholds
        self.critical_threshold = self.config.get("critical_stock_threshold", 5)
        self.low_stock_multiplier = self.config.get("low_stock_multiplier", 1.2)

        logger.info("InventoryAlerter initialized")

    def filter_alert_items(self, df: pd.DataFrame) -> Dict[str, pd.DataFrame]:
        """
        Filter inventory items that require alerts.

        Args:
            df: Processed inventory DataFrame

        Returns:
            Dictionary containing different categories of alert items
        """
        logger.info("Filtering items for alerts")

        alerts = {
            "critical": df[df["StockStatus"].isin(["Critical", "Out of Stock"])].copy(),
            "low_stock": df[df["StockStatus"] == "Low Stock"].copy(),
            "reorder_needed": df[df["ReorderQty"] > 0].copy(),
            "high_value_low_stock": df[
                (df["StockStatus"].isin(["Low Stock", "Critical", "Out of Stock"]))
                & (df["TotalValue"] > df["TotalValue"].quantile(0.8))
            ].copy(),
        }

        # Log alert counts
        for category, items in alerts.items():
            logger.info(f"{category.replace('_', ' ').title()}: {len(items)} items")

        return alerts

    def generate_email_html(
        self, alerts: Dict[str, pd.DataFrame], summary_stats: Dict[str, Any]
    ) -> str:
        """
        Generate HTML email content for inventory alerts.

        Args:
            alerts: Dictionary of alert categories and their DataFrames
            summary_stats: Summary statistics from processing

        Returns:
            HTML string for email body
        """
        logger.info("Generating HTML email content")

        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background-color: #366092; color: white; padding: 20px; text-align: center; }}
                .summary {{ background-color: #f8f9fa; padding: 15px; margin: 20px 0; border-radius: 5px; }}
                .alert-section {{ margin: 20px 0; }}
                .alert-title {{ color: #dc3545; font-size: 18px; font-weight: bold; margin-bottom: 10px; }}
                table {{ border-collapse: collapse; width: 100%; margin-bottom: 20px; }}
                th, td {{ border: 1px solid #ddd; padding: 8px; text-align: left; }}
                th {{ background-color: #366092; color: white; }}
                .critical {{ background-color: #ffe6e6; }}
                .low-stock {{ background-color: #fff3cd; }}
                .footer {{ font-size: 12px; color: #666; margin-top: 30px; text-align: center; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Inventory Alert Report</h1>
                <p>Generated on {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
            </div>
            
            <div class="summary">
                <h3>Processing Summary</h3>
                <ul>
                    <li><strong>Total Records Processed:</strong> {summary_stats.get('total_records', 'N/A')}</li>
                    <li><strong>Unique SKUs:</strong> {summary_stats.get('unique_skus', 'N/A')}</li>
                    <li><strong>Total Inventory Value:</strong> ${summary_stats.get('total_inventory_value', 0):,.2f}</li>
                    <li><strong>Critical/Out of Stock Items:</strong> {len(alerts['critical'])}</li>
                    <li><strong>Low Stock Items:</strong> {len(alerts['low_stock'])}</li>
                    <li><strong>Items Needing Reorder:</strong> {len(alerts['reorder_needed'])}</li>
                </ul>
            </div>
        """

        # Critical items section
        if not alerts["critical"].empty:
            html_content += f"""
            <div class="alert-section">
                <div class="alert-title">🚨 CRITICAL STOCK ALERTS ({len(alerts['critical'])} items)</div>
                <table>
                    <tr>
                        <th>SKU</th>
                        <th>Description</th>
                        <th>Location</th>
                        <th>On Hand</th>
                        <th>Reorder Point</th>
                        <th>Status</th>
                        <th>Reorder Qty</th>
                        <th>Value at Risk</th>
                    </tr>
            """

            for _, row in alerts["critical"].iterrows():
                status_class = (
                    "critical"
                    if row["StockStatus"] in ["Critical", "Out of Stock"]
                    else ""
                )
                html_content += f"""
                    <tr class="{status_class}">
                        <td>{row['SKU']}</td>
                        <td>{row['Description']}</td>
                        <td>{row['Location']}</td>
                        <td>{row['OnHandQty']}</td>
                        <td>{row['ReorderPoint']}</td>
                        <td>{row['StockStatus']}</td>
                        <td>{row['ReorderQty']}</td>
                        <td>${row.get('TotalValue', 0):.2f}</td>
                    </tr>
                """

            html_content += "</table></div>"

        # Low stock items section
        if not alerts["low_stock"].empty:
            html_content += f"""
            <div class="alert-section">
                <div class="alert-title">⚠️ LOW STOCK ALERTS ({len(alerts['low_stock'])} items)</div>
                <table>
                    <tr>
                        <th>SKU</th>
                        <th>Description</th>
                        <th>Location</th>
                        <th>On Hand</th>
                        <th>Reorder Point</th>
                        <th>Reorder Qty</th>
                        <th>Days of Supply</th>
                    </tr>
            """

            for _, row in alerts["low_stock"].iterrows():
                days_supply = (
                    f"{row.get('DaysOfSupply', 0):.1f}"
                    if pd.notna(row.get("DaysOfSupply"))
                    else "N/A"
                )
                html_content += f"""
                    <tr class="low-stock">
                        <td>{row['SKU']}</td>
                        <td>{row['Description']}</td>
                        <td>{row['Location']}</td>
                        <td>{row['OnHandQty']}</td>
                        <td>{row['ReorderPoint']}</td>
                        <td>{row['ReorderQty']}</td>
                        <td>{days_supply}</td>
                    </tr>
                """

            html_content += "</table></div>"

        # High value low stock items
        if not alerts["high_value_low_stock"].empty:
            html_content += f"""
            <div class="alert-section">
                <div class="alert-title">💰 HIGH VALUE LOW STOCK ITEMS ({len(alerts['high_value_low_stock'])} items)</div>
                <p>These high-value items require immediate attention to prevent significant revenue impact.</p>
                <table>
                    <tr>
                        <th>SKU</th>
                        <th>Description</th>
                        <th>Location</th>
                        <th>On Hand</th>
                        <th>Status</th>
                        <th>Total Value</th>
                        <th>Potential Loss</th>
                    </tr>
            """

            for _, row in alerts["high_value_low_stock"].iterrows():
                potential_loss = row["ReorderQty"] * row["UnitCost"]
                html_content += f"""
                    <tr>
                        <td>{row['SKU']}</td>
                        <td>{row['Description']}</td>
                        <td>{row['Location']}</td>
                        <td>{row['OnHandQty']}</td>
                        <td>{row['StockStatus']}</td>
                        <td>${row['TotalValue']:.2f}</td>
                        <td>${potential_loss:.2f}</td>
                    </tr>
                """

            html_content += "</table></div>"

        # Footer
        html_content += f"""
            <div class="footer">
                <p>This is an automated report from the RPA Inventory Management System.</p>
                <p>For questions or issues, please contact the IT Support team.</p>
            </div>
        </body>
        </html>
        """

        return html_content

    def send_email_alert(
        self,
        alerts: Dict[str, pd.DataFrame],
        summary_stats: Dict[str, Any],
        subject: str = None,
        attach_report: bool = True,
        report_file_path: str = None,
    ) -> bool:
        """
        Send email alert with inventory information.

        Args:
            alerts: Dictionary of alert categories and DataFrames
            summary_stats: Summary statistics
            subject: Email subject line
            attach_report: Whether to attach detailed report
            report_file_path: Path to report file to attach

        Returns:
            True if email sent successfully, False otherwise
        """
        if not self.email_user or not self.alert_recipients:
            logger.warning("Email configuration missing, skipping email alert")
            return False

        try:
            logger.info(
                f"Sending email alert to {len(self.alert_recipients)} recipients"
            )

            # Create message
            msg = MIMEMultipart()
            msg["From"] = self.email_user
            msg["To"] = ", ".join(self.alert_recipients)

            # Generate subject if not provided
            if not subject:
                total_alerts = sum(len(df) for df in alerts.values() if not df.empty)
                critical_count = len(alerts.get("critical", []))
                subject = f"Inventory Alert: {total_alerts} items need attention"
                if critical_count > 0:
                    subject += f" ({critical_count} CRITICAL)"

            msg["Subject"] = subject

            # Generate and attach HTML body
            html_body = self.generate_email_html(alerts, summary_stats)
            msg.attach(MIMEText(html_body, "html"))

            # Attach report file if requested
            if attach_report and report_file_path and Path(report_file_path).exists():
                with open(report_file_path, "rb") as attachment:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.read())

                encoders.encode_base64(part)
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename= {Path(report_file_path).name}",
                )
                msg.attach(part)

            # Send email
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            server.starttls()
            server.login(self.email_user, self.email_password)
            text = msg.as_string()
            server.sendmail(self.email_user, self.alert_recipients, text)
            server.quit()

            logger.info("Email alert sent successfully")
            return True

        except Exception as e:
            logger.error(f"Error sending email alert: {e}")
            return False

    def generate_console_alert(self, alerts: Dict[str, pd.DataFrame]) -> str:
        """
        Generate console/text-based alert summary.

        Args:
            alerts: Dictionary of alert categories and DataFrames

        Returns:
            Formatted string for console output
        """
        output = []
        output.append("=" * 60)
        output.append("INVENTORY ALERT SUMMARY")
        output.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        output.append("=" * 60)

        for category, df in alerts.items():
            if not df.empty:
                category_name = category.replace("_", " ").title()
                output.append(f"\n{category_name}: {len(df)} items")
                output.append("-" * 30)

                for _, row in df.head(5).iterrows():  # Show top 5 items
                    output.append(
                        f"  • {row['SKU']} - {row['Description']} ({row['Location']})"
                    )
                    output.append(
                        f"    On Hand: {row['OnHandQty']}, Reorder: {row['ReorderPoint']}, Status: {row['StockStatus']}"
                    )

                if len(df) > 5:
                    output.append(f"    ... and {len(df) - 5} more items")

        output.append("\n" + "=" * 60)

        return "\n".join(output)

    def save_alert_log(
        self,
        alerts: Dict[str, pd.DataFrame],
        summary_stats: Dict[str, Any],
        log_file: str = "logs/alerts.log",
    ) -> bool:
        """
        Save alert information to log file.

        Args:
            alerts: Dictionary of alert categories and DataFrames
            summary_stats: Summary statistics
            log_file: Path to alert log file

        Returns:
            True if successful, False otherwise
        """
        try:
            # Ensure log directory exists
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)

            alert_data = {
                "timestamp": datetime.now().isoformat(),
                "summary_stats": summary_stats,
                "alert_counts": {category: len(df) for category, df in alerts.items()},
                "total_alerts": sum(len(df) for df in alerts.values()),
                "critical_items": (
                    alerts["critical"]["SKU"].tolist()
                    if not alerts["critical"].empty
                    else []
                ),
                "low_stock_items": (
                    alerts["low_stock"]["SKU"].tolist()
                    if not alerts["low_stock"].empty
                    else []
                ),
            }

            with open(log_file, "a") as f:
                f.write(json.dumps(alert_data) + "\n")

            logger.info(f"Alert information logged to {log_file}")
            return True

        except Exception as e:
            logger.error(f"Error saving alert log: {e}")
            return False

    def send_alerts(
        self,
        df: pd.DataFrame,
        summary_stats: Dict[str, Any],
        send_email: bool = True,
        save_log: bool = True,
        show_console: bool = True,
    ) -> Dict[str, bool]:
        """
        Main method to send all types of alerts.

        Args:
            df: Processed inventory DataFrame
            summary_stats: Summary statistics
            send_email: Whether to send email alerts
            save_log: Whether to save alert log
            show_console: Whether to show console output

        Returns:
            Dictionary showing success status for each alert type
        """
        logger.info("Starting alert generation and distribution")

        # Filter items needing alerts
        alerts = self.filter_alert_items(df)

        results = {}

        # Send email alert
        if send_email:
            results["email"] = self.send_email_alert(alerts, summary_stats)

        # Save alert log
        if save_log:
            results["log"] = self.save_alert_log(alerts, summary_stats)

        # Show console alert
        if show_console:
            console_alert = self.generate_console_alert(alerts)
            print(console_alert)
            results["console"] = True

        logger.info(f"Alert distribution completed. Results: {results}")
        return results


def send_inventory_alerts(
    df: pd.DataFrame,
    summary_stats: Dict[str, Any],
    config: Optional[Dict[str, Any]] = None,
    send_email: bool = True,
) -> Dict[str, bool]:
    """
    Convenience function for sending inventory alerts.

    Args:
        df: Processed inventory DataFrame
        summary_stats: Summary statistics
        config: Optional configuration dictionary
        send_email: Whether to send email alerts

    Returns:
        Dictionary showing success status for each alert type
    """
    alerter = InventoryAlerter(config)
    return alerter.send_alerts(df, summary_stats, send_email=send_email)


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # Create sample data for testing
    sample_data = {
        "SKU": ["SKU001", "SKU002", "SKU003", "SKU004"],
        "Description": [
            "Critical Item",
            "Low Stock Item",
            "Normal Item",
            "Out of Stock Item",
        ],
        "Location": ["WH1", "WH2", "WH3", "WH1"],
        "OnHandQty": [2, 15, 100, 0],
        "ReorderPoint": [25, 30, 50, 20],
        "UnitCost": [10.99, 15.50, 8.99, 25.00],
        "ReorderQty": [23, 15, 0, 20],
        "StockStatus": ["Critical", "Low Stock", "Normal", "Out of Stock"],
        "TotalValue": [21.98, 232.50, 899.00, 0.00],
        "DaysOfSupply": [2.4, 15.0, 60.0, 0.0],
    }

    df = pd.DataFrame(sample_data)
    summary = {
        "total_records": 4,
        "unique_skus": 4,
        "total_inventory_value": 1153.48,
        "processing_timestamp": datetime.now().isoformat(),
    }

    # Test without actual email sending
    config = {"email_user": None}
    results = send_inventory_alerts(df, summary, config, send_email=False)
    print(f"Alert results: {results}")
