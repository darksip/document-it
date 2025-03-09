"""
Add trace IDs for observability.

Revision ID: 002
Revises: 001
Create Date: 2025-03-09 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade():
    # Add trace_id column to documents table
    op.add_column('documents', sa.Column('trace_id', sa.String(36), nullable=True), schema='document_it')
    op.create_index('ix_document_trace_id', 'documents', ['trace_id'], schema='document_it')
    
    # Add trace_id column to document_contents table
    op.add_column('document_contents', sa.Column('trace_id', sa.String(36), nullable=True), schema='document_it')
    op.create_index('ix_document_content_trace_id', 'document_contents', ['trace_id'], schema='document_it')
    
    # Add trace_id column to document_embeddings table
    op.add_column('document_embeddings', sa.Column('trace_id', sa.String(36), nullable=True), schema='document_it')
    op.create_index('ix_document_embedding_trace_id', 'document_embeddings', ['trace_id'], schema='document_it')
    
    # Add trace_id column to document_chunks table
    op.add_column('document_chunks', sa.Column('trace_id', sa.String(36), nullable=True), schema='document_it')
    op.create_index('ix_document_chunk_trace_id', 'document_chunks', ['trace_id'], schema='document_it')
    
    # Add trace_id column to document_analyses table
    op.add_column('document_analyses', sa.Column('trace_id', sa.String(36), nullable=True), schema='document_it')
    op.create_index('ix_document_analysis_trace_id', 'document_analyses', ['trace_id'], schema='document_it')
    
    # Add trace_id column to document_relationships table
    op.add_column('document_relationships', sa.Column('trace_id', sa.String(36), nullable=True), schema='document_it')
    op.create_index('ix_document_relationship_trace_id', 'document_relationships', ['trace_id'], schema='document_it')
    
    # Add trace_id column to crawl_sessions table
    op.add_column('crawl_sessions', sa.Column('trace_id', sa.String(36), nullable=True), schema='document_it')
    op.create_index('ix_crawl_session_trace_id', 'crawl_sessions', ['trace_id'], schema='document_it')


def downgrade():
    # Drop trace_id column from documents table
    op.drop_index('ix_document_trace_id', table_name='documents', schema='document_it')
    op.drop_column('documents', 'trace_id', schema='document_it')
    
    # Drop trace_id column from document_contents table
    op.drop_index('ix_document_content_trace_id', table_name='document_contents', schema='document_it')
    op.drop_column('document_contents', 'trace_id', schema='document_it')
    
    # Drop trace_id column from document_embeddings table
    op.drop_index('ix_document_embedding_trace_id', table_name='document_embeddings', schema='document_it')
    op.drop_column('document_embeddings', 'trace_id', schema='document_it')
    
    # Drop trace_id column from document_chunks table
    op.drop_index('ix_document_chunk_trace_id', table_name='document_chunks', schema='document_it')
    op.drop_column('document_chunks', 'trace_id', schema='document_it')
    
    # Drop trace_id column from document_analyses table
    op.drop_index('ix_document_analysis_trace_id', table_name='document_analyses', schema='document_it')
    op.drop_column('document_analyses', 'trace_id', schema='document_it')
    
    # Drop trace_id column from document_relationships table
    op.drop_index('ix_document_relationship_trace_id', table_name='document_relationships', schema='document_it')
    op.drop_column('document_relationships', 'trace_id', schema='document_it')
    
    # Drop trace_id column from crawl_sessions table
    op.drop_index('ix_crawl_session_trace_id', table_name='crawl_sessions', schema='document_it')
    op.drop_column('crawl_sessions', 'trace_id', schema='document_it')