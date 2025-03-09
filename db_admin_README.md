# Database Administration Tool

This tool provides command-line utilities for managing the Document-it database, including resetting the database, checking its status, and performing maintenance tasks.

## Overview

The `db_admin.py` script offers several commands for database management:

- **reset**: Drop and recreate all tables in the database
- **status**: Check the status of the database connection and tables
- **vacuum**: Perform VACUUM operation to reclaim storage and optimize the database
- **init**: Initialize the database schema without dropping existing tables
- **truncate**: Clear data from specific tables or all tables

## Prerequisites

- PostgreSQL database with pgvector extension installed
- DATABASE_URL environment variable set (or provided via command-line option)
- Python 3.8+ with required dependencies installed

## Installation

No special installation is required. The script uses the existing Document-it database configuration.

## Usage

### Basic Usage

```bash
# Show help
python db_admin.py --help

# Show help for a specific command
python db_admin.py reset --help
```

### Reset Database

Drops all tables and recreates them, effectively resetting the database to a clean state.

```bash
# With confirmation prompt
python db_admin.py reset

# Skip confirmation prompt
python db_admin.py reset --force
```

### Check Database Status

Displays information about the database connection, tables, and row counts.

```bash
python db_admin.py status
```

Example output:
```
2025-03-09 09:15:23,456 - document-it.db-admin - INFO - Database connection successful
2025-03-09 09:15:23,567 - document-it.db-admin - INFO - pgvector extension is installed
2025-03-09 09:15:23,678 - document-it.db-admin - INFO - Database has 7 tables
2025-03-09 09:15:23,789 - document-it.db-admin - INFO - Table documents: 120 rows
2025-03-09 09:15:23,890 - document-it.db-admin - INFO - Table document_contents: 120 rows
2025-03-09 09:15:23,901 - document-it.db-admin - INFO - Table document_embeddings: 98 rows
2025-03-09 09:15:23,912 - document-it.db-admin - INFO - Table document_chunks: 1543 rows
2025-03-09 09:15:23,923 - document-it.db-admin - INFO - Table document_analyses: 87 rows
2025-03-09 09:15:23,934 - document-it.db-admin - INFO - Table document_relationships: 45 rows
2025-03-09 09:15:23,945 - document-it.db-admin - INFO - Table crawl_sessions: 5 rows
```

### Vacuum Database

Performs a VACUUM FULL ANALYZE operation to reclaim storage and update statistics.

```bash
python db_admin.py vacuum
```

### Initialize Schema

Creates tables if they don't exist, without dropping existing tables.

```bash
python db_admin.py init
```

### Truncate Tables

Clears data from specific tables or all tables.

```bash
# Truncate all tables (with confirmation prompt)
python db_admin.py truncate

# Truncate specific tables
python db_admin.py truncate --tables documents document_contents

# Skip confirmation prompt
python db_admin.py truncate --force
```

### Custom Database URL

You can specify a custom database URL for any command:

```bash
python db_admin.py status --database-url postgresql://user:password@localhost:5432/document_it
```

## Use Cases

### Testing

Reset the database before running tests to ensure a clean state:

```bash
python db_admin.py reset --force && python run_database_tests.py
```

### Development

Initialize the schema in a new development environment:

```bash
python db_admin.py init
```

### Maintenance

Reclaim storage and optimize the database:

```bash
python db_admin.py vacuum
```

### Troubleshooting

Check the database status to verify connection and table counts:

```bash
python db_admin.py status
```

## Error Handling

The tool provides detailed error messages and logs for all operations. If an operation fails, check the log output for more information.

## Safety Features

Destructive operations (reset, truncate) require confirmation unless the `--force` flag is used. This helps prevent accidental data loss.