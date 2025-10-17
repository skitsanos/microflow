# Data Transformation Nodes

Data transformation nodes provide powerful capabilities for processing, filtering, and manipulating data within your workflows. They support JSON parsing, data filtering, field selection, and custom transformations.

## Available Nodes

### data_transform

Apply custom transformations to lists of data using Python expressions.

**Parameters:**
- `transform_expression` (str): Python expression for transformation (item available as 'item')
- `data_key` (str): Context key containing list to transform (default: "data")
- `output_key` (str): Context key to store transformed data (default: "transformed_data")
- `name` (str, optional): Node name

**Returns:**
- `transform_success`: Boolean indicating if transformation succeeded
- `item_count`: Number of items processed
- `transform_expression`: The expression that was applied
- `[output_key]`: Transformed data list
- `transform_error`: Error message if transformation failed

**Example:**
```python
from microflow import data_transform, task

@task(name="setup_data")
def setup_data(ctx):
    return {
        "users": [
            {"name": "Alice", "age": 30, "salary": 50000},
            {"name": "Bob", "age": 25, "salary": 45000},
            {"name": "Carol", "age": 35, "salary": 60000}
        ]
    }

# Transform user data
calculate_annual_bonus = data_transform(
    transform_expression="{'name': item['name'], 'bonus': item['salary'] * 0.1}",
    data_key="users",
    output_key="user_bonuses"
)

setup_data >> calculate_annual_bonus
```

### data_filter

Filter lists of data based on conditions.

**Parameters:**
- `filter_expression` (str): Python expression for filtering (item available as 'item')
- `data_key` (str): Context key containing list to filter (default: "data")
- `output_key` (str): Context key to store filtered data (default: "filtered_data")
- `name` (str, optional): Node name

**Returns:**
- `filter_success`: Boolean indicating if filtering succeeded
- `original_count`: Number of items before filtering
- `filtered_count`: Number of items after filtering
- `filter_expression`: The expression that was applied
- `[output_key]`: Filtered data list
- `filter_error`: Error message if filtering failed

**Example:**
```python
from microflow import data_filter

# Filter high-value customers
filter_premium_users = data_filter(
    filter_expression="item.get('salary', 0) > 50000",
    data_key="users",
    output_key="premium_users"
)

# Filter by multiple conditions
filter_young_employees = data_filter(
    filter_expression="item.get('age', 0) < 30 and item.get('department') == 'Engineering'",
    data_key="employees",
    output_key="young_engineers"
)
```

### select_fields

Select specific fields from dictionaries in a list.

**Parameters:**
- `data_key` (str): Context key containing list of dictionaries (default: "data")
- `fields` (List[str]): List of field names to select
- `output_key` (str): Context key to store selected data (default: "selected_data")

**Returns:**
- `transform_success`: Boolean indicating if selection succeeded
- `item_count`: Number of items processed
- `[output_key]`: Data with only selected fields

**Example:**
```python
from microflow import select_fields

# Select only name and email fields
select_contact_info = select_fields(
    data_key="users",
    fields=["name", "email"],
    output_key="contact_list"
)

# Select subset for reporting
select_summary_fields = select_fields(
    data_key="employees",
    fields=["id", "name", "department", "salary"],
    output_key="employee_summary"
)
```

### rename_fields

Rename fields in dictionaries within a list.

**Parameters:**
- `data_key` (str): Context key containing list of dictionaries (default: "data")
- `field_mapping` (Dict[str, str]): Mapping of old field names to new names
- `output_key` (str): Context key to store renamed data (default: "renamed_data")

**Returns:**
- `transform_success`: Boolean indicating if renaming succeeded
- `item_count`: Number of items processed
- `[output_key]`: Data with renamed fields

**Example:**
```python
from microflow import rename_fields

# Rename fields for API compatibility
standardize_fields = rename_fields(
    data_key="raw_data",
    field_mapping={
        "user_id": "id",
        "user_name": "name",
        "user_email": "email",
        "created_at": "created_date"
    },
    output_key="standardized_data"
)

# Rename for database schema
prepare_for_db = rename_fields(
    data_key="api_response",
    field_mapping={
        "firstName": "first_name",
        "lastName": "last_name",
        "phoneNumber": "phone"
    },
    output_key="db_ready_data"
)
```

### json_parse

Parse JSON strings into Python objects.

**Parameters:**
- `json_key` (str): Context key containing JSON string (default: "json_data")
- `output_key` (str): Context key to store parsed data (default: "parsed_data")
- `name` (str, optional): Node name

**Returns:**
- `parse_success`: Boolean indicating if parsing succeeded
- `[output_key]`: Parsed Python object
- `parse_error`: Error message if parsing failed

**Example:**
```python
from microflow import json_parse, task

@task(name="fetch_json_string")
def fetch_json_string(ctx):
    return {
        "api_response": '{"users": [{"name": "Alice", "id": 1}], "total": 1}'
    }

parse_response = json_parse(
    json_key="api_response",
    output_key="parsed_response"
)

fetch_json_string >> parse_response
```

### json_stringify

Convert Python objects to JSON strings.

**Parameters:**
- `data_key` (str): Context key containing data to stringify (default: "data")
- `output_key` (str): Context key to store JSON string (default: "json_string")
- `indent` (int, optional): JSON indentation for pretty printing
- `name` (str, optional): Node name

**Returns:**
- `stringify_success`: Boolean indicating if conversion succeeded
- `[output_key]`: JSON string representation
- `stringify_error`: Error message if conversion failed

**Example:**
```python
from microflow import json_stringify

# Convert data to JSON for API
prepare_api_payload = json_stringify(
    data_key="user_data",
    output_key="api_payload",
    indent=2
)

# Convert for logging
log_data = json_stringify(
    data_key="debug_info",
    output_key="log_json",
    name="prepare_log_data"
)
```

## Advanced Usage

### Complex Data Transformations

Chain multiple transformations for complex data processing:

```python
from microflow import data_filter, data_transform, select_fields, task

@task(name="setup_employee_data")
def setup_employee_data(ctx):
    return {
        "employees": [
            {"id": 1, "name": "Alice", "dept": "Engineering", "salary": 75000, "years": 3},
            {"id": 2, "name": "Bob", "dept": "Sales", "salary": 55000, "years": 2},
            {"id": 3, "name": "Carol", "dept": "Engineering", "salary": 85000, "years": 5},
            {"id": 4, "name": "David", "dept": "Marketing", "salary": 48000, "years": 1}
        ]
    }

# Filter experienced engineers
filter_senior_engineers = data_filter(
    filter_expression="item.get('dept') == 'Engineering' and item.get('years', 0) >= 3",
    data_key="employees",
    output_key="senior_engineers"
)

# Calculate bonuses
calculate_bonuses = data_transform(
    transform_expression="{**item, 'bonus': item['salary'] * 0.15}",
    data_key="senior_engineers",
    output_key="engineers_with_bonuses"
)

# Select final fields
select_bonus_report = select_fields(
    data_key="engineers_with_bonuses",
    fields=["name", "salary", "bonus"],
    output_key="bonus_report"
)

# Chain transformations
setup_employee_data >> filter_senior_engineers >> calculate_bonuses >> select_bonus_report
```

### Data Aggregation

Aggregate data using transformations:

```python
from microflow import data_transform, task

@task(name="setup_sales_data")
def setup_sales_data(ctx):
    return {
        "sales": [
            {"region": "North", "amount": 10000, "month": "Jan"},
            {"region": "South", "amount": 15000, "month": "Jan"},
            {"region": "North", "amount": 12000, "month": "Feb"},
            {"region": "South", "amount": 18000, "month": "Feb"}
        ]
    }

@task(name="aggregate_by_region")
def aggregate_by_region(ctx):
    sales = ctx.get("sales", [])
    regions = {}

    for sale in sales:
        region = sale["region"]
        if region not in regions:
            regions[region] = {"region": region, "total": 0, "count": 0}
        regions[region]["total"] += sale["amount"]
        regions[region]["count"] += 1

    return {"regional_totals": list(regions.values())}

setup_sales_data >> aggregate_by_region
```

### Dynamic Field Operations

Use context data to dynamically select or rename fields:

```python
from microflow import task, data_transform

@task(name="setup_dynamic_config")
def setup_dynamic_config(ctx):
    return {
        "data": [{"a": 1, "b": 2, "c": 3}, {"a": 4, "b": 5, "c": 6}],
        "required_fields": ["a", "c"],
        "field_mapping": {"a": "first", "c": "third"}
    }

@task(name="dynamic_field_selection")
def dynamic_field_selection(ctx):
    data = ctx.get("data", [])
    required_fields = ctx.get("required_fields", [])
    field_mapping = ctx.get("field_mapping", {})

    result = []
    for item in data:
        # Select and rename fields dynamically
        new_item = {}
        for old_field in required_fields:
            if old_field in item:
                new_field = field_mapping.get(old_field, old_field)
                new_item[new_field] = item[old_field]
        result.append(new_item)

    return {"processed_data": result}

setup_dynamic_config >> dynamic_field_selection
```

## Data Validation

### Schema Validation
```python
from microflow import data_filter, task

validate_required_fields = data_filter(
    filter_expression="all(field in item for field in ['id', 'name', 'email'])",
    data_key="input_data",
    output_key="valid_records"
)

@task(name="count_validation_results")
def count_validation_results(ctx):
    original = ctx.get("input_data", [])
    valid = ctx.get("valid_records", [])
    invalid_count = len(original) - len(valid)

    return {
        "validation_summary": {
            "total_records": len(original),
            "valid_records": len(valid),
            "invalid_records": invalid_count
        }
    }

validate_required_fields >> count_validation_results
```

### Data Type Validation
```python
from microflow import data_filter

validate_numeric_fields = data_filter(
    filter_expression="isinstance(item.get('age'), int) and isinstance(item.get('salary'), (int, float))",
    data_key="user_data",
    output_key="valid_users"
)

validate_email_format = data_filter(
    filter_expression="'@' in item.get('email', '') and '.' in item.get('email', '')",
    data_key="valid_users",
    output_key="users_with_valid_email"
)
```

## Error Handling

Data transformation nodes provide detailed error information:

```python
from microflow import data_transform, task

risky_transform = data_transform(
    transform_expression="{'result': 10 / item.get('value', 0)}",
    data_key="input_data",
    output_key="calculated_data"
)

@task(name="handle_transform_result")
def handle_transform_result(ctx):
    if ctx.get("transform_success"):
        data = ctx.get("calculated_data", [])
        return {"status": "success", "processed_count": len(data)}
    else:
        error = ctx.get("transform_error")
        return {"status": "error", "message": error}

risky_transform >> handle_transform_result
```

## Performance Considerations

### Large Dataset Processing
```python
from microflow import task

@task(name="batch_process_large_dataset")
def batch_process_large_dataset(ctx):
    large_dataset = ctx.get("large_data", [])
    batch_size = 1000
    processed_batches = []

    for i in range(0, len(large_dataset), batch_size):
        batch = large_dataset[i:i + batch_size]
        # Process batch
        processed_batch = [{"processed": True, **item} for item in batch]
        processed_batches.extend(processed_batch)

    return {"processed_data": processed_batches}
```

### Memory-Efficient Processing
```python
from microflow import task

@task(name="stream_process_data")
def stream_process_data(ctx):
    input_data = ctx.get("input_data", [])

    # Generator for memory efficiency
    def process_items():
        for item in input_data:
            yield {"transformed": True, **item}

    # Convert generator to list only when needed
    result = list(process_items())
    return {"output_data": result}
```

## Best Practices

1. **Keep expressions simple**: Use clear, readable transformation expressions
2. **Handle missing data**: Use `.get()` with defaults for dictionary access
3. **Validate input data**: Check data structure before transformation
4. **Use appropriate data types**: Ensure expressions return expected types
5. **Test with sample data**: Verify transformations with representative data
6. **Handle large datasets**: Consider memory usage for large data processing
7. **Chain transformations**: Break complex operations into smaller steps
8. **Document expressions**: Use meaningful node names and comments
9. **Error handling**: Always check success flags before using results
10. **Performance monitoring**: Monitor execution time for large transformations