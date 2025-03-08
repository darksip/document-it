"""Initial schema

Revision ID: 001
Revises: 
Create Date: 2025-03-08

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
from pgvector.sqlalchemy import Vector

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create schema
    op.execute('CREATE SCHEMA IF NOT EXISTS document_it')
    
    # Set search path
    op.execute('SET search_path TO document_it, public')
    
    # Create documents table
    op.create_table(
        'documents',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('url', sa.String(2048), nullable=False),
        sa.Column('local_path', sa.String(1024), nullable=True),
        sa.Column('content_hash', sa.String(32), nullable=True),
        sa.Column('last_crawled', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('last_processed', sa.DateTime(), nullable=True),
        sa.Column('processing_required', sa.Boolean(), nullable=False, server_default=sa.text('true')),
        sa.Column('doc_metadata', JSONB, nullable=True),
        sa.UniqueConstraint('url', name='uq_document_url'),
        schema='document_it'
    )
    
    # Create index on content_hash
    op.create_index('ix_document_content_hash', 'documents', ['content_hash'], schema='document_it')
    
    # Create document_contents table
    op.create_table(
        'document_contents',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('document_id', UUID(as_uuid=True), nullable=False),
        sa.Column('content', sa.Text(), nullable=True),
        sa.Column('parsed_content', sa.Text(), nullable=True),
        sa.Column('structure_data', JSONB, nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['document_it.documents.id'], ondelete='CASCADE'),
        schema='document_it'
    )
    
    # Create document_embeddings table
    op.create_table(
        'document_embeddings',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('document_id', UUID(as_uuid=True), nullable=False),
        sa.Column('document_embedding', Vector(3072), nullable=True),
        sa.Column('chunk_embeddings', JSONB, nullable=True),
        sa.Column('chunk_metadata', JSONB, nullable=True),
        sa.Column('embedding_model', sa.String(100), nullable=False),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['document_id'], ['document_it.documents.id'], ondelete='CASCADE'),
        schema='document_it'
    )
    
    # Create index on document_id
    op.create_index('ix_document_embedding_document_id', 'document_embeddings', ['document_id'], schema='document_it')
    
    # Create document_chunks table
    op.create_table(
        'document_chunks',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('document_id', UUID(as_uuid=True), nullable=False),
        sa.Column('content', sa.Text(), nullable=False),
        sa.Column('chunk_index', sa.Integer(), nullable=False),
        sa.Column('chunk_metadata', JSONB, nullable=True),
        sa.Column('embedding', Vector(3072), nullable=True),
        sa.ForeignKeyConstraint(['document_id'], ['document_it.documents.id'], ondelete='CASCADE'),
        schema='document_it'
    )
    
    # Create indexes on document_id and chunk_index
    op.create_index('ix_document_chunk_document_id', 'document_chunks', ['document_id'], schema='document_it')
    op.create_index('ix_document_chunk_index', 'document_chunks', ['document_id', 'chunk_index'], schema='document_it')
    
    # Create document_analyses table
    op.create_table(
        'document_analyses',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('document_id', UUID(as_uuid=True), nullable=False),
        sa.Column('analysis_result', JSONB, nullable=False),
        sa.Column('analysis_time', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('model_version', sa.String(100), nullable=False),
        sa.ForeignKeyConstraint(['document_id'], ['document_it.documents.id'], ondelete='CASCADE'),
        schema='document_it'
    )
    
    # Create index on document_id
    op.create_index('ix_document_analysis_document_id', 'document_analyses', ['document_id'], schema='document_it')
    
    # Create document_relationships table
    op.create_table(
        'document_relationships',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('source_document_id', UUID(as_uuid=True), nullable=False),
        sa.Column('target_document_id', UUID(as_uuid=True), nullable=False),
        sa.Column('relationship_type', sa.String(100), nullable=False),
        sa.Column('relationship_strength', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['source_document_id'], ['document_it.documents.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['target_document_id'], ['document_it.documents.id'], ondelete='CASCADE'),
        schema='document_it'
    )
    
    # Create indexes on source_document_id, target_document_id, and relationship_type
    op.create_index('ix_document_relationship_source', 'document_relationships', ['source_document_id'], schema='document_it')
    op.create_index('ix_document_relationship_target', 'document_relationships', ['target_document_id'], schema='document_it')
    op.create_index('ix_document_relationship_type', 'document_relationships', ['relationship_type'], schema='document_it')
    
    # Create crawl_sessions table
    op.create_table(
        'crawl_sessions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, server_default=sa.text('gen_random_uuid()')),
        sa.Column('start_time', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('end_time', sa.DateTime(), nullable=True),
        sa.Column('status', sa.String(50), nullable=False, server_default=sa.text("'in_progress'")),
        sa.Column('config', JSONB, nullable=True),
        sa.Column('documents_processed', sa.Integer(), nullable=False, server_default=sa.text('0')),
        schema='document_it'
    )
    
    # Create crawl_session_documents table
    op.create_table(
        'crawl_session_documents',
        sa.Column('crawl_session_id', UUID(as_uuid=True), nullable=False),
        sa.Column('document_id', UUID(as_uuid=True), nullable=False),
        sa.ForeignKeyConstraint(['crawl_session_id'], ['document_it.crawl_sessions.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['document_id'], ['document_it.documents.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('crawl_session_id', 'document_id'),
        schema='document_it'
    )


def downgrade() -> None:
    # Drop tables
    op.drop_table('crawl_session_documents', schema='document_it')
    op.drop_table('crawl_sessions', schema='document_it')
    op.drop_table('document_relationships', schema='document_it')
    op.drop_table('document_analyses', schema='document_it')
    op.drop_table('document_chunks', schema='document_it')
    op.drop_table('document_embeddings', schema='document_it')
    op.drop_table('document_contents', schema='document_it')
    op.drop_table('documents', schema='document_it')
    
    # Drop schema
    op.execute('DROP SCHEMA IF EXISTS document_it')