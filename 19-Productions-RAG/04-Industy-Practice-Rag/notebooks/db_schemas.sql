-- Documents table — one row per uploaded file
CREATE TABLE documents (
    id          UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    filename    TEXT NOT NULL,
    file_type   TEXT NOT NULL,
    status      TEXT NOT NULL DEFAULT 'pending',
    created_at  TIMESTAMPTZ DEFAULT now()
);

-- Chunks table — one row per chunk, with vector + metadata
CREATE TABLE chunks (
    id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id    UUID REFERENCES documents(id) ON DELETE CASCADE,
    content        TEXT NOT NULL,
    parent_content TEXT,
    embedding      vector(1024),
    metadata       JSONB NOT NULL DEFAULT '{}',
    created_at     TIMESTAMPTZ DEFAULT now()
);

-- HNSW index for fast cosine similarity search
-- Create this AFTER bulk loading data in production
-- Fine to create now for practice
CREATE INDEX idx_chunks_embedding
    ON chunks
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- GIN index so metadata filtering is fast
CREATE INDEX idx_chunks_metadata
    ON chunks USING gin(metadata);

-- Verify tables exist
\dt