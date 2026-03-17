-- Supabase 数据库初始化脚本
-- 在 Supabase SQL 编辑器中执行此脚本

-- 创建分析记录表
CREATE TABLE IF NOT EXISTS analyses (
    id BIGSERIAL PRIMARY KEY,
    sql_text TEXT NOT NULL,
    analysis_result JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 创建反馈表
CREATE TABLE IF NOT EXISTS feedbacks (
    id BIGSERIAL PRIMARY KEY,
    analysis_id BIGINT REFERENCES analyses(id),
    feedback TEXT NOT NULL,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- 启用 Row Level Security
ALTER TABLE analyses ENABLE ROW LEVEL SECURITY;
ALTER TABLE feedbacks ENABLE ROW LEVEL SECURITY;

-- 创建允许读取的策略（匿名用户可读）
CREATE POLICY "Allow anonymous read analyses" ON analyses
    FOR SELECT TO anon
    USING (true);

CREATE POLICY "Allow anonymous read feedbacks" ON feedbacks
    FOR SELECT TO anon
    USING (true);

-- 创建允许插入的策略（匿名用户可写入）
CREATE POLICY "Allow anonymous insert analyses" ON analyses
    FOR INSERT TO anon
    WITH CHECK (true);

CREATE POLICY "Allow anonymous insert feedbacks" ON feedbacks
    FOR INSERT TO anon
    WITH CHECK (true);

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_analyses_created_at ON analyses(created_at DESC);

-- 启用 pgvector 扩展（如果需要向量搜索功能）
-- CREATE EXTENSION IF NOT EXISTS vector;

-- 创建历史分析视图（可选）
CREATE OR REPLACE VIEW recent_analyses AS
SELECT
    id,
    sql_text,
    created_at,
    (analysis_result->>'summary') as summary
FROM analyses
ORDER BY created_at DESC
LIMIT 50;
