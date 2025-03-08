-- Enable the pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create schema
CREATE SCHEMA IF NOT EXISTS document_it;

-- Set search path
SET search_path TO document_it, public;

-- Create tables will be handled by SQLAlchemy/Alembic migrations