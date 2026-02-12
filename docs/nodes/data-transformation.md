# Data Transformation Nodes

## API

```python
json_parse(json_key='json_string', output_key='parsed_data', name=None)
json_stringify(data_key='data', output_key='json_string', indent=None, ensure_ascii=False, name=None)
json_query(query_path, data_key='data', output_key='query_result', default_value=None, name=None)
csv_parse(csv_key='csv_string', output_key='csv_data', delimiter=',', has_header=True, name=None)
csv_generate(data_key='data', output_key='csv_string', delimiter=',', include_header=True, name=None)
xml_parse(xml_key='xml_string', output_key='xml_data', name=None)
data_filter(filter_condition, data_key='data', output_key='filtered_data', name=None)
data_transform(transform_expression, data_key='data', output_key='transformed_data', name=None)
data_aggregate(data_key='data', group_by=None, aggregations=None, output_key='aggregated_data', name=None)
data_sort(sort_by, data_key='data', reverse=False, output_key='sorted_data', name=None)
select_fields(data_key='data', fields=None, output_key='selected_data')
rename_fields(data_key='data', field_mapping=None, output_key='renamed_data')
```

## Notes

- `data_filter` and `data_transform` evaluate Python expressions with a limited eval context.
- `select_fields` and `rename_fields` are convenience wrappers built on `data_transform`.
- Most nodes expose success/error keys such as `*_success` and `*_error` plus the configured `output_key`.

## Example

```python
from microflow import data_filter, data_transform

active = data_filter(
    "item.get('active') is True",
    data_key="users",
    output_key="active_users",
)

emails = data_transform(
    "item.get('email')",
    data_key="active_users",
    output_key="active_emails",
)
```
