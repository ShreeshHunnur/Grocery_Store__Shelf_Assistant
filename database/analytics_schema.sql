-- Analytics Database Schema for ShelfSense AI
-- Comprehensive tracking of user queries, performance, and usage patterns

-- Query tracking table - stores every user query
CREATE TABLE IF NOT EXISTS query_analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    query_text TEXT NOT NULL,
    query_type TEXT NOT NULL, -- 'location', 'information', 'general'
    input_method TEXT NOT NULL, -- 'voice', 'text', 'vision'
    response_time_ms INTEGER NOT NULL,
    confidence_score REAL,
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    user_agent TEXT,
    ip_address TEXT
);

-- Product search tracking
CREATE TABLE IF NOT EXISTS product_searches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_id INTEGER REFERENCES query_analytics(id),
    normalized_product TEXT NOT NULL,
    original_product TEXT NOT NULL,
    found BOOLEAN DEFAULT FALSE,
    match_count INTEGER DEFAULT 0,
    best_match_confidence REAL,
    disambiguation_needed BOOLEAN DEFAULT FALSE,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Location queries tracking
CREATE TABLE IF NOT EXISTS location_queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_id INTEGER REFERENCES query_analytics(id),
    product_name TEXT NOT NULL,
    aisle TEXT,
    bay TEXT,
    shelf TEXT,
    confidence REAL,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Information queries tracking
CREATE TABLE IF NOT EXISTS information_queries (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_id INTEGER REFERENCES query_analytics(id),
    product_name TEXT NOT NULL,
    info_type TEXT NOT NULL, -- 'ingredients', 'nutrition', 'price', 'allergens', etc.
    found BOOLEAN DEFAULT FALSE,
    response_length INTEGER,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Session tracking
CREATE TABLE IF NOT EXISTS session_analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT UNIQUE NOT NULL,
    start_time DATETIME DEFAULT CURRENT_TIMESTAMP,
    end_time DATETIME,
    total_queries INTEGER DEFAULT 0,
    voice_queries INTEGER DEFAULT 0,
    text_queries INTEGER DEFAULT 0,
    vision_queries INTEGER DEFAULT 0,
    successful_queries INTEGER DEFAULT 0,
    average_response_time REAL,
    user_agent TEXT,
    ip_address TEXT
);

-- Performance metrics
CREATE TABLE IF NOT EXISTS performance_metrics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    metric_name TEXT NOT NULL,
    metric_value REAL NOT NULL,
    unit TEXT, -- 'ms', 'count', 'percentage', etc.
    category TEXT -- 'response_time', 'accuracy', 'system', etc.
);

-- Popular search terms
CREATE TABLE IF NOT EXISTS search_trends (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    search_term TEXT NOT NULL,
    search_count INTEGER DEFAULT 1,
    last_searched DATETIME DEFAULT CURRENT_TIMESTAMP,
    category TEXT, -- 'product', 'location', 'information'
    UNIQUE(search_term, category)
);

-- Error tracking
CREATE TABLE IF NOT EXISTS error_analytics (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
    error_type TEXT NOT NULL,
    error_message TEXT,
    query_text TEXT,
    input_method TEXT,
    session_id TEXT,
    stack_trace TEXT
);

-- User feedback (for future enhancement)
CREATE TABLE IF NOT EXISTS user_feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    query_id INTEGER REFERENCES query_analytics(id),
    rating INTEGER CHECK(rating >= 1 AND rating <= 5),
    feedback_text TEXT,
    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_query_analytics_timestamp ON query_analytics(timestamp);
CREATE INDEX IF NOT EXISTS idx_query_analytics_session ON query_analytics(session_id);
CREATE INDEX IF NOT EXISTS idx_query_analytics_type ON query_analytics(query_type);
CREATE INDEX IF NOT EXISTS idx_product_searches_product ON product_searches(normalized_product);
CREATE INDEX IF NOT EXISTS idx_location_queries_product ON location_queries(product_name);
CREATE INDEX IF NOT EXISTS idx_session_analytics_start ON session_analytics(start_time);
CREATE INDEX IF NOT EXISTS idx_performance_metrics_timestamp ON performance_metrics(timestamp);
CREATE INDEX IF NOT EXISTS idx_search_trends_term ON search_trends(search_term);

-- Views for common analytics queries
CREATE VIEW IF NOT EXISTS daily_query_stats AS
SELECT 
    DATE(timestamp) as date,
    COUNT(*) as total_queries,
    COUNT(CASE WHEN input_method = 'voice' THEN 1 END) as voice_queries,
    COUNT(CASE WHEN input_method = 'text' THEN 1 END) as text_queries,
    COUNT(CASE WHEN input_method = 'vision' THEN 1 END) as vision_queries,
    COUNT(CASE WHEN success = 1 THEN 1 END) as successful_queries,
    AVG(response_time_ms) as avg_response_time,
    AVG(confidence_score) as avg_confidence
FROM query_analytics 
GROUP BY DATE(timestamp)
ORDER BY date DESC;

CREATE VIEW IF NOT EXISTS popular_products AS
SELECT 
    normalized_product,
    COUNT(*) as search_count,
    AVG(best_match_confidence) as avg_confidence,
    MAX(timestamp) as last_searched,
    COUNT(CASE WHEN found = 1 THEN 1 END) as found_count
FROM product_searches 
GROUP BY normalized_product
ORDER BY search_count DESC;

CREATE VIEW IF NOT EXISTS busiest_locations AS
SELECT 
    COALESCE(aisle, 'Unknown') as aisle,
    COALESCE(bay, 'Unknown') as bay,
    COUNT(*) as query_count,
    AVG(confidence) as avg_confidence
FROM location_queries 
WHERE aisle IS NOT NULL OR bay IS NOT NULL
GROUP BY aisle, bay
ORDER BY query_count DESC;

CREATE VIEW IF NOT EXISTS query_type_distribution AS
SELECT 
    query_type,
    COUNT(*) as count,
    ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM query_analytics), 2) as percentage,
    AVG(response_time_ms) as avg_response_time,
    AVG(confidence_score) as avg_confidence
FROM query_analytics 
GROUP BY query_type
ORDER BY count DESC;