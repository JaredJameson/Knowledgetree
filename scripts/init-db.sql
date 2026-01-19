-- KnowledgeTree Database Initialization Script
-- PostgreSQL 16 + pgvector 0.7

-- Enable pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Verify extension is loaded
SELECT * FROM pg_extension WHERE extname = 'vector';

-- Create UUID extension (for generating UUIDs)
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Set timezone
SET timezone = 'UTC';

-- Create database user (if not exists)
-- Note: This is handled by POSTGRES_USER in docker-compose.yml

-- Grant permissions
GRANT ALL PRIVILEGES ON DATABASE knowledgetree TO knowledgetree;

-- Success message
DO $$
BEGIN
  RAISE NOTICE 'KnowledgeTree database initialized successfully!';
  RAISE NOTICE 'pgvector extension: ENABLED';
  RAISE NOTICE 'uuid-ossp extension: ENABLED';
END $$;
