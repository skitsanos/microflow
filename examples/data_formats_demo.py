"""Example demonstrating CSV and Excel data format operations"""

import asyncio
import os
from pathlib import Path

from microflow import (
    Workflow, task, JSONStateStore,
    csv_read, csv_write, json_to_csv, csv_to_json,
    excel_read, excel_write, excel_to_json
)


@task(name="setup_sample_data")
def setup_sample_data(ctx):
    """Create sample data for testing format conversions"""
    return {
        "employees": [
            {"id": 1, "name": "Alice Johnson", "department": "Engineering", "salary": 85000, "start_date": "2023-01-15"},
            {"id": 2, "name": "Bob Smith", "department": "Sales", "salary": 62000, "start_date": "2023-03-20"},
            {"id": 3, "name": "Carol Davis", "department": "Marketing", "salary": 58000, "start_date": "2023-02-10"},
            {"id": 4, "name": "David Wilson", "department": "Engineering", "salary": 92000, "start_date": "2022-11-05"},
            {"id": 5, "name": "Eve Brown", "department": "HR", "salary": 55000, "start_date": "2023-04-12"}
        ],
        "products": [
            {"sku": "LAPTOP001", "name": "Business Laptop", "category": "Electronics", "price": 1299.99, "stock": 45},
            {"sku": "CHAIR002", "name": "Ergonomic Chair", "category": "Furniture", "price": 399.99, "stock": 23},
            {"sku": "DESK003", "name": "Standing Desk", "category": "Furniture", "price": 799.99, "stock": 12}
        ]
    }


# Create nodes for data format operations
write_employees_csv = csv_write(
    data_key="employees",
    file_path="./output/employees.csv",
    name="write_employees_csv"
)

write_products_csv = csv_write(
    data_key="products",
    file_path="./output/products.csv",
    name="write_products_csv"
)

read_employees_csv = csv_read(
    file_path="./output/employees.csv",
    output_key="employees_from_csv",
    name="read_employees_csv"
)

# Try Excel operations (will work if pandas/openpyxl are available)
write_employees_excel = excel_write(
    data_key="employees",
    file_path="./output/employees.xlsx",
    sheet_name="Employees",
    name="write_employees_excel"
)

read_employees_excel = excel_read(
    file_path="./output/employees.xlsx",
    sheet_name="Employees",
    output_key="employees_from_excel",
    name="read_employees_excel"
)

# Convert between formats
convert_csv_to_json = csv_to_json(
    file_path="./output/employees.csv",
    output_file="./output/employees.json",
    output_key="employees_json",
    name="convert_csv_to_json"
)

convert_json_to_csv = json_to_csv(
    data_key="products",
    output_file="./output/products_from_json.csv",
    name="convert_json_to_csv"
)

convert_excel_to_json = excel_to_json(
    file_path="./output/employees.xlsx",
    sheet_name="Employees",
    output_file="./output/employees_from_excel.json",
    output_key="employees_excel_json",
    name="convert_excel_to_json"
)


@task(name="verify_conversions")
def verify_conversions(ctx):
    """Verify that all format conversions worked correctly"""
    results = {
        "verification_results": {},
        "files_created": [],
        "conversion_summary": {}
    }

    # Check which operations succeeded
    csv_ops_success = ctx.get("csv_success", False)
    excel_ops_success = ctx.get("excel_success", False)
    conversion_success = ctx.get("conversion_success", False)

    # Count files created
    output_dir = Path("./output")
    if output_dir.exists():
        results["files_created"] = [f.name for f in output_dir.glob("*") if f.is_file()]

    # Verify data integrity
    original_employees = ctx.get("employees", [])
    csv_employees = ctx.get("employees_from_csv", [])
    excel_employees = ctx.get("employees_from_excel", [])
    json_employees = ctx.get("employees_json", [])

    results["verification_results"] = {
        "original_employee_count": len(original_employees),
        "csv_employee_count": len(csv_employees),
        "excel_employee_count": len(excel_employees) if excel_employees else "Excel not available",
        "json_employee_count": len(json_employees) if json_employees else 0,
        "csv_integrity_check": len(csv_employees) == len(original_employees) if csv_employees else False,
        "excel_available": excel_ops_success,
        "all_csv_operations_successful": csv_ops_success
    }

    results["conversion_summary"] = {
        "csv_read_write": "✅ Success" if csv_ops_success else "❌ Failed",
        "excel_operations": "✅ Success" if excel_ops_success else "⚠️  Requires pandas/openpyxl",
        "format_conversions": "✅ Success" if conversion_success else "❌ Failed"
    }

    # Print summary
    print("\n=== Data Format Operations Summary ===")
    print(f"Files created: {len(results['files_created'])}")
    for file in results["files_created"]:
        print(f"  - {file}")

    print(f"\nOperations Summary:")
    for operation, status in results["conversion_summary"].items():
        print(f"  {operation}: {status}")

    print(f"\nData Integrity:")
    verification = results["verification_results"]
    print(f"  Original employees: {verification['original_employee_count']}")
    print(f"  CSV roundtrip: {verification['csv_employee_count']} (integrity: {verification['csv_integrity_check']})")
    if verification["excel_available"]:
        print(f"  Excel roundtrip: {verification['excel_employee_count']}")
    else:
        print(f"  Excel operations: Not available (install: pip install pandas openpyxl)")

    return results


async def main():
    """Demonstrate comprehensive data format operations"""
    print("Starting data format operations demo...")

    # Ensure output directory exists
    Path("./output").mkdir(exist_ok=True)

    # Build workflow with CSV operations (always available)
    csv_workflow_tasks = [
        setup_sample_data,
        write_employees_csv,
        write_products_csv,
        read_employees_csv,
        convert_csv_to_json,
        convert_json_to_csv
    ]

    # Try to add Excel operations
    try:
        import pandas as pd
        import openpyxl
        print("✅ Excel support available (pandas + openpyxl found)")
        excel_workflow_tasks = [
            write_employees_excel,
            read_employees_excel,
            convert_excel_to_json
        ]
        all_tasks = csv_workflow_tasks + excel_workflow_tasks + [verify_conversions]
    except ImportError as e:
        print(f"⚠️  Excel support not available: {e}")
        print("   Install with: pip install pandas openpyxl")
        all_tasks = csv_workflow_tasks + [verify_conversions]

    # Set up task dependencies
    setup_sample_data >> write_employees_csv >> read_employees_csv
    setup_sample_data >> write_products_csv
    setup_sample_data >> convert_json_to_csv
    read_employees_csv >> convert_csv_to_json

    if len(all_tasks) > len(csv_workflow_tasks) + 1:  # Excel tasks included
        setup_sample_data >> write_employees_excel >> read_employees_excel >> convert_excel_to_json
        convert_excel_to_json >> verify_conversions
    else:
        convert_csv_to_json >> verify_conversions
        convert_json_to_csv >> verify_conversions

    # Create and run workflow
    workflow = Workflow(all_tasks, name="data_formats_demo")
    store = JSONStateStore("./data")

    try:
        print("\n🚀 Running data format workflow...")
        result = await workflow.run("data_formats_demo_001", store, {})
        print("✅ Data format operations completed successfully!")

        # Keep demo files for inspection
        print("\n📁 Demo files saved in ./output/ directory for inspection")

    except Exception as e:
        print(f"❌ Workflow failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())