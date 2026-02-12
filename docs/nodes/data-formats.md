# Data Format Nodes

## API

```python
csv_read(file_path, delimiter=',', encoding='utf-8', has_header=True, output_key='csv_data', name=None)
csv_write(data_key='data', file_path='output.csv', delimiter=',', encoding='utf-8', write_header=True, name=None)
excel_read(file_path, sheet_name=0, has_header=True, output_key='excel_data', name=None)
excel_write(data_key='data', file_path='output.xlsx', sheet_name='Sheet1', write_header=True, name=None)
json_to_csv(data_key='data', output_file='output.csv', flatten_nested=False, delimiter=',', name=None)
csv_to_json(file_path, output_file=None, output_key='json_data', delimiter=',', name=None)
excel_to_json(file_path, sheet_name=0, output_file=None, output_key='json_data', name=None)
read_csv_file(file_path, **kwargs)
write_csv_file(data_key, file_path, **kwargs)
read_excel_file(file_path, **kwargs)
write_excel_file(data_key, file_path, **kwargs)
```

## Dependencies

- CSV functions use stdlib.
- Excel functions require `pandas` and `openpyxl`.

## Behavior

These nodes return operation flags like `csv_success` / `excel_success` / `conversion_success`, plus row counts and output data/file paths.

## Example

```python
from microflow import csv_read, json_to_csv

read_users = csv_read("./users.csv", output_key="users")
export_flat = json_to_csv(data_key="users", output_file="./users_out.csv", flatten_nested=True)
```
