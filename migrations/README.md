# Database Migrations with Alembic

This directory contains database migration scripts managed by Alembic.

## Prerequisites

- Python 3.11+
- Poetry (for dependency management)
- PostgreSQL database

## Setup

1. **Install Dependencies**
   ```bash
   poetry install
   ```

2. **Configure Database**
   - Copy `.env.example` to `.env` if it doesn't exist
   - Update the `POSTGRES_DSN` in `.env` with your database connection details

## Usage

### Create a New Migration
To create a new migration after making changes to your SQLAlchemy models:

```bash
# Create a new migration
poetry run alembic revision --autogenerate -m "Your migration message"

# Review the generated migration file in migrations/versions/
```

### Apply Migrations
To apply all pending migrations:

```bash
poetry run alembic upgrade head
```

### Rollback Migrations
To rollback the last migration:

```bash
poetry run alembic downgrade -1
```

### View Current Migration Status
```bash
poetry run alembic current
```

## Configuration

- `alembic.ini`: Main configuration file
- `env.py`: Migration environment setup (uses settings from `.env`)
- `script.py.mako`: Template for new migration files

## Best Practices

1. Always review auto-generated migrations before applying them
2. Write idempotent migration scripts
3. Test migrations in a development environment first
4. Keep migration files in version control
5. Document any data migration steps in the migration file

## Troubleshooting

- If you get connection errors, verify your `.env` file has the correct database credentials
- If you encounter issues with missing tables, ensure your models are properly imported in `env.py`
- For other issues, check the logs or run with `--verbose` for more details
