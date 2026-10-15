## Overview

In many companies, business teams need to send files to data pipelines for reporting but sometimes theses files contain missing values, incorrect formats or unexpected columns. These issues can cause ingestion errors.

This desktop application was created to help prevent theses problems. It allows users to check their files before ingestion, using validation rules defined by the data governance team.
Users only need to select a data product, choose a CSV file and run the validation. If the file passes all checks, its marked as ready for ingestion. Otherwise the application shows the errors that need to be corrected.

## Features

- Simple desktop interface built with Tkinter.
- CSV file validation using YAML contracts.
- Support for multiple business areas and data products.
- Automatic detection of available YAML contracts.
- Preview of the first 10 rows before validation.
- Validation of column names and data types.
- Detection of missing values and duplicate values.
- Numeric range validation.
- Allowed values validation.
- Date and text format validation using Regex.
- Validation progress and error logs.
- Automatic file organization by date and time.
- Lightweight application.

## How It Works

1. The data team or data steward defines validation rules in a YAML file.
2. A business users opens the application and selects the data product.
3. The user chooses a CSV file from their computer. The application will display the first 10 rows of that file.
4. The user clicks **Validate File**.
5. The application checks the file against the data contract.
6. The validation results are displayed on the screen

| Status | Description |
|--------|-------------|
| APPROVED | The file passed all validation rules and is ready for ingestion. |
| REJECTED | The file contains errors that need to be corrected. |

**Note:** It does not automatically send files to a production data pipeline. It can be adjusted by the data engineers team.

## Project Structure

```text
data-contract-validator/
├── main.py
├── ui/
│   ├── __init__.py
│   └── app.py
├── validators/
│   ├── __init__.py
│   ├── engine.py
│   ├── rules.py
│   └── regex.py
├── contracts/
│   ├── finance/
│   │   └── transactions.yaml
│   └── procurement/
│       └── providers.yaml
├── tests/
├── requirements.txt
├── .gitignore
└── README.md
```

Each data product has its own YAML file. These contracts define the expected columns, data types, and validation rules.

### YAML Example

```yaml
contract:
  name: finance_transactions
  version: "1.0"
  owner: Finance
  description: Financial transactions validation
file:
  format: csv
  delimiter: ","
  encoding: utf-8
  allow_extra_columns: false
columns:
  - name: transaction_id
    type: integer
    nullable: false
    unique: true
  - name: customer_id
    type: integer
    nullable: false
  - name: amount
    type: decimal
    nullable: false
    min: 0
  - name: currency
    type: string
    nullable: false
    allowed_values:
      - PEN
      - USD
  - name: transaction_date
    type: date
    format: "%Y-%m-%d"
    nullable: false
  - name: email
    type: string
    nullable: true
    regex: email
```

## Available Validation Rules

| Rule | Description |
|------|-------------|
| type | Checks if the value matches the expected data type. |
| nullable | Checks if empty values are allowed. |
| unique | Checks for duplicate values in a column. |
| min | Defines the minimum allowed numeric value. |
| max | Defines the maximum allowed numeric value. |
| allowed_values | Defines a list of accepted values. |
| regex | Checks text formats using predefined patterns. |
| format | Defines the expected date format. |
| allow_extra_columns | Controls whether additional CSV columns are accepted. |

### Supported Data Types

- `string`
- `integer`
- `decimal`
- `date`
- `boolean`

## File Organization

When a user selects a CSV file, the application creates a copy inside the `input` folder.
Files are organized by business area, year, month, day, and time.

Example:

```text
input/
└── finance/
    └── 2025/
        └── 10/
            └── 15/
                └── 083000_123456/
                    └── transactions.csv
```
This structure helps organize received files and reduces the chance of overwriting previous uploads. The original file remains unchanged.

## Installation

### 1. Clone the repo

```bash
git clone https://github.com/Rscaballero-data/data-contract-validator.git
cd data-contract-validator
```

### Requirements

- Python 3.10 or newer
- Tkinter
- PyYAML

### 2. Create a virtual environment

Linux:

```bash
python -m venv .venv
source .venv/bin/activate
```

Windows:

```powershell
python -m venv .venv
.venv\Scripts\activate
```
### 3. Install dependencies

```bash
python -m pip install -r requirements.txt
```
### 4. Run the application

```bash
python main.py
```

## Portable Version

The application can also be packaged using PyInstaller. This allows business users to run it without installing Python.

```bash
python -m PyInstaller --onefile --windowed --name DataContractValidator main.py
```

The generated executable can be distributed together with the `contracts` folder.

```text
DataContractValidator/
├── DataContractValidator
└── contracts/
    ├── finance/
    └── procurement/
```
## Technologies Used

| Technology | Purpose |
|------------|---------|
| Python | Main programming language |
| Tkinter | Desktop user interface |
| PyYAML | Read YAML data contracts |
| CSV | Read and process CSV files |
| Regex | Validate text patterns |
| Threading | Run validation without freezing the interface |
| PyInstaller | Package the application as a standalone executable |

## Future Improvements

- Export validation results to JSON and save validation history.
- Support other file formats.
- Add more data quality rules.
- Connect approved files to ingestion pipelines.
- Support cloud storage integration.
