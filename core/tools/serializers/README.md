# Tool Serialization

JSON ↔ Tool Object Conversion for the Tools Specification System

## Overview

This module provides comprehensive serialization and deserialization functionality for Tool objects, enabling seamless conversion between JSON and Python Tool specifications.

## Features

- ✅ **Serialize Tools to JSON** - Convert any Tool object to JSON string
- ✅ **Serialize Tools to Dict** - Convert any Tool object to Python dictionary  
- ✅ **Deserialize JSON to Tools** - Create Tool objects from JSON strings
- ✅ **Deserialize Dict to Tools** - Create Tool objects from Python dictionaries
- ✅ **Automatic Type Detection** - Automatically instantiates correct Tool subclass
- ✅ **All Tool Types Supported** - Function, HTTP, DB (DynamoDB, PostgreSQL, MySQL, SQLite)
- ✅ **Round-trip Safe** - Preserve all data through serialization/deserialization cycles
- ✅ **Pydantic Integration** - Leverages Pydantic for validation

## Quick Start

### Installation

```python
from core.tools import (
    tool_to_json,
    tool_to_dict,
    tool_from_json,
    tool_from_dict,
)
```

### Basic Usage

```python
from core.tools import FunctionToolSpec, tool_to_json, tool_from_json

# Create a tool
tool = FunctionToolSpec(
    id="my-tool",
    tool_name="calculator",
    description="Perform calculations",
    parameters=[...]
)

# Convert to JSON
json_str = tool_to_json(tool)

# Convert back to Tool
restored_tool = tool_from_json(json_str)
```

## API Reference

### `tool_to_json(tool, *, indent=2, exclude_none=True, exclude_unset=False)`

Serialize a Tool object to a JSON string.

**Parameters:**
- `tool`: Tool specification object to serialize
- `indent`: Number of spaces for JSON indentation (default: 2)
- `exclude_none`: Exclude fields with None values (default: True)
- `exclude_unset`: Exclude fields that weren't explicitly set (default: False)

**Returns:** JSON string representation

**Example:**
```python
json_str = tool_to_json(tool, indent=4)
```

---

### `tool_to_dict(tool, *, exclude_none=True, exclude_unset=False)`

Serialize a Tool object to a Python dictionary.

**Parameters:**
- `tool`: Tool specification object to serialize
- `exclude_none`: Exclude fields with None values (default: True)
- `exclude_unset`: Exclude fields that weren't explicitly set (default: False)

**Returns:** Dictionary representation

**Example:**
```python
tool_dict = tool_to_dict(tool)
```

---

### `tool_from_json(json_str, *, strict=False)`

Deserialize a JSON string to a Tool object.

Automatically detects the correct tool type and instantiates the appropriate subclass.

**Parameters:**
- `json_str`: JSON string to deserialize
- `strict`: Whether to validate strictly (default: False)

**Returns:** Tool specification object (correct subclass)

**Raises:** `ToolSerializationError` if deserialization fails

**Example:**
```python
tool = tool_from_json(json_str)
```

---

### `tool_from_dict(data, *, strict=False)`

Deserialize a dictionary to a Tool object.

Automatically detects the correct tool type based on `tool_type` and `driver` fields.

**Parameters:**
- `data`: Dictionary containing tool data
- `strict`: Whether to validate strictly (default: False)

**Returns:** Tool specification object (correct subclass)

**Raises:** `ToolSerializationError` if deserialization fails

**Example:**
```python
tool = tool_from_dict(data)
```

## Supported Tool Types

### Function Tools
```python
{
    "id": "calculator-v1",
    "tool_name": "calculator",
    "tool_type": "function",
    "parameters": [...]
}
```

### HTTP Tools
```python
{
    "id": "api-client-v1",
    "tool_name": "fetch_data",
    "tool_type": "http",
    "url": "https://api.example.com/data",
    "method": "GET",
    "parameters": [...]
}
```

### Database Tools

#### DynamoDB
```python
{
    "id": "dynamo-tool-v1",
    "tool_name": "get_item",
    "tool_type": "db",
    "driver": "dynamodb",
    "region": "us-west-2",
    "table_name": "my-table",
    "parameters": [...]
}
```

#### PostgreSQL
```python
{
    "id": "pg-tool-v1",
    "tool_name": "query",
    "tool_type": "db",
    "driver": "postgresql",
    "host": "localhost",
    "port": 5432,
    "database": "mydb",
    "username": "user",
    "password": "pass",
    "parameters": [...]
}
```

#### MySQL
```python
{
    "id": "mysql-tool-v1",
    "tool_name": "query",
    "tool_type": "db",
    "driver": "mysql",
    "host": "localhost",
    "port": 3306,
    "database": "mydb",
    "username": "user",
    "password": "pass",
    "parameters": [...]
}
```

#### SQLite
```python
{
    "id": "sqlite-tool-v1",
    "tool_name": "query",
    "tool_type": "db",
    "driver": "sqlite",
    "database_path": "/path/to/db.sqlite",
    "parameters": [...]
}
```

## Common Use Cases

### 1. Storing Tools in a Database

```python
# Serialize tool for storage
json_str = tool_to_json(tool)
db.save(tool_id, json_str)

# Retrieve and deserialize
json_str = db.get(tool_id)
tool = tool_from_json(json_str)
```

### 2. API Communication

```python
# Send tool as JSON in API request
response = requests.post(
    "https://api.example.com/tools",
    json=tool_to_dict(tool)
)

# Receive tool from API response
tool = tool_from_dict(response.json())
```

### 3. Configuration Files

```python
# Load tool from JSON file
with open("tool-config.json") as f:
    json_str = f.read()
    tool = tool_from_json(json_str)

# Save tool to JSON file
with open("tool-config.json", "w") as f:
    f.write(tool_to_json(tool, indent=2))
```

### 4. Tool Templates

```python
# Create tool from template JSON
template = """
{
    "id": "template-v1",
    "tool_name": "generic_tool",
    "tool_type": "function",
    "parameters": []
}
"""
tool = tool_from_json(template)

# Customize and use
tool.tool_name = "my_custom_tool"
tool.description = "My custom implementation"
```

## Error Handling

```python
from core.tools import tool_from_json, ToolSerializationError

try:
    tool = tool_from_json(json_str)
except ToolSerializationError as e:
    print(f"Deserialization failed: {e}")
    # Handle error appropriately
```

## Advanced Features

### Custom Database Drivers

Register custom database drivers for unsupported databases:

```python
from core.tools.serializers import register_db_driver
from core.tools.spec.tool_types import DbToolSpec

class MongoDbToolSpec(DbToolSpec):
    driver: str = Field(default="mongodb")
    connection_string: str
    database: str
    collection: str

# Register the custom driver
register_db_driver("mongodb", MongoDbToolSpec)

# Now tool_from_json/dict will work with mongodb tools
```

### Helper Functions

```python
from core.tools.serializers import (
    get_supported_tool_types,
    get_supported_db_drivers
)

# Get list of supported types
tool_types = get_supported_tool_types()
# ['function', 'http', 'db']

db_drivers = get_supported_db_drivers()
# ['dynamodb', 'postgresql', 'mysql', 'sqlite']
```

## Testing

Run the comprehensive test suite:

```bash
uv run pytest tests/tools/test_tool_serializer.py -v
```

Test coverage:
- ✅ Serialization to JSON (5 tests)
- ✅ Serialization to Dict (3 tests)  
- ✅ Deserialization from JSON (6 tests)
- ✅ Deserialization from Dict (3 tests)
- ✅ All Tool Types (1 test)
- ✅ Error Handling (4 tests)
- ✅ Round-trip Conversion (4 tests)

**Total: 26 tests, 100% passing**

## Examples

See `examples/tool_serialization_example.py` for comprehensive examples of all functionality.

Run the examples:
```bash
python examples/tool_serialization_example.py
```

## License

Part of the Tools Specification System v1.2.0

