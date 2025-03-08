# Docker Compose Configuration for PostgreSQL with pgvector

This document provides the docker-compose configuration for setting up PostgreSQL with the pgvector extension for the document-it project.

## Configuration

Save the following configuration as `docker-compose.yml` in the project root:

```yaml
version: '3.8'

services:
  postgres:
    image: ankane/pgvector:latest
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./init-scripts:/docker-entrypoint-initdb.d
    environment:
      POSTGRES_DB: document_it
      POSTGRES_USER: document_it_user
      POSTGRES_PASSWORD: ${POSTGRES_PASSWORD}
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U document_it_user -d document_it"]
      interval: 10s
      timeout: 5s
      retries: 5

  # Optional: Add pgAdmin for database management
  pgadmin:
    image: dpage/pgadmin4:latest
    ports:
      - "5050:80"
    environment:
      PGADMIN_DEFAULT_EMAIL: ${PGADMIN_EMAIL:-admin@document-it.com}
      PGADMIN_DEFAULT_PASSWORD: ${PGADMIN_PASSWORD}
    volumes:
      - pgadmin_data:/var/lib/pgadmin
    depends_on:
      - postgres

volumes:
  postgres_data:
  pgadmin_data:
```

## Initialization Script

Create a directory named `init-scripts` in the project root and add a file named `01-init.sql` with the following content:

```sql
-- Enable the pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create schema
CREATE SCHEMA IF NOT EXISTS document_it;

-- Set search path
SET search_path TO document_it, public;

-- Create tables will be handled by SQLAlchemy/Alembic migrations
```

## Environment Variables

Add the following to your `.env` file:

```
# PostgreSQL Configuration
DATABASE_URL=postgresql://document_it_user:${POSTGRES_PASSWORD}@localhost:5432/document_it

# Docker Postgres credentials (used by docker-compose)
POSTGRES_PASSWORD=secure_password
PGADMIN_EMAIL=admin@document-it.com
PGADMIN_PASSWORD=admin_password
```

## Usage Instructions

1. **Start the database**:
   ```bash
   docker-compose up -d
   ```

2. **Shut down the database**:
   ```bash
   docker-compose down
   ```

3. **View logs**:
   ```bash
   docker-compose logs -f postgres
   ```

4. **Access pgAdmin**:
   Open http://localhost:5050 in your browser and login with the credentials from your .env file.

## Adding the Database in pgAdmin

1. In pgAdmin, right-click on "Servers" and select "Register > Server"
2. On the "General" tab, enter "document-it" as the Name
3. On the "Connection" tab, enter:
   - Host: postgres (the service name in docker-compose)
   - Port: 5432
   - Maintenance database: document_it
   - Username: document_it_user
   - Password: (the password from POSTGRES_PASSWORD in .env)
4. Click "Save"

## Backup and Restore

### Create a backup

```bash
docker-compose exec postgres pg_dump -U document_it_user -d document_it -F c -f /tmp/document_it_backup.dump
docker cp $(docker-compose ps -q postgres):/tmp/document_it_backup.dump ./document_it_backup.dump
```

### Restore from backup

```bash
docker cp ./document_it_backup.dump $(docker-compose ps -q postgres):/tmp/document_it_backup.dump
docker-compose exec postgres pg_restore -U document_it_user -d document_it -c /tmp/document_it_backup.dump