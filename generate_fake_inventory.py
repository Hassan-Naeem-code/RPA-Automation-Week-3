# generate_fake_inventory.py
"""
Creates data/inventory_raw.csv with columns:
SKU, Description, Location, OnHandQty, ReorderPoint, UnitCost

This script generates synthetic inventory data for testing the RPA automation workflow.
It includes edge cases like negative quantities and duplicate SKUs to test error handling.
"""

import pandas as pd
from faker import Faker
from random import randint, choice, uniform
from pathlib import Path

fake = Faker()
SKUS = [f"SKU{str(i).zfill(5)}" for i in range(1, 501)]
LOCATIONS = ["WH1", "WH2", "WH3"]

def make_row(sku):
    """Generate a single inventory record with realistic data."""
    return {
        "SKU": sku,
        "Description": fake.word().capitalize() + " " + fake.word().capitalize(),
        "Location": choice(LOCATIONS),
        "OnHandQty": randint(-5, 500),  # Include negative values for edge case testing
        "ReorderPoint": randint(20, 100),
        "UnitCost": round(uniform(2.5, 50.0), 2),
    }

def generate_inventory_data():
    """Generate complete inventory dataset with edge cases."""
    Path("data").mkdir(exist_ok=True)
    
    # Generate main dataset
    data = [make_row(s) for s in SKUS]
    
    # Add some edge cases for testing
    # Duplicate SKUs
    data.append(make_row("SKU00001"))  # Duplicate
    data.append(make_row("SKU00002"))  # Duplicate
    
    # Empty/null-like descriptions
    data.append({
        "SKU": "SKU00999",
        "Description": "",
        "Location": "WH1",
        "OnHandQty": 50,
        "ReorderPoint": 25,
        "UnitCost": 15.99
    })
    
    df = pd.DataFrame(data)
    df.to_csv("data/inventory_raw.csv", index=False)
    print("✅  Fake inventory written to data/inventory_raw.csv")
    print(f"📊  Generated {len(df)} records with edge cases for testing")
    
    # Print summary statistics
    print(f"📈  Summary:")
    print(f"   - Records: {len(df)}")
    print(f"   - Unique SKUs: {df['SKU'].nunique()}")
    print(f"   - Duplicate SKUs: {len(df) - df['SKU'].nunique()}")
    print(f"   - Negative Quantities: {(df['OnHandQty'] < 0).sum()}")
    print(f"   - Low Stock Items: {(df['OnHandQty'] < df['ReorderPoint']).sum()}")

if __name__ == "__main__":
    generate_inventory_data()
