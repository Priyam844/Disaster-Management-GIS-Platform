"""Initial migration

Revision ID: 0001
Revises: 
Create Date: 2026-09-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import geoalchemy2

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Enable PostGIS extension
    op.execute('CREATE EXTENSION IF NOT EXISTS postgis;')
    op.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp";')
    op.execute('CREATE EXTENSION IF NOT EXISTS postgis_topology;')
    
    # Create enums
    op.execute("""
        CREATE TYPE hazard_type_enum AS ENUM (
            'LANDSLIDE', 'FLOOD', 'COASTAL_EROSION', 'CLOUDBURST', 'EARTHQUAKE'
        );
    """)
    op.execute("""
        CREATE TYPE severity_level_enum AS ENUM (
            'VERY_LOW', 'LOW', 'MODERATE', 'HIGH', 'VERY_HIGH'
        );
    """)
    op.execute("""
        CREATE TYPE priority_tier_enum AS ENUM (
            'IMMEDIATE', 'SHORT_TERM', 'MEDIUM_TERM', 'NOT_REQUIRED'
        );
    """)
    op.execute("""
        CREATE TYPE relocation_status_enum AS ENUM (
            'PENDING', 'IN_PROGRESS', 'COMPLETED', 'ON_HOLD', 'CANCELLED'
        );
    """)
    op.execute("""
        CREATE TYPE model_status_enum AS ENUM (
            'STAGING', 'PRODUCTION', 'ARCHIVED'
        );
    """)
    op.execute("""
        CREATE TYPE ingestion_status_enum AS ENUM (
            'STARTED', 'SUCCESS', 'FAILED', 'PARTIAL'
        );
    """)
    op.execute("""
        CREATE TYPE user_role_enum AS ENUM (
            'ADMIN', 'ANALYST', 'VIEWER'
        );
    """)
    
    # States table
    op.create_table(
        'states',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('code', sa.String(10), nullable=False, unique=True),
        sa.Column('geom', geoalchemy2.Geometry(geometry_type='MULTIPOLYGON', srid=4326, spatial_index=True), nullable=False),
        sa.Column('metadata', postgresql.JSONB, default={}, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('idx_states_geom', 'states', ['geom'], postgresql_using='gist')
    
    # Districts table
    op.create_table(
        'districts',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('state_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('states.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('code', sa.String(20), nullable=False),
        sa.Column('geom', geoalchemy2.Geometry(geometry_type='MULTIPOLYGON', srid=4326, spatial_index=True), nullable=False),
        sa.Column('metadata', postgresql.JSONB, default={}, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_unique_constraint('uq_district_state_code', 'districts', ['state_id', 'code'])
    op.create_index('idx_districts_geom', 'districts', ['geom'], postgresql_using='gist')
    
    # Habitations table
    op.create_table(
        'habitations',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('district_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('districts.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('state_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('states.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('geom', geoalchemy2.Geometry(geometry_type='POINT', srid=4326, spatial_index=True), nullable=False),
        sa.Column('boundary_geom', geoalchemy2.Geometry(geometry_type='POLYGON', srid=4326, spatial_index=True), nullable=True),
        sa.Column('population', sa.Integer, nullable=True),
        sa.Column('households', sa.Integer, nullable=True),
        sa.Column('socioeconomic_vulnerability', sa.DECIMAL(5,2), nullable=True),
        sa.Column('physical_vulnerability', sa.DECIMAL(5,2), nullable=True),
        sa.Column('composite_vulnerability', sa.DECIMAL(5,2), nullable=True, index=True),
        sa.Column('literacy_rate', sa.DECIMAL(5,2), nullable=True),
        sa.Column('pucca_houses_pct', sa.DECIMAL(5,2), nullable=True),
        sa.Column('sc_st_pct', sa.DECIMAL(5,2), nullable=True),
        sa.Column('female_headed_pct', sa.DECIMAL(5,2), nullable=True),
        sa.Column('disability_pct', sa.DECIMAL(5,2), nullable=True),
        sa.Column('road_access_km', sa.DECIMAL(8,2), nullable=True),
        sa.Column('healthcare_access_km', sa.DECIMAL(8,2), nullable=True),
        sa.Column('metadata', postgresql.JSONB, default={}, nullable=False),
        sa.Column('assessed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('idx_habitations_geom', 'habitations', ['geom'], postgresql_using='gist')
    
    # Hazard Zones table
    op.create_table(
        'hazard_zones',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('hazard_type', postgresql.ENUM('LANDSLIDE', 'FLOOD', 'COASTAL_EROSION', 'CLOUDBURST', 'EARTHQUAKE', name='hazard_type_enum', create_constraint=True), nullable=False, index=True),
        sa.Column('severity', postgresql.ENUM('VERY_LOW', 'LOW', 'MODERATE', 'HIGH', 'VERY_HIGH', name='severity_level_enum', create_constraint=True), nullable=False, index=True),
        sa.Column('severity_score', sa.DECIMAL(4,2), nullable=True),
        sa.Column('geom', geoalchemy2.Geometry(geometry_type='POLYGON', srid=4326, spatial_index=True), nullable=False),
        sa.Column('valid_from', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('valid_to', sa.DateTime(timezone=True), nullable=True),
        sa.Column('source', sa.String(100), nullable=False, index=True),
        sa.Column('model_version', sa.String(50), nullable=True),
        sa.Column('confidence_score', sa.DECIMAL(4,2), nullable=True),
        sa.Column('metadata', postgresql.JSONB, default={}, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('idx_hazard_zones_geom', 'hazard_zones', ['geom'], postgresql_using='gist')
    op.create_index('idx_hazard_zones_type_severity', 'hazard_zones', ['hazard_type', 'severity'])
    op.create_index('idx_hazard_zones_temporal', 'hazard_zones', ['valid_from', 'valid_to'])
    
    # Disaster Events table
    op.create_table(
        'disaster_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('hazard_type', postgresql.ENUM('LANDSLIDE', 'FLOOD', 'COASTAL_EROSION', 'CLOUDBURST', 'EARTHQUAKE', name='hazard_type_enum_disaster', create_constraint=True), nullable=False, index=True),
        sa.Column('event_name', sa.String(200), nullable=True),
        sa.Column('event_date', sa.Date, nullable=False, index=True),
        sa.Column('end_date', sa.Date, nullable=True),
        sa.Column('affected_geom', geoalchemy2.Geometry(geometry_type='GEOMETRY', srid=4326, spatial_index=True), nullable=True),
        sa.Column('affected_habitations', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), default=list, nullable=False),
        sa.Column('casualties', sa.Integer, nullable=True),
        sa.Column('injured', sa.Integer, nullable=True),
        sa.Column('displaced', sa.Integer, nullable=True),
        sa.Column('houses_damaged', sa.Integer, nullable=True),
        sa.Column('economic_loss_inr', sa.BigInteger, nullable=True),
        sa.Column('source', sa.String(100), nullable=True),
        sa.Column('verified', sa.Boolean, default=False, nullable=False),
        sa.Column('metadata', postgresql.JSONB, default={}, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('idx_disaster_events_geom', 'disaster_events', ['affected_geom'], postgresql_using='gist')
    op.create_index('idx_disaster_events_type_date', 'disaster_events', ['hazard_type', 'event_date'])
    
    # Relocation Sites table
    op.create_table(
        'relocation_sites',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('district_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('districts.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('name', sa.String(200), nullable=False),
        sa.Column('geom', geoalchemy2.Geometry(geometry_type='POLYGON', srid=4326, spatial_index=True), nullable=False),
        sa.Column('total_area_ha', sa.DECIMAL(10,2), nullable=False),
        sa.Column('buildable_area_ha', sa.DECIMAL(10,2), nullable=True),
        sa.Column('agricultural_area_ha', sa.DECIMAL(10,2), nullable=True),
        sa.Column('forest_area_ha', sa.DECIMAL(10,2), nullable=True),
        sa.Column('water_body_area_ha', sa.DECIMAL(10,2), nullable=True),
        sa.Column('water_availability_score', sa.DECIMAL(4,2), nullable=True),
        sa.Column('road_access_score', sa.DECIMAL(4,2), nullable=True),
        sa.Column('electricity_access', sa.Boolean, default=False, nullable=False),
        sa.Column('healthcare_facility_km', sa.DECIMAL(8,2), nullable=True),
        sa.Column('school_facility_km', sa.DECIMAL(8,2), nullable=True),
        sa.Column('market_facility_km', sa.DECIMAL(8,2), nullable=True),
        sa.Column('current_population', sa.Integer, default=0, nullable=False),
        sa.Column('max_carrying_capacity', sa.Integer, nullable=True),
        sa.Column('recommended_capacity', sa.Integer, nullable=True),
        sa.Column('land_suitability_score', sa.DECIMAL(4,2), nullable=True),
        sa.Column('water_suitability_score', sa.DECIMAL(4,2), nullable=True),
        sa.Column('infrastructure_suitability_score', sa.DECIMAL(4,2), nullable=True),
        sa.Column('environmental_suitability_score', sa.DECIMAL(4,2), nullable=True),
        sa.Column('composite_suitability_score', sa.DECIMAL(4,2), nullable=True, index=True),
        sa.Column('flood_risk', sa.Boolean, default=False, nullable=False),
        sa.Column('landslide_risk', sa.Boolean, default=False, nullable=False),
        sa.Column('seismic_zone', sa.Integer, nullable=True),
        sa.Column('ecological_sensitivity', sa.String(20), nullable=True),
        sa.Column('land_ownership', sa.String(50), nullable=True),
        sa.Column('assessment_date', sa.Date, nullable=False),
        sa.Column('assessed_by', sa.String(100), nullable=True),
        sa.Column('metadata', postgresql.JSONB, default={}, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('idx_relocation_sites_geom', 'relocation_sites', ['geom'], postgresql_using='gist')
    op.create_index('idx_relocation_sites_district', 'relocation_sites', ['district_id'])
    op.create_index('idx_relocation_sites_suitability', 'relocation_sites', ['composite_suitability_score'])
    
    # Relocation Priorities table
    op.create_table(
        'relocation_priorities',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('habitation_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('habitations.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('recommended_site_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('relocation_sites.id', ondelete='SET NULL'), nullable=True, index=True),
        sa.Column('alternative_site_ids', postgresql.ARRAY(postgresql.UUID(as_uuid=True)), default=list, nullable=False),
        sa.Column('priority_tier', postgresql.ENUM('IMMEDIATE', 'SHORT_TERM', 'MEDIUM_TERM', 'NOT_REQUIRED', name='priority_tier_enum', create_constraint=True), nullable=False, index=True),
        sa.Column('priority_rank', sa.Integer, nullable=True),
        sa.Column('hazard_exposure_score', sa.DECIMAL(5,2), nullable=True),
        sa.Column('vulnerability_score', sa.DECIMAL(5,2), nullable=True),
        sa.Column('capacity_gap_score', sa.DECIMAL(5,2), nullable=True),
        sa.Column('distance_score', sa.DECIMAL(5,2), nullable=True),
        sa.Column('cost_effectiveness_score', sa.DECIMAL(5,2), nullable=True),
        sa.Column('composite_priority_score', sa.DECIMAL(5,2), nullable=True, index=True),
        sa.Column('distance_to_site_km', sa.DECIMAL(8,2), nullable=True),
        sa.Column('estimated_relocation_cost_inr', sa.BigInteger, nullable=True),
        sa.Column('estimated_timeline_months', sa.Integer, nullable=True),
        sa.Column('status', postgresql.ENUM('PENDING', 'IN_PROGRESS', 'COMPLETED', 'ON_HOLD', 'CANCELLED', name='relocation_status_enum', create_constraint=True), default='PENDING', nullable=False),
        sa.Column('approved_by', sa.String(100), nullable=True),
        sa.Column('approved_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('notes', sa.Text, nullable=True),
        sa.Column('model_version', sa.String(50), nullable=True),
        sa.Column('computed_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_unique_constraint('uq_priority_habitation_version', 'relocation_priorities', ['habitation_id', 'model_version'])
    op.create_index('idx_relocation_priorities_tier', 'relocation_priorities', ['priority_tier'])
    op.create_index('idx_relocation_priorities_site', 'relocation_priorities', ['recommended_site_id'])
    op.create_index('idx_relocation_priorities_score', 'relocation_priorities', ['composite_priority_score'])
    
    # ML Models table
    op.create_table(
        'ml_models',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('name', sa.String(100), nullable=False),
        sa.Column('version', sa.String(50), nullable=False),
        sa.Column('model_type', sa.String(50), nullable=True),
        sa.Column('hazard_type', postgresql.ENUM('LANDSLIDE', 'FLOOD', 'COASTAL_EROSION', 'CLOUDBURST', 'EARTHQUAKE', name='hazard_type_enum_model', create_constraint=True), nullable=True),
        sa.Column('framework', sa.String(50), nullable=True),
        sa.Column('artifact_path', sa.String(500), nullable=True),
        sa.Column('metrics', postgresql.JSONB, nullable=True),
        sa.Column('training_data_hash', sa.String(64), nullable=True),
        sa.Column('features', postgresql.JSONB, nullable=True),
        sa.Column('hyperparameters', postgresql.JSONB, nullable=True),
        sa.Column('status', postgresql.ENUM('STAGING', 'PRODUCTION', 'ARCHIVED', name='model_status_enum', create_constraint=True), default='STAGING', nullable=False),
        sa.Column('deployed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_by', sa.String(100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_unique_constraint('uq_model_name_version', 'ml_models', ['name', 'version'])
    
    # Ingestion Logs table
    op.create_table(
        'ingestion_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('source', sa.String(100), nullable=False, index=True),
        sa.Column('dataset', sa.String(100), nullable=False),
        sa.Column('status', postgresql.ENUM('STARTED', 'SUCCESS', 'FAILED', 'PARTIAL', name='ingestion_status_enum', create_constraint=True), nullable=False),
        sa.Column('records_processed', sa.Integer, default=0, nullable=False),
        sa.Column('records_inserted', sa.Integer, default=0, nullable=False),
        sa.Column('records_updated', sa.Integer, default=0, nullable=False),
        sa.Column('records_failed', sa.Integer, default=0, nullable=False),
        sa.Column('error_message', sa.Text, nullable=True),
        sa.Column('started_at', sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata', postgresql.JSONB, default={}, nullable=False),
    )
    op.create_index('idx_ingestion_logs_source_date', 'ingestion_logs', ['source', 'started_at'])
    
    # Users table
    op.create_table(
        'users',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('email', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('username', sa.String(100), nullable=False, unique=True, index=True),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(200), nullable=True),
        sa.Column('role', postgresql.ENUM('ADMIN', 'ANALYST', 'VIEWER', name='user_role_enum', create_constraint=True), default='VIEWER', nullable=False),
        sa.Column('is_active', sa.Boolean, default=True, nullable=False),
        sa.Column('is_superuser', sa.Boolean, default=False, nullable=False),
        sa.Column('last_login', sa.DateTime(timezone=True), nullable=True),
        sa.Column('metadata', postgresql.JSONB, default={}, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    
    # Refresh Tokens table
    op.create_table(
        'refresh_tokens',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=sa.text('uuid_generate_v4()')),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False, index=True),
        sa.Column('token_hash', sa.String(255), nullable=False, index=True),
        sa.Column('expires_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('revoked', sa.Boolean, default=False, nullable=False),
        sa.Column('user_agent', sa.String(500), nullable=True),
        sa.Column('ip_address', sa.String(45), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )
    op.create_index('idx_refresh_token_user_expires', 'refresh_tokens', ['user_id', 'expires_at'])
    
    # User-State Permissions table
    op.create_table(
        'user_state_permissions',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('state_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('states.id', ondelete='CASCADE'), primary_key=True),
        sa.Column('role', postgresql.ENUM('ADMIN', 'ANALYST', 'VIEWER', name='user_role_enum_perm', create_constraint=True), default='VIEWER', nullable=False),
    )
    
    # Materialized Views
    op.execute("""
        CREATE MATERIALIZED VIEW current_red_zones AS
        SELECT DISTINCT ON (hz.hazard_type, hz.geom)
            hz.id, hz.hazard_type, hz.severity, hz.severity_score,
            hz.geom, hz.valid_from, hz.source, hz.confidence_score,
            hz.metadata
        FROM hazard_zones hz
        WHERE hz.valid_to IS NULL OR hz.valid_to > NOW()
          AND hz.severity IN ('HIGH', 'VERY_HIGH')
        ORDER BY hz.hazard_type, hz.geom, hz.valid_from DESC;
    """)
    op.execute("CREATE UNIQUE INDEX idx_current_red_zones_unique ON current_red_zones (hazard_type, geom);")
    op.execute("CREATE INDEX idx_current_red_zones_geom ON current_red_zones USING GIST (geom);")
    
    op.execute("""
        CREATE MATERIALIZED VIEW habitation_hazard_exposure AS
        SELECT 
            h.id AS habitation_id,
            h.name AS habitation_name,
            h.district_id,
            h.geom,
            h.composite_vulnerability,
            hz.hazard_type,
            hz.severity,
            hz.severity_score,
            ST_Distance(h.geom::geography, hz.geom::geography) AS distance_m
        FROM habitations h
        JOIN current_red_zones hz ON ST_Intersects(h.geom, hz.geom)
        WHERE h.composite_vulnerability IS NOT NULL;
    """)
    op.execute("CREATE INDEX idx_habitation_exposure_habitation ON habitation_hazard_exposure (habitation_id);")
    op.execute("CREATE INDEX idx_habitation_exposure_type ON habitation_hazard_exposure (hazard_type);")
    
    op.execute("""
        CREATE MATERIALIZED VIEW site_capacity_summary AS
        SELECT 
            s.id AS site_id,
            s.name AS site_name,
            s.district_id,
            s.geom,
            s.max_carrying_capacity,
            s.recommended_capacity,
            s.current_population,
            (s.recommended_capacity - s.current_population) AS available_capacity,
            s.composite_suitability_score,
            COUNT(DISTINCT rp.habitation_id) AS assigned_habitations,
            COALESCE(SUM(hab.population), 0) AS assigned_population
        FROM relocation_sites s
        LEFT JOIN relocation_priorities rp ON rp.recommended_site_id = s.id AND rp.status IN ('PENDING', 'IN_PROGRESS')
        LEFT JOIN habitations hab ON hab.id = rp.habitation_id
        GROUP BY s.id;
    """)
    op.execute("CREATE INDEX idx_site_capacity_summary_district ON site_capacity_summary (district_id);")
    
    # Trigger function for updated_at
    op.execute("""
        CREATE OR REPLACE FUNCTION update_updated_at_column()
        RETURNS TRIGGER AS $$
        BEGIN
            NEW.updated_at = NOW();
            RETURN NEW;
        END;
        $$ language 'plpgsql';
    """)
    
    # Apply triggers to tables with updated_at
    for table in ['states', 'districts', 'habitations', 'relocation_sites', 'relocation_priorities', 'ml_models', 'ingestion_logs', 'users', 'refresh_tokens']:
        op.execute(f"""
            CREATE TRIGGER update_{table}_updated_at
            BEFORE UPDATE ON {table}
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        """)


def downgrade() -> None:
    # Drop triggers
    for table in ['states', 'districts', 'habitations', 'relocation_sites', 'relocation_priorities', 'ml_models', 'ingestion_logs', 'users', 'refresh_tokens']:
        op.execute(f"DROP TRIGGER IF EXISTS update_{table}_updated_at ON {table};")
    
    op.execute("DROP FUNCTION IF EXISTS update_updated_at_column();")
    
    # Drop materialized views
    op.execute("DROP MATERIALIZED VIEW IF EXISTS site_capacity_summary;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS habitation_hazard_exposure;")
    op.execute("DROP MATERIALIZED VIEW IF EXISTS current_red_zones;")
    
    # Drop tables in reverse order
    op.drop_table('user_state_permissions')
    op.drop_table('refresh_tokens')
    op.drop_table('users')
    op.drop_table('ingestion_logs')
    op.drop_table('ml_models')
    op.drop_table('relocation_priorities')
    op.drop_table('relocation_sites')
    op.drop_table('disaster_events')
    op.drop_table('hazard_zones')
    op.drop_table('habitations')
    op.drop_table('districts')
    op.drop_table('states')
    
    # Drop enums
    op.execute("DROP TYPE IF EXISTS ingestion_status_enum;")
    op.execute("DROP TYPE IF EXISTS model_status_enum;")
    op.execute("DROP TYPE IF EXISTS relocation_status_enum;")
    op.execute("DROP TYPE IF EXISTS priority_tier_enum;")
    op.execute("DROP TYPE IF EXISTS severity_level_enum;")
    op.execute("DROP TYPE IF EXISTS hazard_type_enum;")
    op.execute("DROP TYPE IF EXISTS user_role_enum;")
    op.execute("DROP TYPE IF EXISTS user_role_enum_perm;")
    op.execute("DROP TYPE IF EXISTS hazard_type_enum_disaster;")
    op.execute("DROP TYPE IF EXISTS hazard_type_enum_model;")
    
    # Drop extensions
    op.execute('DROP EXTENSION IF EXISTS postgis_topology;')
    op.execute('DROP EXTENSION IF EXISTS "uuid-ossp";')
    op.execute('DROP EXTENSION IF EXISTS postgis;')