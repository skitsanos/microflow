# Data Format Nodes

Data format nodes enable seamless conversion between different file formats including CSV, Excel, and JSON. They provide robust handling for data import/export operations with comprehensive error handling and validation.

## Available Nodes

### csv_read

Read CSV files and convert them to structured data.

**Parameters:**
- `file_path` (str): Path to CSV file
- `delimiter` (str): Field delimiter (default: ",")
- `encoding` (str): File encoding (default: "utf-8")
- `has_header` (bool): Whether first row contains headers (default: True)
- `output_key` (str): Context key to store data (default: "csv_data")
- `name` (str, optional): Node name

**Returns:**
- `csv_success`: Boolean indicating if read operation succeeded
- `csv_rows`: Number of rows read
- `csv_file_path`: Path of the file that was read
- `csv_has_header`: Whether headers were processed
- `[output_key]`: List of dictionaries (if headers) or list of lists (if no headers)
- `csv_error`: Error message if operation failed

**Example:**
```python
from microflow import csv_read

# Read CSV with headers
read_users = csv_read(
    file_path="./data/users.csv",
    output_key="user_data",
    name="read_user_csv"
)

# Read CSV with custom delimiter
read_data = csv_read(
    file_path="./data/export.tsv",
    delimiter="\t",
    encoding="utf-8",
    output_key="tsv_data",
    name="read_tsv_file"
)

# Read CSV without headers
read_raw = csv_read(
    file_path="./data/raw_data.csv",
    has_header=False,
    output_key="raw_rows",
    name="read_raw_csv"
)
```

### csv_write

Write structured data to CSV files.

**Parameters:**
- `data_key` (str): Context key containing data to write (default: "data")
- `file_path` (str): Output CSV file path (default: "output.csv")
- `delimiter` (str): Field delimiter (default: ",")
- `encoding` (str): File encoding (default: "utf-8")
- `write_header` (bool): Whether to write header row (default: True)
- `name` (str, optional): Node name

**Returns:**
- `csv_success`: Boolean indicating if write operation succeeded
- `csv_file_path`: Path where file was written
- `csv_rows_written`: Number of rows written
- `csv_write_header`: Whether headers were written
- `csv_error`: Error message if operation failed

**Example:**
```python
from microflow import csv_write, task

@task(name="prepare_export_data")
def prepare_export_data(ctx):
    return {
        "export_data": [
            {"id": 1, "name": "Alice", "department": "Engineering"},
            {"id": 2, "name": "Bob", "department": "Sales"},
            {"id": 3, "name": "Carol", "department": "Marketing"}
        ]
    }

# Write to CSV
export_csv = csv_write(
    data_key="export_data",
    file_path="./output/employees.csv",
    name="export_employees"
)

prepare_export_data >> export_csv
```

### excel_read

Read Excel files and convert them to structured data.

**Parameters:**
- `file_path` (str): Path to Excel file
- `sheet_name` (Union[str, int]): Sheet name or index (default: 0)
- `has_header` (bool): Whether first row contains headers (default: True)
- `output_key` (str): Context key to store data (default: "excel_data")
- `name` (str, optional): Node name

**Dependencies:** Requires pandas and openpyxl to be installed

**Returns:**
- `excel_success`: Boolean indicating if read operation succeeded
- `excel_rows`: Number of rows read
- `excel_columns`: Number of columns read
- `excel_file_path`: Path of the file that was read
- `excel_sheet_name`: Name/index of sheet that was read
- `excel_has_header`: Whether headers were processed
- `[output_key]`: List of dictionaries (if headers) or list of lists (if no headers)
- `excel_error`: Error message if operation failed

**Example:**
```python
from microflow import excel_read

# Read first sheet with headers
read_sales = excel_read(
    file_path="./data/sales_report.xlsx",
    output_key="sales_data",
    name="read_sales_excel"
)

# Read specific sheet
read_inventory = excel_read(
    file_path="./data/quarterly_report.xlsx",
    sheet_name="Inventory",
    output_key="inventory_data",
    name="read_inventory_sheet"
)

# Read by sheet index
read_summary = excel_read(
    file_path="./data/report.xlsx",
    sheet_name=2,  # Third sheet (0-indexed)
    output_key="summary_data",
    name="read_summary_sheet"
)
```

### excel_write

Write structured data to Excel files.

**Parameters:**
- `data_key` (str): Context key containing data to write (default: "data")
- `file_path` (str): Output Excel file path (default: "output.xlsx")
- `sheet_name` (str): Sheet name (default: "Sheet1")
- `write_header` (bool): Whether to write header row (default: True)
- `name` (str, optional): Node name

**Dependencies:** Requires pandas and openpyxl to be installed

**Returns:**
- `excel_success`: Boolean indicating if write operation succeeded
- `excel_file_path`: Path where file was written
- `excel_sheet_name`: Name of sheet that was written
- `excel_rows_written`: Number of rows written
- `excel_columns_written`: Number of columns written
- `excel_write_header`: Whether headers were written
- `excel_error`: Error message if operation failed

**Example:**
```python
from microflow import excel_write

# Write to Excel with custom sheet name
export_excel = excel_write(
    data_key="report_data",
    file_path="./output/monthly_report.xlsx",
    sheet_name="Monthly Data",
    name="export_monthly_excel"
)

# Multiple sheets (using multiple write operations)
export_summary = excel_write(
    data_key="summary_data",
    file_path="./output/full_report.xlsx",
    sheet_name="Summary",
    name="export_summary_sheet"
)

export_details = excel_write(
    data_key="detail_data",
    file_path="./output/full_report.xlsx",
    sheet_name="Details",
    name="export_details_sheet"
)
```

## Format Conversion Nodes

### csv_to_json

Convert CSV files to JSON format.

**Parameters:**
- `file_path` (str): Input CSV file path
- `output_file` (str, optional): Output JSON file path
- `output_key` (str): Context key to store JSON data (default: "json_data")
- `delimiter` (str): CSV delimiter (default: ",")
- `name` (str, optional): Node name

**Returns:**
- `conversion_success`: Boolean indicating if conversion succeeded
- `rows_converted`: Number of rows converted
- `input_file`: Path of input CSV file
- `output_file`: Path of output JSON file (if specified)
- `[output_key]`: Converted JSON data
- `conversion_error`: Error message if conversion failed

**Example:**
```python
from microflow import csv_to_json

# Convert CSV to JSON in memory
convert_users = csv_to_json(
    file_path="./data/users.csv",
    output_key="users_json",
    name="convert_users_to_json"
)

# Convert and save to file
convert_and_save = csv_to_json(
    file_path="./data/products.csv",
    output_file="./output/products.json",
    output_key="products_json",
    name="convert_products_to_json"
)
```

### json_to_csv

Convert JSON data to CSV format.

**Parameters:**
- `data_key` (str): Context key containing JSON data (default: "data")
- `output_file` (str): Output CSV file path (default: "output.csv")
- `flatten_nested` (bool): Whether to flatten nested objects (default: False)
- `delimiter` (str): CSV delimiter (default: ",")
- `name` (str, optional): Node name

**Returns:**
- `conversion_success`: Boolean indicating if conversion succeeded
- `rows_converted`: Number of rows converted
- `output_file`: Path of output CSV file
- `flattened`: Whether nested objects were flattened
- `conversion_error`: Error message if conversion failed

**Example:**
```python
from microflow import json_to_csv, task

@task(name="prepare_json_data")
def prepare_json_data(ctx):
    return {
        "api_data": [
            {"id": 1, "name": "Alice", "details": {"age": 30, "city": "NYC"}},
            {"id": 2, "name": "Bob", "details": {"age": 25, "city": "LA"}}
        ]
    }

# Convert with flattening
convert_flat = json_to_csv(
    data_key="api_data",
    output_file="./output/users_flat.csv",
    flatten_nested=True,
    name="convert_json_flat"
)

prepare_json_data >> convert_flat
```

### excel_to_json

Convert Excel files to JSON format.

**Parameters:**
- `file_path` (str): Input Excel file path
- `sheet_name` (Union[str, int]): Sheet name or index (default: 0)
- `output_file` (str, optional): Output JSON file path
- `output_key` (str): Context key to store JSON data (default: "json_data")
- `name` (str, optional): Node name

**Dependencies:** Requires pandas and openpyxl to be installed

**Returns:**
- `conversion_success`: Boolean indicating if conversion succeeded
- `rows_converted`: Number of rows converted
- `input_file`: Path of input Excel file
- `sheet_name`: Name/index of sheet that was converted
- `output_file`: Path of output JSON file (if specified)
- `[output_key]`: Converted JSON data
- `conversion_error`: Error message if conversion failed

**Example:**
```python
from microflow import excel_to_json

# Convert Excel sheet to JSON
convert_report = excel_to_json(
    file_path="./data/quarterly_report.xlsx",
    sheet_name="Summary",
    output_file="./output/quarterly_summary.json",
    output_key="quarterly_data",
    name="convert_quarterly_report"
)
```

## Convenience Functions

### read_csv_file, write_csv_file

Simplified CSV operations.

```python
from microflow import read_csv_file, write_csv_file

# Simple CSV read
simple_read = read_csv_file("./data/simple.csv")

# Simple CSV write
simple_write = write_csv_file("output_data", "./output/simple.csv")
```

### read_excel_file, write_excel_file

Simplified Excel operations.

```python
from microflow import read_excel_file, write_excel_file

# Simple Excel read
simple_excel_read = read_excel_file("./data/report.xlsx")

# Simple Excel write
simple_excel_write = write_excel_file("report_data", "./output/report.xlsx")
```

## Advanced Usage

### Complete Data Processing Pipeline

Build a comprehensive data processing workflow:

```python
from microflow import csv_read, data_filter, data_transform, excel_write, task

# Read source data
read_raw_data = csv_read(
    file_path="./input/raw_sales.csv",
    output_key="raw_sales",
    name="read_raw_sales"
)

# Filter valid records
filter_valid = data_filter(
    filter_expression="item.get('amount', 0) > 0 and item.get('date')",
    data_key="raw_sales",
    output_key="valid_sales",
    name="filter_valid_sales"
)

# Transform and calculate
calculate_metrics = data_transform(
    transform_expression="{**item, 'tax': item['amount'] * 0.08, 'total': item['amount'] * 1.08}",
    data_key="valid_sales",
    output_key="processed_sales",
    name="calculate_tax_total"
)

# Export to Excel
export_processed = excel_write(
    data_key="processed_sales",
    file_path="./output/processed_sales.xlsx",
    sheet_name="Sales Analysis",
    name="export_processed_sales"
)

# Chain the pipeline
read_raw_data >> filter_valid >> calculate_metrics >> export_processed
```

### Multi-Format Export

Export the same data to multiple formats:

```python
from microflow import task, csv_write, excel_write, json_to_csv

@task(name="prepare_multi_export")
def prepare_multi_export(ctx):
    return {
        "report_data": [
            {"month": "January", "revenue": 100000, "expenses": 75000},
            {"month": "February", "revenue": 120000, "expenses": 80000},
            {"month": "March", "revenue": 110000, "expenses": 78000}
        ]
    }

# Export to CSV
export_csv = csv_write(
    data_key="report_data",
    file_path="./exports/monthly_report.csv",
    name="export_csv_report"
)

# Export to Excel
export_excel = excel_write(
    data_key="report_data",
    file_path="./exports/monthly_report.xlsx",
    sheet_name="Monthly Summary",
    name="export_excel_report"
)

# Export to JSON-CSV
export_json_csv = json_to_csv(
    data_key="report_data",
    output_file="./exports/monthly_report_json.csv",
    name="export_json_csv_report"
)

# Execute all exports in parallel
prepare_multi_export >> export_csv
prepare_multi_export >> export_excel
prepare_multi_export >> export_json_csv
```

### Dynamic File Processing

Process files based on directory contents:

```python
from microflow import list_directory, task, csv_read, excel_write

list_csv_files = list_directory(
    directory_path="./input",
    pattern="*.csv",
    output_key="csv_files",
    name="list_input_csvs"
)

@task(name="process_multiple_csvs")
def process_multiple_csvs(ctx):
    csv_files = ctx.get("csv_files", [])
    all_data = []

    for file_info in csv_files:
        file_path = file_info.get("path")
        # Read each CSV file
        # (In practice, you'd use the csv_read node in a loop)
        print(f"Would process: {file_path}")

    return {"combined_data": all_data}

consolidate_excel = excel_write(
    data_key="combined_data",
    file_path="./output/consolidated_report.xlsx",
    sheet_name="Consolidated Data",
    name="consolidate_to_excel"
)

list_csv_files >> process_multiple_csvs >> consolidate_excel
```

### Data Validation Pipeline

Validate data integrity during format conversion:

```python
from microflow import csv_read, task, excel_write

read_source = csv_read(
    file_path="./input/customer_data.csv",
    output_key="customer_data",
    name="read_customer_csv"
)

@task(name="validate_customer_data")
def validate_customer_data(ctx):
    data = ctx.get("customer_data", [])
    valid_records = []
    invalid_records = []

    required_fields = ["id", "name", "email"]

    for record in data:
        # Check required fields
        if all(field in record and record[field] for field in required_fields):
            # Validate email format
            if "@" in record["email"] and "." in record["email"]:
                valid_records.append(record)
            else:
                invalid_records.append({**record, "error": "Invalid email"})
        else:
            missing_fields = [f for f in required_fields if f not in record or not record[f]]
            invalid_records.append({**record, "error": f"Missing: {', '.join(missing_fields)}"})

    return {
        "valid_customers": valid_records,
        "invalid_customers": invalid_records,
        "validation_summary": {
            "total": len(data),
            "valid": len(valid_records),
            "invalid": len(invalid_records)
        }
    }

export_valid = excel_write(
    data_key="valid_customers",
    file_path="./output/valid_customers.xlsx",
    sheet_name="Valid Records",
    name="export_valid_customers"
)

export_invalid = excel_write(
    data_key="invalid_customers",
    file_path="./output/invalid_customers.xlsx",
    sheet_name="Invalid Records",
    name="export_invalid_customers"
)

read_source >> validate_customer_data >> export_valid
validate_customer_data >> export_invalid
```

## Error Handling

Data format nodes provide comprehensive error information:

```python
from microflow import csv_read, task

read_data = csv_read(
    file_path="./data/might_not_exist.csv",
    output_key="csv_data",
    name="read_risky_csv"
)

@task(name="handle_csv_result")
def handle_csv_result(ctx):
    if ctx.get("csv_success"):
        data = ctx.get("csv_data", [])
        return {
            "status": "success",
            "records_read": len(data),
            "message": f"Successfully read {len(data)} records"
        }
    else:
        error = ctx.get("csv_error", "Unknown error")
        return {
            "status": "error",
            "message": f"Failed to read CSV: {error}",
            "fallback_action": "use_default_data"
        }

read_data >> handle_csv_result
```

## Dependency Management

Handle optional dependencies gracefully:

```python
from microflow import task, csv_read, excel_write

@task(name="check_excel_support")
def check_excel_support(ctx):
    try:
        import pandas
        import openpyxl
        return {"excel_available": True}
    except ImportError:
        return {"excel_available": False}

read_csv_data = csv_read(
    file_path="./data/source.csv",
    output_key="source_data",
    name="read_source_data"
)

# Conditional Excel export
excel_export = excel_write(
    data_key="source_data",
    file_path="./output/data.xlsx",
    name="conditional_excel_export"
)

@task(name="fallback_csv_export")
def fallback_csv_export(ctx):
    # Fallback to CSV if Excel not available
    return {"fallback_completed": True}

# Use conditional logic based on dependency availability
check_excel_support >> read_csv_data
# Then use if_node to choose between Excel export or CSV fallback
```

## Best Practices

1. **Check dependencies**: Verify pandas/openpyxl are installed for Excel operations
2. **Handle large files**: Consider memory usage when processing large datasets
3. **Validate data**: Always validate data structure before processing
4. **Use appropriate encoding**: Specify correct encoding for international data
5. **Error handling**: Check success flags before using conversion results
6. **File paths**: Use absolute paths or ensure working directory is correct
7. **Data types**: Be aware of how different formats handle data types
8. **Performance**: For large datasets, consider chunked processing
9. **Backup originals**: Keep original files when doing destructive operations
10. **Document formats**: Clearly document expected data formats and schemas