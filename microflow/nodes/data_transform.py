"""Data transformation nodes for JSON, CSV, XML, and other formats"""

import csv
import io
import json
import xml.etree.ElementTree as ET
from typing import Any, Dict, List, Optional

from ..core.task_spec import task


def json_parse(
    json_key: str = "json_string",
    output_key: str = "parsed_data",
    name: Optional[str] = None,
):
    """
    Parse JSON string from context.

    Args:
        json_key: Context key containing JSON string
        output_key: Context key to store parsed data
        name: Node name
    """
    node_name = name or "json_parse"

    @task(name=node_name, description="Parse JSON string")
    def _json_parse(ctx):
        json_string = ctx.get(json_key)
        if json_string is None:
            return {
                "json_parsed": False,
                "json_error": f"No data found in context key: {json_key}",
            }

        try:
            parsed_data = json.loads(json_string)
            return {
                output_key: parsed_data,
                "json_parsed": True,
                "json_type": type(parsed_data).__name__,
            }

        except json.JSONDecodeError as e:
            return {"json_parsed": False, "json_error": f"JSON decode error: {e}"}

    return _json_parse


def json_stringify(
    data_key: str = "data",
    output_key: str = "json_string",
    indent: Optional[int] = None,
    ensure_ascii: bool = False,
    name: Optional[str] = None,
):
    """
    Convert data to JSON string.

    Args:
        data_key: Context key containing data to serialize
        output_key: Context key to store JSON string
        indent: JSON indentation (None for compact)
        ensure_ascii: Whether to escape non-ASCII characters
        name: Node name
    """
    node_name = name or "json_stringify"

    @task(name=node_name, description="Convert data to JSON")
    def _json_stringify(ctx):
        data = ctx.get(data_key)
        if data is None:
            return {
                "json_serialized": False,
                "json_error": f"No data found in context key: {data_key}",
            }

        try:
            json_string = json.dumps(data, indent=indent, ensure_ascii=ensure_ascii)
            return {
                output_key: json_string,
                "json_serialized": True,
                "json_length": len(json_string),
            }

        except (TypeError, ValueError) as e:
            return {
                "json_serialized": False,
                "json_error": f"JSON serialization error: {e}",
            }

    return _json_stringify


def json_query(
    query_path: str,
    data_key: str = "data",
    output_key: str = "query_result",
    default_value: Any = None,
    name: Optional[str] = None,
):
    """
    Query JSON data using dot notation path.

    Args:
        data_key: Context key containing JSON data
        query_path: Dot notation path (e.g., "user.profile.name")
        output_key: Context key to store result
        default_value: Value to return if path not found
        name: Node name
    """
    node_name = name or f"json_query_{query_path.replace('.', '_')}"

    @task(name=node_name, description=f"Query JSON path: {query_path}")
    def _json_query(ctx):
        data = ctx.get(data_key)
        if data is None:
            return {
                "query_success": False,
                "query_error": f"No data found in context key: {data_key}",
            }

        try:
            # Navigate through the path
            current = data
            path_parts = query_path.split(".")

            for part in path_parts:
                if isinstance(current, dict):
                    current = current.get(part)
                elif isinstance(current, list) and part.isdigit():
                    index = int(part)
                    current = current[index] if 0 <= index < len(current) else None
                else:
                    current = None
                    break

                if current is None:
                    break

            result = current if current is not None else default_value

            return {
                output_key: result,
                "query_success": True,
                "query_path": query_path,
                "query_found": current is not None,
            }

        except (KeyError, IndexError, TypeError) as e:
            return {
                output_key: default_value,
                "query_success": False,
                "query_error": f"Query error: {e}",
                "query_path": query_path,
            }

    return _json_query


def csv_parse(
    csv_key: str = "csv_string",
    output_key: str = "csv_data",
    delimiter: str = ",",
    has_header: bool = True,
    name: Optional[str] = None,
):
    """
    Parse CSV string into list of dictionaries.

    Args:
        csv_key: Context key containing CSV string
        output_key: Context key to store parsed data
        delimiter: CSV delimiter character
        has_header: Whether first row contains headers
        name: Node name
    """
    node_name = name or "csv_parse"

    @task(name=node_name, description="Parse CSV data")
    def _csv_parse(ctx):
        csv_string = ctx.get(csv_key)
        if csv_string is None:
            return {
                "csv_parsed": False,
                "csv_error": f"No data found in context key: {csv_key}",
            }

        try:
            csv_file = io.StringIO(csv_string)
            reader = csv.reader(csv_file, delimiter=delimiter)

            rows = list(reader)
            if not rows:
                return {
                    output_key: [],
                    "csv_parsed": True,
                    "csv_rows": 0,
                    "csv_columns": 0,
                }

            if has_header:
                headers = rows[0]
                data_rows = rows[1:]
                parsed_data = [dict(zip(headers, row)) for row in data_rows]
            else:
                parsed_data = [list(row) for row in rows]

            return {
                output_key: parsed_data,
                "csv_parsed": True,
                "csv_rows": len(parsed_data),
                "csv_columns": len(rows[0]) if rows else 0,
                "csv_headers": headers if has_header else None,
            }

        except Exception as e:
            return {"csv_parsed": False, "csv_error": f"CSV parse error: {e}"}

    return _csv_parse


def csv_generate(
    data_key: str = "data",
    output_key: str = "csv_string",
    delimiter: str = ",",
    include_header: bool = True,
    name: Optional[str] = None,
):
    """
    Generate CSV string from list of dictionaries.

    Args:
        data_key: Context key containing list of dictionaries
        output_key: Context key to store CSV string
        delimiter: CSV delimiter character
        include_header: Whether to include header row
        name: Node name
    """
    node_name = name or "csv_generate"

    @task(name=node_name, description="Generate CSV data")
    def _csv_generate(ctx):
        data = ctx.get(data_key)
        if data is None:
            return {
                "csv_generated": False,
                "csv_error": f"No data found in context key: {data_key}",
            }

        if not isinstance(data, list):
            return {
                "csv_generated": False,
                "csv_error": "Data must be a list of dictionaries",
            }

        if not data:
            return {output_key: "", "csv_generated": True, "csv_rows": 0}

        try:
            output = io.StringIO()

            if isinstance(data[0], dict):
                # List of dictionaries
                fieldnames = data[0].keys()
                writer = csv.DictWriter(
                    output, fieldnames=fieldnames, delimiter=delimiter
                )

                if include_header:
                    writer.writeheader()

                writer.writerows(data)
            else:
                # List of lists
                writer = csv.writer(output, delimiter=delimiter)
                writer.writerows(data)

            csv_string = output.getvalue()

            return {
                output_key: csv_string,
                "csv_generated": True,
                "csv_rows": len(data),
                "csv_length": len(csv_string),
            }

        except Exception as e:
            return {"csv_generated": False, "csv_error": f"CSV generation error: {e}"}

    return _csv_generate


def xml_parse(
    xml_key: str = "xml_string",
    output_key: str = "xml_data",
    name: Optional[str] = None,
):
    """
    Parse XML string into dictionary structure.

    Args:
        xml_key: Context key containing XML string
        output_key: Context key to store parsed data
        name: Node name
    """
    node_name = name or "xml_parse"

    def _xml_to_dict(element):
        """Convert XML element to dictionary"""
        result = {}

        # Add attributes
        if element.attrib:
            result["@attributes"] = element.attrib

        # Add text content
        if element.text and element.text.strip():
            if len(element) == 0:  # No child elements
                return element.text.strip()
            else:
                result["#text"] = element.text.strip()

        # Add child elements
        for child in element:
            child_data = _xml_to_dict(child)

            if child.tag in result:
                # Multiple elements with same tag
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_data)
            else:
                result[child.tag] = child_data

        return result if result else None

    @task(name=node_name, description="Parse XML data")
    def _xml_parse(ctx):
        xml_string = ctx.get(xml_key)
        if xml_string is None:
            return {
                "xml_parsed": False,
                "xml_error": f"No data found in context key: {xml_key}",
            }

        try:
            root = ET.fromstring(xml_string)
            parsed_data = {root.tag: _xml_to_dict(root)}

            return {
                output_key: parsed_data,
                "xml_parsed": True,
                "xml_root_tag": root.tag,
            }

        except ET.ParseError as e:
            return {"xml_parsed": False, "xml_error": f"XML parse error: {e}"}

    return _xml_parse


def data_filter(
    filter_condition: str,
    data_key: str = "data",
    output_key: str = "filtered_data",
    name: Optional[str] = None,
):
    """
    Filter list of items based on condition.

    Args:
        data_key: Context key containing list to filter
        filter_condition: Python expression for filtering (item available as 'item')
        output_key: Context key to store filtered data
        name: Node name
    """
    node_name = name or "data_filter"

    @task(name=node_name, description=f"Filter data: {filter_condition}")
    def _data_filter(ctx):
        data = ctx.get(data_key)
        if data is None:
            return {
                "filter_success": False,
                "filter_error": f"No data found in context key: {data_key}",
            }

        if not isinstance(data, list):
            return {"filter_success": False, "filter_error": "Data must be a list"}

        try:
            filtered_items = []
            for item in data:
                # Create safe evaluation context
                eval_context = {"item": item, "ctx": ctx, "__builtins__": {}}

                if eval(filter_condition, eval_context):
                    filtered_items.append(item)

            return {
                output_key: filtered_items,
                "filter_success": True,
                "original_count": len(data),
                "filtered_count": len(filtered_items),
                "filter_condition": filter_condition,
            }

        except Exception as e:
            return {
                "filter_success": False,
                "filter_error": f"Filter error: {e}",
                "filter_condition": filter_condition,
            }

    return _data_filter


def data_transform(
    transform_expression: str,
    data_key: str = "data",
    output_key: str = "transformed_data",
    name: Optional[str] = None,
):
    """
    Transform list of items using expression.

    Args:
        data_key: Context key containing list to transform
        transform_expression: Python expression for transformation (item available as 'item')
        output_key: Context key to store transformed data
        name: Node name
    """
    node_name = name or "data_transform"

    @task(name=node_name, description=f"Transform data: {transform_expression}")
    def _data_transform(ctx):
        data = ctx.get(data_key)
        if data is None:
            return {
                "transform_success": False,
                "transform_error": f"No data found in context key: {data_key}",
            }

        if not isinstance(data, list):
            return {
                "transform_success": False,
                "transform_error": "Data must be a list",
            }

        try:
            transformed_items = []
            for item in data:
                # Create safe evaluation context
                eval_context = {"item": item, "ctx": ctx, "__builtins__": {}}

                transformed_item = eval(transform_expression, eval_context)
                transformed_items.append(transformed_item)

            return {
                output_key: transformed_items,
                "transform_success": True,
                "item_count": len(transformed_items),
                "transform_expression": transform_expression,
            }

        except Exception as e:
            return {
                "transform_success": False,
                "transform_error": f"Transform error: {e}",
                "transform_expression": transform_expression,
            }

    return _data_transform


def data_aggregate(
    data_key: str = "data",
    group_by: Optional[str] = None,
    aggregations: Optional[Dict[str, str]] = None,
    output_key: str = "aggregated_data",
    name: Optional[str] = None,
):
    """
    Aggregate data with grouping and calculations.

    Args:
        data_key: Context key containing list of dictionaries
        group_by: Field to group by (None for no grouping)
        aggregations: Dict of {output_field: aggregation_expression}
        output_key: Context key to store aggregated data
        name: Node name

    Example aggregations:
        {"total_sales": "sum(item['sales'] for item in group)",
         "avg_price": "sum(item['price'] for item in group) / len(group)"}
    """
    node_name = name or "data_aggregate"

    @task(name=node_name, description="Aggregate data")
    def _data_aggregate(ctx):
        data = ctx.get(data_key)
        if data is None:
            return {
                "aggregate_success": False,
                "aggregate_error": f"No data found in context key: {data_key}",
            }

        if not isinstance(data, list):
            return {
                "aggregate_success": False,
                "aggregate_error": "Data must be a list of dictionaries",
            }

        if not aggregations:
            aggregations_to_use = {"count": "len(group)"}
        else:
            aggregations_to_use = aggregations

        try:
            if group_by:
                # Group data by field
                groups = {}
                for item in data:
                    if not isinstance(item, dict):
                        continue

                    group_key = item.get(group_by, "None")
                    if group_key not in groups:
                        groups[group_key] = []
                    groups[group_key].append(item)

                # Aggregate each group
                results = []
                for group_key, group_items in groups.items():
                    result = {group_by: group_key}

                    for output_field, expression in aggregations_to_use.items():
                        eval_context = {
                            "group": group_items,
                            "sum": sum,
                            "len": len,
                            "min": min,
                            "max": max,
                            "avg": lambda x: sum(x) / len(x) if x else 0,
                            "__builtins__": {},
                        }

                        try:
                            result[output_field] = eval(expression, eval_context)
                        except Exception as e:
                            result[output_field] = f"Error: {e}"

                    results.append(result)

            else:
                # Aggregate entire dataset
                result = {}
                for output_field, expression in aggregations_to_use.items():
                    eval_context = {
                        "group": data,
                        "sum": sum,
                        "len": len,
                        "min": min,
                        "max": max,
                        "avg": lambda x: sum(x) / len(x) if x else 0,
                        "__builtins__": {},
                    }

                    try:
                        result[output_field] = eval(expression, eval_context)
                    except Exception as e:
                        result[output_field] = f"Error: {e}"

                results = [result]

            return {
                output_key: results,
                "aggregate_success": True,
                "group_count": len(results),
                "original_count": len(data),
            }

        except Exception as e:
            return {
                "aggregate_success": False,
                "aggregate_error": f"Aggregation error: {e}",
            }

    return _data_aggregate


def data_sort(
    sort_by: str,
    data_key: str = "data",
    reverse: bool = False,
    output_key: str = "sorted_data",
    name: Optional[str] = None,
):
    """
    Sort list of items.

    Args:
        data_key: Context key containing list to sort
        sort_by: Field name to sort by or expression (item available as 'item')
        reverse: Whether to sort in descending order
        output_key: Context key to store sorted data
        name: Node name
    """
    node_name = name or f"data_sort_{sort_by}"

    @task(name=node_name, description=f"Sort data by: {sort_by}")
    def _data_sort(ctx):
        data = ctx.get(data_key)
        if data is None:
            return {
                "sort_success": False,
                "sort_error": f"No data found in context key: {data_key}",
            }

        if not isinstance(data, list):
            return {"sort_success": False, "sort_error": "Data must be a list"}

        try:

            def sort_key(item):
                if isinstance(item, dict) and sort_by in item:
                    return item[sort_by]
                else:
                    # Treat as expression
                    eval_context = {"item": item, "__builtins__": {}}
                    return eval(sort_by, eval_context)

            sorted_data = sorted(data, key=sort_key, reverse=reverse)

            return {
                output_key: sorted_data,
                "sort_success": True,
                "item_count": len(sorted_data),
                "sort_by": sort_by,
                "sort_reverse": reverse,
            }

        except Exception as e:
            return {
                "sort_success": False,
                "sort_error": f"Sort error: {e}",
                "sort_by": sort_by,
            }

    return _data_sort


# Convenience functions for common data operations
def select_fields(
    data_key: str = "data",
    fields: Optional[List[str]] = None,
    output_key: str = "selected_data",
):
    """Select specific fields from list of dictionaries"""
    if not fields:
        fields = []

    expression = f"{{k: item[k] for k in {fields} if k in item}}"
    return data_transform(
        expression,
        data_key=data_key,
        output_key=output_key,
        name=f"select_{len(fields)}_fields",
    )


def rename_fields(
    data_key: str = "data",
    field_mapping: Optional[Dict[str, str]] = None,
    output_key: str = "renamed_data",
):
    """Rename fields in list of dictionaries"""
    if not field_mapping:
        field_mapping = {}

    # Build expression that directly embeds the mapping
    expression = (
        "{mapping.get(k, k): v for k, v in item.items()} "
        "if isinstance(item, dict) else item"
    )

    # Create the transform task with correct parameter order
    transform_task = data_transform(
        expression, data_key=data_key, output_key=output_key, name="rename_fields"
    )

    # Override the function to inject mapping into evaluation context
    def enhanced_fn(ctx):
        data = ctx.get(data_key)
        if data is None:
            return {
                "transform_success": False,
                "transform_error": f"No data found in context key: {data_key}",
            }

        if not isinstance(data, list):
            return {
                "transform_success": False,
                "transform_error": "Data must be a list",
            }

        try:
            transformed_items = []
            for item in data:
                # Create safe evaluation context with mapping included
                eval_context = {
                    "item": item,
                    "ctx": ctx,
                    "mapping": field_mapping,
                    "__builtins__": {"isinstance": isinstance, "dict": dict},
                }

                transformed_item = eval(expression, eval_context)
                transformed_items.append(transformed_item)

            return {
                output_key: transformed_items,
                "transform_success": True,
                "item_count": len(transformed_items),
                "transform_expression": expression,
            }

        except Exception as e:
            return {
                "transform_success": False,
                "transform_error": f"Transform error: {e}",
                "transform_expression": expression,
            }

    transform_task.spec.fn = enhanced_fn
    return transform_task
