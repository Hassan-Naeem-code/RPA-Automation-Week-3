"""
Data Extraction Module for RPA Inventory Management System

This module handles the extraction of inventory data from various sources,
primarily CSV files but designed to be extensible for other formats.

Author: Hassan Naeem
Date: July 2025
"""

import pandas as pd
import logging
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime

# Configure logging
logger = logging.getLogger(__name__)


class InventoryExtractor:
    """
    Handles extraction of inventory data from various sources.

    Currently supports CSV files with plans for Excel, JSON, and API sources.
    """

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the inventory extractor.

        Args:
            config: Configuration dictionary with extraction parameters
        """
        self.config = config or {}
        self.supported_formats = [".csv", ".xlsx", ".xls"]
        logger.info("InventoryExtractor initialized")

    def extract_from_csv(self, file_path: str) -> pd.DataFrame:
        """
        Extract inventory data from CSV file.

        Args:
            file_path: Path to the CSV file

        Returns:
            DataFrame containing the extracted data

        Raises:
            FileNotFoundError: If the file doesn't exist
            pd.errors.EmptyDataError: If the file is empty
            ValueError: If required columns are missing
        """
        logger.info(f"Starting CSV extraction from: {file_path}")

        # Validate file exists
        if not Path(file_path).exists():
            raise FileNotFoundError(f"Input file not found: {file_path}")

        try:
            # Read CSV with error handling
            df = pd.read_csv(file_path)

            # Validate data is not empty
            if df.empty:
                raise pd.errors.EmptyDataError("CSV file is empty")

            # Validate required columns exist
            required_columns = [
                "SKU",
                "Description",
                "Location",
                "OnHandQty",
                "ReorderPoint",
                "UnitCost",
            ]
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                raise ValueError(f"Missing required columns: {missing_columns}")

            logger.info(f"Successfully extracted {len(df)} records from CSV")
            logger.info(f"Columns found: {list(df.columns)}")

            return df

        except pd.errors.EmptyDataError as e:
            logger.error(f"Empty data error: {e}")
            raise
        except pd.errors.ParserError as e:
            logger.error(f"CSV parsing error: {e}")
            raise ValueError(f"Error parsing CSV file: {e}")
        except Exception as e:
            logger.error(f"Unexpected error during CSV extraction: {e}")
            raise

    def extract_from_excel(
        self, file_path: str, sheet_name: Optional[str] = None
    ) -> pd.DataFrame:
        """
        Extract inventory data from Excel file.

        Args:
            file_path: Path to the Excel file
            sheet_name: Name of the sheet to read (default: first sheet)

        Returns:
            DataFrame containing the extracted data
        """
        logger.info(f"Starting Excel extraction from: {file_path}")

        if not Path(file_path).exists():
            raise FileNotFoundError(f"Input file not found: {file_path}")

        try:
            df = pd.read_excel(file_path, sheet_name=sheet_name)

            if df.empty:
                raise ValueError("Excel file is empty")

            logger.info(f"Successfully extracted {len(df)} records from Excel")
            return df

        except Exception as e:
            logger.error(f"Error during Excel extraction: {e}")
            raise

    def extract_data(self, file_path: str, **kwargs) -> pd.DataFrame:
        """
        Main extraction method that determines file type and extracts accordingly.

        Args:
            file_path: Path to the input file
            **kwargs: Additional arguments for specific extractors

        Returns:
            DataFrame containing the extracted data
        """
        file_path_obj = Path(file_path)
        file_extension = file_path_obj.suffix.lower()

        logger.info(f"Extracting data from: {file_path}")
        logger.info(f"File type detected: {file_extension}")

        if file_extension == ".csv":
            return self.extract_from_csv(str(file_path_obj))
        elif file_extension in [".xlsx", ".xls"]:
            return self.extract_from_excel(str(file_path_obj))
        else:
            raise ValueError(f"Unsupported file format: {file_extension}")

    def get_file_info(self, file_path: str) -> Dict[str, Any]:
        """
        Get detailed information about a file.

        Args:
            file_path: Path to the file

        Returns:
            Dictionary containing file information
        """
        file_path_obj = Path(file_path)

        if not file_path_obj.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            stat_info = file_path_obj.stat()
            return {
                "file_name": file_path_obj.name,
                "file_size_bytes": stat_info.st_size,
                "file_size_mb": round(stat_info.st_size / (1024 * 1024), 2),
                "modified_date": datetime.fromtimestamp(stat_info.st_mtime),
                "file_extension": file_path_obj.suffix.lower(),
                "absolute_path": str(file_path_obj.absolute()),
            }
        except Exception as e:
            logger.error(f"Error getting file info: {e}")
            raise


def extract_inventory_data(
    file_path: str, config: Optional[Dict[str, Any]] = None
) -> pd.DataFrame:
    """
    Convenience function for extracting inventory data.

    Args:
        file_path: Path to the input file
        config: Optional configuration dictionary

    Returns:
        DataFrame containing the extracted inventory data
    """
    extractor = InventoryExtractor(config)
    return extractor.extract_data(file_path)


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    try:
        # Test extraction (assumes data file exists)
        df = extract_inventory_data("../data/inventory_raw.csv")
        print(f"Extracted {len(df)} records")
        print(f"Columns: {list(df.columns)}")
        print(df.head())
    except Exception as e:
        print(f"Error: {e}")
