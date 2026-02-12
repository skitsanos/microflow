"""Data format conversion nodes for CSV, Excel, and JSON operations"""

import csv
import json
import os
from pathlib import Path
from typing import Optional, Union

from ..core.task_spec import task

# Note: pandas and openpyxl are optional dependencies for Excel support
try:
    import pandas as pd  # type: ignore[import-untyped]

    PANDAS_AVAILABLE = True
except ImportError:
    PANDAS_AVAILABLE = False

try:
    import openpyxl  # type: ignore[import-untyped]  # noqa: F401

    OPENPYXL_AVAILABLE = True
except ImportError:
    OPENPYXL_AVAILABLE = False


def csv_read(
    file_path: str,
    delimiter: str = ",",
    encoding: str = "utf-8",
    has_header: bool = True,
    output_key: str = "csv_data",
    name: Optional[str] = None,
):
    """
    Read CSV file and convert to list of dictionaries.

    Args:
        file_path: Path to CSV file
        delimiter: Field delimiter (default: comma)
        encoding: File encoding
        has_header: Whether first row contains headers
        output_key: Context key to store data
        name: Node name
    """
    node_name = name or f"csv_read_{Path(file_path).stem}"

    @task(name=node_name, description=f"Read CSV: {file_path}")
    def _csv_read(ctx):
        try:
            if not os.path.exists(file_path):
                return {
                    "csv_success": False,
                    "csv_error": f"File not found: {file_path}",
                    "file_path": file_path,
                }

            data = []
            with open(file_path, "r", encoding=encoding, newline="") as csvfile:
                if has_header:
                    reader = csv.DictReader(csvfile, delimiter=delimiter)
                    data = list(reader)
                else:
                    reader = csv.reader(csvfile, delimiter=delimiter)
                    data = [list(row) for row in reader]

            return {
                output_key: data,
                "csv_success": True,
                "csv_rows": len(data),
                "csv_file_path": file_path,
                "csv_has_header": has_header,
            }

        except Exception as e:
            return {
                "csv_success": False,
                "csv_error": f"CSV read error: {e}",
                "file_path": file_path,
            }

    return _csv_read


def csv_write(
    data_key: str = "data",
    file_path: str = "output.csv",
    delimiter: str = ",",
    encoding: str = "utf-8",
    write_header: bool = True,
    name: Optional[str] = None,
):
    """
    Write data to CSV file.

    Args:
        data_key: Context key containing data to write
        file_path: Output CSV file path
        delimiter: Field delimiter
        encoding: File encoding
        write_header: Whether to write header row
        name: Node name
    """
    node_name = name or f"csv_write_{Path(file_path).stem}"

    @task(name=node_name, description=f"Write CSV: {file_path}")
    def _csv_write(ctx):
        try:
            data = ctx.get(data_key)
            if data is None:
                return {
                    "csv_success": False,
                    "csv_error": f"No data found in context key: {data_key}",
                }

            if not isinstance(data, list) or not data:
                return {
                    "csv_success": False,
                    "csv_error": "Data must be a non-empty list",
                }

            # Ensure output directory exists
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)

            with open(file_path, "w", encoding=encoding, newline="") as csvfile:
                if isinstance(data[0], dict):
                    # Write dictionary data
                    fieldnames = data[0].keys()
                    writer = csv.DictWriter(
                        csvfile, fieldnames=fieldnames, delimiter=delimiter
                    )

                    if write_header:
                        writer.writeheader()
                    writer.writerows(data)
                else:
                    # Write list data
                    writer = csv.writer(csvfile, delimiter=delimiter)
                    writer.writerows(data)

            return {
                "csv_success": True,
                "csv_file_path": file_path,
                "csv_rows_written": len(data),
                "csv_write_header": write_header,
            }

        except Exception as e:
            return {
                "csv_success": False,
                "csv_error": f"CSV write error: {e}",
                "file_path": file_path,
            }

    return _csv_write


def excel_read(
    file_path: str,
    sheet_name: Union[str, int] = 0,
    has_header: bool = True,
    output_key: str = "excel_data",
    name: Optional[str] = None,
):
    """
    Read Excel file and convert to list of dictionaries.

    Args:
        file_path: Path to Excel file
        sheet_name: Sheet name or index (0-based)
        has_header: Whether first row contains headers
        output_key: Context key to store data
        name: Node name

    Note: Requires pandas and openpyxl to be installed
    """
    node_name = name or f"excel_read_{Path(file_path).stem}"

    @task(name=node_name, description=f"Read Excel: {file_path}")
    def _excel_read(ctx):
        try:
            if not PANDAS_AVAILABLE:
                return {
                    "excel_success": False,
                    "excel_error": "pandas is required for Excel operations. Install with: pip install pandas",
                }

            if not OPENPYXL_AVAILABLE:
                return {
                    "excel_success": False,
                    "excel_error": "openpyxl is required for Excel operations. Install with: pip install openpyxl",
                }

            if not os.path.exists(file_path):
                return {
                    "excel_success": False,
                    "excel_error": f"File not found: {file_path}",
                    "file_path": file_path,
                }

            # Read Excel file
            header = 0 if has_header else None
            df = pd.read_excel(file_path, sheet_name=sheet_name, header=header)

            # Convert to list of dictionaries
            if has_header:
                data = df.to_dict("records")
            else:
                data = df.values.tolist()

            return {
                output_key: data,
                "excel_success": True,
                "excel_rows": len(data),
                "excel_columns": len(df.columns),
                "excel_file_path": file_path,
                "excel_sheet_name": sheet_name,
                "excel_has_header": has_header,
            }

        except Exception as e:
            return {
                "excel_success": False,
                "excel_error": f"Excel read error: {e}",
                "file_path": file_path,
            }

    return _excel_read


def excel_write(
    data_key: str = "data",
    file_path: str = "output.xlsx",
    sheet_name: str = "Sheet1",
    write_header: bool = True,
    name: Optional[str] = None,
):
    """
    Write data to Excel file.

    Args:
        data_key: Context key containing data to write
        file_path: Output Excel file path
        sheet_name: Sheet name
        write_header: Whether to write header row
        name: Node name

    Note: Requires pandas and openpyxl to be installed
    """
    node_name = name or f"excel_write_{Path(file_path).stem}"

    @task(name=node_name, description=f"Write Excel: {file_path}")
    def _excel_write(ctx):
        try:
            if not PANDAS_AVAILABLE:
                return {
                    "excel_success": False,
                    "excel_error": "pandas is required for Excel operations. Install with: pip install pandas",
                }

            if not OPENPYXL_AVAILABLE:
                return {
                    "excel_success": False,
                    "excel_error": "openpyxl is required for Excel operations. Install with: pip install openpyxl",
                }

            data = ctx.get(data_key)
            if data is None:
                return {
                    "excel_success": False,
                    "excel_error": f"No data found in context key: {data_key}",
                }

            if not isinstance(data, list) or not data:
                return {
                    "excel_success": False,
                    "excel_error": "Data must be a non-empty list",
                }

            # Ensure output directory exists
            Path(file_path).parent.mkdir(parents=True, exist_ok=True)

            # Convert to DataFrame
            df = pd.DataFrame(data)

            # Write to Excel
            df.to_excel(
                file_path, sheet_name=sheet_name, index=False, header=write_header
            )

            return {
                "excel_success": True,
                "excel_file_path": file_path,
                "excel_sheet_name": sheet_name,
                "excel_rows_written": len(data),
                "excel_columns_written": len(df.columns),
                "excel_write_header": write_header,
            }

        except Exception as e:
            return {
                "excel_success": False,
                "excel_error": f"Excel write error: {e}",
                "file_path": file_path,
            }

    return _excel_write


def json_to_csv(
    data_key: str = "data",
    output_file: str = "output.csv",
    flatten_nested: bool = False,
    delimiter: str = ",",
    name: Optional[str] = None,
):
    """
    Convert JSON data to CSV format.

    Args:
        data_key: Context key containing JSON data
        output_file: Output CSV file path
        flatten_nested: Whether to flatten nested objects
        delimiter: CSV delimiter
        name: Node name
    """
    node_name = name or "json_to_csv"

    @task(name=node_name, description=f"Convert JSON to CSV: {output_file}")
    def _json_to_csv(ctx):
        try:
            data = ctx.get(data_key)
            if data is None:
                return {
                    "conversion_success": False,
                    "conversion_error": f"No data found in context key: {data_key}",
                }

            if not isinstance(data, list):
                return {
                    "conversion_success": False,
                    "conversion_error": "Data must be a list of objects for CSV conversion",
                }

            if not data:
                return {
                    "conversion_success": False,
                    "conversion_error": "Data list is empty",
                }

            # Flatten nested objects if requested
            if flatten_nested:
                flattened_data = []
                for item in data:
                    if isinstance(item, dict):
                        flat_item = {}
                        _flatten_dict(item, flat_item)
                        flattened_data.append(flat_item)
                    else:
                        flattened_data.append(item)
                data = flattened_data

            # Ensure output directory exists
            Path(output_file).parent.mkdir(parents=True, exist_ok=True)

            # Write CSV
            with open(output_file, "w", newline="", encoding="utf-8") as csvfile:
                if isinstance(data[0], dict):
                    fieldnames = data[0].keys()
                    writer = csv.DictWriter(
                        csvfile, fieldnames=fieldnames, delimiter=delimiter
                    )
                    writer.writeheader()
                    writer.writerows(data)
                else:
                    writer = csv.writer(csvfile, delimiter=delimiter)
                    writer.writerows(data)

            return {
                "conversion_success": True,
                "output_file": output_file,
                "rows_converted": len(data),
                "flattened": flatten_nested,
            }

        except Exception as e:
            return {
                "conversion_success": False,
                "conversion_error": f"JSON to CSV conversion error: {e}",
                "output_file": output_file,
            }

    return _json_to_csv


def csv_to_json(
    file_path: str,
    output_file: Optional[str] = None,
    output_key: str = "json_data",
    delimiter: str = ",",
    name: Optional[str] = None,
):
    """
    Convert CSV file to JSON format.

    Args:
        file_path: Input CSV file path
        output_file: Output JSON file path (optional)
        output_key: Context key to store JSON data
        delimiter: CSV delimiter
        name: Node name
    """
    node_name = name or f"csv_to_json_{Path(file_path).stem}"

    @task(name=node_name, description=f"Convert CSV to JSON: {file_path}")
    def _csv_to_json(ctx):
        try:
            if not os.path.exists(file_path):
                return {
                    "conversion_success": False,
                    "conversion_error": f"File not found: {file_path}",
                    "file_path": file_path,
                }

            # Read CSV
            data = []
            with open(file_path, "r", encoding="utf-8", newline="") as csvfile:
                reader = csv.DictReader(csvfile, delimiter=delimiter)
                data = list(reader)

            result = {
                output_key: data,
                "conversion_success": True,
                "rows_converted": len(data),
                "input_file": file_path,
            }

            # Write JSON file if requested
            if output_file:
                Path(output_file).parent.mkdir(parents=True, exist_ok=True)
                with open(output_file, "w", encoding="utf-8") as jsonfile:
                    json.dump(data, jsonfile, indent=2, ensure_ascii=False)
                result["output_file"] = output_file

            return result

        except Exception as e:
            return {
                "conversion_success": False,
                "conversion_error": f"CSV to JSON conversion error: {e}",
                "file_path": file_path,
            }

    return _csv_to_json


def excel_to_json(
    file_path: str,
    sheet_name: Union[str, int] = 0,
    output_file: Optional[str] = None,
    output_key: str = "json_data",
    name: Optional[str] = None,
):
    """
    Convert Excel file to JSON format.

    Args:
        file_path: Input Excel file path
        sheet_name: Sheet name or index
        output_file: Output JSON file path (optional)
        output_key: Context key to store JSON data
        name: Node name

    Note: Requires pandas and openpyxl to be installed
    """
    node_name = name or f"excel_to_json_{Path(file_path).stem}"

    @task(name=node_name, description=f"Convert Excel to JSON: {file_path}")
    def _excel_to_json(ctx):
        try:
            if not PANDAS_AVAILABLE:
                return {
                    "conversion_success": False,
                    "conversion_error": "pandas is required for Excel operations. Install with: pip install pandas",
                }

            if not OPENPYXL_AVAILABLE:
                return {
                    "conversion_success": False,
                    "conversion_error": "openpyxl is required for Excel operations. Install with: pip install openpyxl",
                }

            if not os.path.exists(file_path):
                return {
                    "conversion_success": False,
                    "conversion_error": f"File not found: {file_path}",
                    "file_path": file_path,
                }

            # Read Excel
            df = pd.read_excel(file_path, sheet_name=sheet_name)
            data = df.to_dict("records")

            result = {
                output_key: data,
                "conversion_success": True,
                "rows_converted": len(data),
                "input_file": file_path,
                "sheet_name": sheet_name,
            }

            # Write JSON file if requested
            if output_file:
                Path(output_file).parent.mkdir(parents=True, exist_ok=True)
                with open(output_file, "w", encoding="utf-8") as jsonfile:
                    json.dump(data, jsonfile, indent=2, ensure_ascii=False)
                result["output_file"] = output_file

            return result

        except Exception as e:
            return {
                "conversion_success": False,
                "conversion_error": f"Excel to JSON conversion error: {e}",
                "file_path": file_path,
            }

    return _excel_to_json


def _flatten_dict(
    nested_dict: dict, flat_dict: dict, parent_key: str = "", separator: str = "."
):
    """Helper function to flatten nested dictionaries"""
    for key, value in nested_dict.items():
        new_key = f"{parent_key}{separator}{key}" if parent_key else key
        if isinstance(value, dict):
            _flatten_dict(value, flat_dict, new_key, separator)
        else:
            flat_dict[new_key] = value


# Convenience functions for common operations
def read_csv_file(file_path: str, **kwargs):
    """Simple CSV file reader"""
    return csv_read(file_path, **kwargs)


def write_csv_file(data_key: str, file_path: str, **kwargs):
    """Simple CSV file writer"""
    return csv_write(data_key, file_path, **kwargs)


def read_excel_file(file_path: str, **kwargs):
    """Simple Excel file reader"""
    return excel_read(file_path, **kwargs)


def write_excel_file(data_key: str, file_path: str, **kwargs):
    """Simple Excel file writer"""
    return excel_write(data_key, file_path, **kwargs)
