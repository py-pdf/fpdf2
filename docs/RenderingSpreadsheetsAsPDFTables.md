# Rendering spreadsheets as PDF tables

<img src="table-from-spreadsheet.png" style="max-width: 15rem">

All the details on tables and options to style them are detailed on the dedicated page: [Tables](Tables.md).

## From a .csv spreadsheet
Example input file: [color_srgb.csv](./color_srgb.csv)
```python
{% include "../tutorial/csv2table.py" %}
```

## From a .xlsx spreadsheet
Example input file: [color_srgb.xlsx](./color_srgb.xlsx)
```python
{% include "../tutorial/xlsx2table.py" %}
```

## From an .ods spreadsheet
Example input file: [color_srgb.ods](./color_srgb.ods)
```python
{% include "../tutorial/ods2table.py" %}
```

## From pandas DataFrame
_cf._ [Maths documentation page](Maths.md#using-pandas)
