-- Enable the pgvector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create users table for Clerk integration
CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    clerk_user_id TEXT UNIQUE NOT NULL,
    email TEXT,
    first_name TEXT,
    last_name TEXT,
    image_url TEXT,
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create documents table with user isolation
CREATE TABLE IF NOT EXISTS documents (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    filename TEXT NOT NULL,
    file_type TEXT NOT NULL,
    file_size BIGINT,
    content_hash TEXT,
    metadata JSONB DEFAULT '{}',
    status TEXT DEFAULT 'processing' CHECK (status IN ('processing', 'ready', 'error')),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create document_chunks table with vector embeddings
CREATE TABLE IF NOT EXISTS document_chunks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    document_id UUID NOT NULL REFERENCES documents(id) ON DELETE CASCADE,
    user_id UUID NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    chunk_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    embedding vector(384), -- sentence-transformers/all-MiniLM-L6-v2 dimension
    metadata JSONB DEFAULT '{}',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_documents_user_id ON documents(user_id);
CREATE INDEX IF NOT EXISTS idx_documents_status ON documents(status);
CREATE INDEX IF NOT EXISTS idx_document_chunks_document_id ON document_chunks(document_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_user_id ON document_chunks(user_id);

-- Create vector similarity search index
CREATE INDEX IF NOT EXISTS idx_document_chunks_embedding ON document_chunks 
USING ivfflat (embedding vector_cosine_ops) WITH (lists = 100);

-- Enable Row Level Security (RLS)
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;
ALTER TABLE document_chunks ENABLE ROW LEVEL SECURITY;

-- RLS Policies for users table
CREATE POLICY "Users can view own profile" ON users
    FOR SELECT USING (clerk_user_id = current_setting('app.current_user_id', true));

CREATE POLICY "Users can update own profile" ON users
    FOR UPDATE USING (clerk_user_id = current_setting('app.current_user_id', true));

-- RLS Policies for documents table
CREATE POLICY "Users can view own documents" ON documents
    FOR SELECT USING (user_id IN (
        SELECT id FROM users WHERE clerk_user_id = current_setting('app.current_user_id', true)
    ));

CREATE POLICY "Users can insert own documents" ON documents
    FOR INSERT WITH CHECK (user_id IN (
        SELECT id FROM users WHERE clerk_user_id = current_setting('app.current_user_id', true)
    ));

CREATE POLICY "Users can update own documents" ON documents
    FOR UPDATE USING (user_id IN (
        SELECT id FROM users WHERE clerk_user_id = current_setting('app.current_user_id', true)
    ));

CREATE POLICY "Users can delete own documents" ON documents
    FOR DELETE USING (user_id IN (
        SELECT id FROM users WHERE clerk_user_id = current_setting('app.current_user_id', true)
    ));

-- RLS Policies for document_chunks table
CREATE POLICY "Users can view own chunks" ON document_chunks
    FOR SELECT USING (user_id IN (
        SELECT id FROM users WHERE clerk_user_id = current_setting('app.current_user_id', true)
    ));

CREATE POLICY "Users can insert own chunks" ON document_chunks
    FOR INSERT WITH CHECK (user_id IN (
        SELECT id FROM users WHERE clerk_user_id = current_setting('app.current_user_id', true)
    ));

CREATE POLICY "Users can delete own chunks" ON document_chunks
    FOR DELETE USING (user_id IN (
        SELECT id FROM users WHERE clerk_user_id = current_setting('app.current_user_id', true)
    ));

-- Function to search similar documents
CREATE OR REPLACE FUNCTION search_documents(
    query_embedding vector(384),
    match_threshold float DEFAULT 0.7,
    match_count int DEFAULT 10,
    filter_user_id uuid DEFAULT NULL
)
RETURNS TABLE (
    id uuid,
    document_id uuid,
    content text,
    metadata jsonb,
    similarity float
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        dc.id,
        dc.document_id,
        dc.content,
        dc.metadata,
        1 - (dc.embedding <=> query_embedding) AS similarity
    FROM document_chunks dc
    WHERE 
        (filter_user_id IS NULL OR dc.user_id = filter_user_id)
        AND 1 - (dc.embedding <=> query_embedding) > match_threshold
    ORDER BY dc.embedding <=> query_embedding
    LIMIT match_count;
END;
$$;

-- Function to get document statistics
CREATE OR REPLACE FUNCTION get_user_document_stats(user_uuid uuid)
RETURNS TABLE (
    total_documents bigint,
    total_chunks bigint,
    total_size bigint,
    ready_documents bigint,
    processing_documents bigint
)
LANGUAGE plpgsql
AS $$
BEGIN
    RETURN QUERY
    SELECT
        COUNT(d.id) as total_documents,
        COUNT(dc.id) as total_chunks,
        COALESCE(SUM(d.file_size), 0) as total_size,
        COUNT(d.id) FILTER (WHERE d.status = 'ready') as ready_documents,
        COUNT(d.id) FILTER (WHERE d.status = 'processing') as processing_documents
    FROM documents d
    LEFT JOIN document_chunks dc ON d.id = dc.document_id
    WHERE d.user_id = user_uuid;
END;
$$;