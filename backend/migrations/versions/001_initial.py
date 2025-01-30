"""Initial migration

Revision ID: 001
Revises: 
Create Date: 2025-01-30 15:03:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSON

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None

def upgrade() -> None:
    # Create api_keys table
    op.create_table(
        'api_keys',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('key_name', sa.String(), nullable=False),
        sa.Column('key_value', sa.String(), nullable=False),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('key_name')
    )
    op.create_index(op.f('ix_api_keys_key_name'), 'api_keys', ['key_name'], unique=True)

    # Create llm_models table
    op.create_table(
        'llm_models',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('model_name', sa.String(), nullable=False),
        sa.Column('provider', sa.String(), nullable=False),
        sa.Column('api_key_id', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('configuration', JSON, nullable=False, default={}),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('now()')),
        sa.ForeignKeyConstraint(['api_key_id'], ['api_keys.id'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('model_name')
    )
    op.create_index(op.f('ix_llm_models_model_name'), 'llm_models', ['model_name'], unique=True)

    # Create trigger for updating updated_at timestamp
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = now();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)

    # Add trigger to api_keys table
    op.execute("""
        CREATE TRIGGER update_api_keys_updated_at
            BEFORE UPDATE ON api_keys
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    """)

    # Add trigger to llm_models table
    op.execute("""
        CREATE TRIGGER update_llm_models_updated_at
            BEFORE UPDATE ON llm_models
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
    """)

def downgrade() -> None:
    # Drop triggers first
    op.execute("DROP TRIGGER IF EXISTS update_llm_models_updated_at ON llm_models;")
    op.execute("DROP TRIGGER IF EXISTS update_api_keys_updated_at ON api_keys;")
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column();")

    # Drop tables
    op.drop_table('llm_models')
    op.drop_table('api_keys')
