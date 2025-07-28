"""
Data Processing Module for RPA Inventory Management System

This module handles data cleaning, validation, transformation, and business logic
for inventory management including reorder calculations and low stock detection.

Author: Hassan Naeem
Date: July 2025
"""

import pandas as pd
import numpy as np
import logging
from typing import Dict, List, Any, Tuple, Optional
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)


class InventoryProcessor:
    """
    Handles all data processing operations for inventory management.

    Includes data cleaning, validation, business rule application,
    and preparation for reporting and alerts.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the inventory processor.

        Args:
            config: Configuration dictionary with processing parameters
        """
        self.config = config or {}
        self.low_stock_multiplier = self.config.get("low_stock_multiplier", 1.2)
        self.critical_stock_threshold = self.config.get("critical_stock_threshold", 5)

        # Processing statistics
        self.stats = {
            "records_processed": 0,
            "duplicates_removed": 0,
            "invalid_records": 0,
            "negative_quantities_fixed": 0,
            "low_stock_items": 0,
            "critical_stock_items": 0,
        }

        logger.info("InventoryProcessor initialized")

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Perform comprehensive data cleaning on inventory data.

        Args:
            df: Raw inventory DataFrame

        Returns:
            Cleaned DataFrame
        """
        logger.info(f"Starting data cleaning for {len(df)} records")
        original_count = len(df)

        # Create a copy to avoid modifying original data
        df_clean = df.copy()

        # Remove completely empty rows
        df_clean = df_clean.dropna(how="all")

        # Clean SKU field
        df_clean["SKU"] = df_clean["SKU"].astype(str).str.strip().str.upper()
        df_clean = df_clean[df_clean["SKU"] != ""]

        # Clean Description field
        df_clean["Description"] = df_clean["Description"].astype(str).str.strip()
        df_clean["Description"] = df_clean["Description"].replace("", "Unknown Item")

        # Clean Location field
        df_clean["Location"] = df_clean["Location"].astype(str).str.strip().str.upper()

        # Handle numeric fields
        numeric_fields = ["OnHandQty", "ReorderPoint", "UnitCost"]
        for field in numeric_fields:
            # Convert to numeric, coercing errors to NaN
            df_clean[field] = pd.to_numeric(df_clean[field], errors="coerce")

            # Fill NaN values with 0 for quantities, appropriate defaults for others
            if field in ["OnHandQty", "ReorderPoint"]:
                df_clean[field] = df_clean[field].fillna(0)
            else:  # UnitCost
                df_clean[field] = df_clean[field].fillna(df_clean[field].median())

        # Fix negative quantities (business rule: treat as 0)
        negative_qty_mask = df_clean["OnHandQty"] < 0
        self.stats["negative_quantities_fixed"] = negative_qty_mask.sum()
        df_clean.loc[negative_qty_mask, "OnHandQty"] = 0

        # Remove records with invalid reorder points or unit costs
        valid_mask = (df_clean["ReorderPoint"] >= 0) & (df_clean["UnitCost"] > 0)
        df_clean = df_clean[valid_mask]

        self.stats["records_processed"] = len(df_clean)
        self.stats["invalid_records"] = original_count - len(df_clean)

        logger.info(f"Data cleaning completed: {len(df_clean)} records remaining")
        logger.info(f"Removed {original_count - len(df_clean)} invalid records")
        logger.info(
            f"Fixed {self.stats['negative_quantities_fixed']} negative quantities"
        )

        return df_clean

    def remove_duplicates(
        self, df: pd.DataFrame, strategy: str = "keep_last"
    ) -> pd.DataFrame:
        """
        Remove duplicate records based on SKU and Location.

        Args:
            df: DataFrame to deduplicate
            strategy: 'keep_first', 'keep_last', or 'remove_all'

        Returns:
            Deduplicated DataFrame
        """
        logger.info("Starting duplicate removal")
        original_count = len(df)

        if strategy == "remove_all":
            # Remove all duplicates including originals
            duplicated_mask = df.duplicated(subset=["SKU", "Location"], keep=False)
            df_dedup = df[~duplicated_mask]
        else:
            # Keep first or last occurrence
            keep = "first" if strategy == "keep_first" else "last"
            df_dedup = df.drop_duplicates(subset=["SKU", "Location"], keep=keep)

        self.stats["duplicates_removed"] = original_count - len(df_dedup)

        logger.info(f"Removed {self.stats['duplicates_removed']} duplicate records")

        return df_dedup

    def calculate_reorder_metrics(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Calculate reorder quantities and stock status indicators.

        Args:
            df: Cleaned inventory DataFrame

        Returns:
            DataFrame with additional calculated columns
        """
        logger.info("Calculating reorder metrics")

        df_calc = df.copy()

        # Calculate reorder quantity needed
        df_calc["ReorderQty"] = np.maximum(
            0, df_calc["ReorderPoint"] - df_calc["OnHandQty"]
        )

        # Calculate stock status
        df_calc["StockStatus"] = "Normal"

        # Low stock: below reorder point but above critical threshold
        low_stock_mask = (df_calc["OnHandQty"] < df_calc["ReorderPoint"]) & (
            df_calc["OnHandQty"] > self.critical_stock_threshold
        )
        df_calc.loc[low_stock_mask, "StockStatus"] = "Low Stock"

        # Critical stock: at or below critical threshold
        critical_stock_mask = df_calc["OnHandQty"] <= self.critical_stock_threshold
        df_calc.loc[critical_stock_mask, "StockStatus"] = "Critical"

        # Out of stock: zero quantity
        out_of_stock_mask = df_calc["OnHandQty"] == 0
        df_calc.loc[out_of_stock_mask, "StockStatus"] = "Out of Stock"

        # Calculate days of supply (assuming daily usage rate)
        df_calc["DaysOfSupply"] = np.where(
            df_calc["ReorderPoint"] > 0,
            df_calc["OnHandQty"]
            / (df_calc["ReorderPoint"] / 30),  # Assume 30-day reorder cycle
            np.inf,
        )

        # Calculate total value of inventory
        df_calc["TotalValue"] = df_calc["OnHandQty"] * df_calc["UnitCost"]

        # Add processing timestamp
        df_calc["ProcessedAt"] = datetime.now().isoformat()

        # Update statistics
        self.stats["low_stock_items"] = (df_calc["StockStatus"] == "Low Stock").sum()
        self.stats["critical_stock_items"] = (
            df_calc["StockStatus"].isin(["Critical", "Out of Stock"])
        ).sum()

        logger.info(f"Calculated metrics for {len(df_calc)} items")
        logger.info(f"Low stock items: {self.stats['low_stock_items']}")
        logger.info(
            f"Critical/Out of stock items: {self.stats['critical_stock_items']}"
        )

        return df_calc

    def validate_business_rules(
        self, df: pd.DataFrame
    ) -> Tuple[pd.DataFrame, List[Dict[str, Any]]]:
        """
        Validate business rules and flag violations.

        Args:
            df: Processed DataFrame

        Returns:
            Tuple of (validated DataFrame, list of violations)
        """
        logger.info("Validating business rules")

        violations = []
        df_validated = df.copy()

        # Rule 1: Reorder point should be reasonable (not more than 50% of max observed quantity)
        max_qty_per_sku = df.groupby("SKU")["OnHandQty"].max()

        for idx, row in df_validated.iterrows():
            max_qty = max_qty_per_sku.get(row["SKU"], row["OnHandQty"])
            if row["ReorderPoint"] > max_qty * 0.5:
                violations.append(
                    {
                        "SKU": row["SKU"],
                        "Location": row["Location"],
                        "Rule": "High Reorder Point",
                        "Details": f"Reorder point ({row['ReorderPoint']}) > 50% of max quantity ({max_qty})",
                    }
                )

        # Rule 2: Unit cost should be within reasonable range
        cost_outliers = df_validated[
            (df_validated["UnitCost"] < 0.1) | (df_validated["UnitCost"] > 1000)
        ]

        for idx, row in cost_outliers.iterrows():
            violations.append(
                {
                    "SKU": row["SKU"],
                    "Location": row["Location"],
                    "Rule": "Unusual Unit Cost",
                    "Details": f"Unit cost ${row['UnitCost']:.2f} may be incorrect",
                }
            )

        # Add validation flag
        df_validated["ValidationStatus"] = "Passed"
        violation_skus = {v["SKU"] for v in violations}
        df_validated.loc[
            df_validated["SKU"].isin(violation_skus), "ValidationStatus"
        ] = "Flagged"

        logger.info(f"Found {len(violations)} business rule violations")

        return df_validated, violations

    def generate_summary_stats(self, df: pd.DataFrame) -> Dict[str, Any]:
        """
        Generate summary statistics for the processed inventory data.

        Args:
            df: Processed DataFrame

        Returns:
            Dictionary containing summary statistics
        """
        logger.info("Generating summary statistics")

        summary = {
            "processing_timestamp": datetime.now().isoformat(),
            "total_records": len(df),
            "unique_skus": df["SKU"].nunique(),
            "locations": sorted(df["Location"].unique().tolist()),
            "total_inventory_value": float(df["TotalValue"].sum()),
            "average_unit_cost": float(df["UnitCost"].mean()),
            "stock_status_breakdown": df["StockStatus"].value_counts().to_dict(),
            "top_5_high_value_items": df.nlargest(5, "TotalValue")[
                ["SKU", "Description", "TotalValue"]
            ].to_dict("records"),
            "processing_stats": self.stats.copy(),
        }

        return summary

    def process_inventory(
        self,
        df: pd.DataFrame,
        remove_duplicates: bool = True,
        validate_rules: bool = True,
    ) -> Tuple[pd.DataFrame, Dict[str, Any], List[Dict[str, Any]]]:
        """
        Main processing pipeline that orchestrates all processing steps.

        Args:
            df: Raw inventory DataFrame
            remove_duplicates: Whether to remove duplicate records
            validate_rules: Whether to validate business rules

        Returns:
            Tuple of (processed DataFrame, summary statistics, violations list)
        """
        logger.info("Starting complete inventory processing pipeline")

        # Step 1: Clean data
        df_processed = self.clean_data(df)

        # Step 2: Remove duplicates if requested
        if remove_duplicates:
            df_processed = self.remove_duplicates(df_processed)

        # Step 3: Calculate reorder metrics
        df_processed = self.calculate_reorder_metrics(df_processed)

        # Step 4: Validate business rules if requested
        violations = []
        if validate_rules:
            df_processed, violations = self.validate_business_rules(df_processed)

        # Step 5: Generate summary statistics
        summary_stats = self.generate_summary_stats(df_processed)

        logger.info("Inventory processing pipeline completed successfully")

        return df_processed, summary_stats, violations


def process_inventory_data(
    df: pd.DataFrame, config: Optional[Dict[str, Any]] = None
) -> Tuple[pd.DataFrame, Dict[str, Any], List[Dict[str, Any]]]:
    """
    Convenience function for processing inventory data.

    Args:
        df: Raw inventory DataFrame
        config: Optional configuration dictionary

    Returns:
        Tuple of (processed DataFrame, summary statistics, violations list)
    """
    processor = InventoryProcessor(config)
    return processor.process_inventory(df)


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # Create sample data for testing
    sample_data = {
        "SKU": ["SKU001", "SKU002", "SKU001", "SKU003"],
        "Description": ["Item A", "Item B", "Item A", ""],
        "Location": ["WH1", "WH2", "WH1", "WH3"],
        "OnHandQty": [50, -5, 60, 25],
        "ReorderPoint": [25, 30, 25, 20],
        "UnitCost": [10.99, 15.50, 10.99, 0.99],
    }

    df = pd.DataFrame(sample_data)
    processed_df, stats, violations = process_inventory_data(df)

    print("Processed Data:")
    print(processed_df)
    print("\nSummary Statistics:")
    print(stats)
    print("\nViolations:")
    print(violations)
