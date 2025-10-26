-- Retail Shelf Assistant Database Schema
-- SQLite3 database for product catalog with location data

-- Categories table
CREATE TABLE IF NOT EXISTS categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    parent_category_id INTEGER,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (parent_category_id) REFERENCES categories(id)
);

-- Brands table
CREATE TABLE IF NOT EXISTS brands (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    description TEXT,
    country_of_origin TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Products table
CREATE TABLE IF NOT EXISTS products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    brand_id INTEGER NOT NULL,
    category_id INTEGER NOT NULL,
    description TEXT,
    barcode TEXT UNIQUE,
    size TEXT,
    weight TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (brand_id) REFERENCES brands(id),
    FOREIGN KEY (category_id) REFERENCES categories(id)
);

-- Inventory locations table
CREATE TABLE IF NOT EXISTS inventory_locations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    aisle TEXT NOT NULL,
    bay TEXT NOT NULL,
    shelf TEXT NOT NULL,
    position TEXT, -- e.g., "left", "center", "right"
    stock_level INTEGER DEFAULT 0,
    last_updated DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- Product synonyms table for alternative names and search terms
CREATE TABLE IF NOT EXISTS product_synonyms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    synonym TEXT NOT NULL,
    synonym_type TEXT DEFAULT 'alternative_name', -- 'alternative_name', 'nickname', 'search_term'
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- Product keywords for enhanced search
CREATE TABLE IF NOT EXISTS product_keywords (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    keyword TEXT NOT NULL,
    keyword_type TEXT DEFAULT 'feature', -- 'feature', 'ingredient', 'dietary', 'usage'
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- Popularity/trending data
CREATE TABLE IF NOT EXISTS product_popularity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER NOT NULL,
    search_count INTEGER DEFAULT 0,
    last_searched DATETIME,
    popularity_score REAL DEFAULT 0.0,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- Create indices for performance
CREATE INDEX IF NOT EXISTS idx_products_name ON products(name);
CREATE INDEX IF NOT EXISTS idx_products_brand ON products(brand_id);
CREATE INDEX IF NOT EXISTS idx_products_category ON products(category_id);
CREATE INDEX IF NOT EXISTS idx_products_barcode ON products(barcode);

CREATE INDEX IF NOT EXISTS idx_inventory_aisle ON inventory_locations(aisle);
CREATE INDEX IF NOT EXISTS idx_inventory_bay ON inventory_locations(bay);
CREATE INDEX IF NOT EXISTS idx_inventory_shelf ON inventory_locations(shelf);
CREATE INDEX IF NOT EXISTS idx_inventory_product ON inventory_locations(product_id);

CREATE INDEX IF NOT EXISTS idx_synonyms_text ON product_synonyms(synonym);
CREATE INDEX IF NOT EXISTS idx_synonyms_product ON product_synonyms(product_id);
CREATE INDEX IF NOT EXISTS idx_synonyms_type ON product_synonyms(synonym_type);

CREATE INDEX IF NOT EXISTS idx_keywords_text ON product_keywords(keyword);
CREATE INDEX IF NOT EXISTS idx_keywords_product ON product_keywords(product_id);
CREATE INDEX IF NOT EXISTS idx_keywords_type ON product_keywords(keyword_type);

CREATE INDEX IF NOT EXISTS idx_popularity_score ON product_popularity(popularity_score);
CREATE INDEX IF NOT EXISTS idx_popularity_product ON product_popularity(product_id);

-- Mapping table for FAISS index ids to product ids
CREATE TABLE IF NOT EXISTS faiss_mapping (
    faiss_idx INTEGER PRIMARY KEY,
    product_id INTEGER NOT NULL UNIQUE,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products(id) ON DELETE CASCADE
);

-- Full-text search indices (SQLite FTS5)
CREATE VIRTUAL TABLE IF NOT EXISTS products_fts USING fts5(
    product_name,
    brand_name,
    category_name,
    synonyms,
    keywords
);

-- View for product search with location data
CREATE VIEW IF NOT EXISTS product_search_view AS
SELECT 
    p.id as product_id,
    p.name as product_name,
    b.name as brand_name,
    c.name as category_name,
    il.aisle,
    il.bay,
    il.shelf,
    il.position,
    il.stock_level,
    pp.popularity_score,
    GROUP_CONCAT(DISTINCT ps.synonym, '|') as synonyms,
    GROUP_CONCAT(DISTINCT pk.keyword, '|') as keywords
FROM products p
JOIN brands b ON p.brand_id = b.id
JOIN categories c ON p.category_id = c.id
LEFT JOIN inventory_locations il ON p.id = il.product_id
LEFT JOIN product_popularity pp ON p.id = pp.product_id
LEFT JOIN product_synonyms ps ON p.id = ps.product_id
LEFT JOIN product_keywords pk ON p.id = pk.product_id
GROUP BY p.id, il.id;

-- View for fuzzy search candidates
CREATE VIEW IF NOT EXISTS search_candidates AS
SELECT 
    p.id as product_id,
    p.name as product_name,
    b.name as brand_name,
    c.name as category_name,
    il.aisle,
    il.bay,
    il.shelf,
    il.position,
    pp.popularity_score,
    ps.synonym,
    pk.keyword
FROM products p
JOIN brands b ON p.brand_id = b.id
JOIN categories c ON p.category_id = c.id
LEFT JOIN inventory_locations il ON p.id = il.product_id
LEFT JOIN product_popularity pp ON p.id = pp.product_id
LEFT JOIN product_synonyms ps ON p.id = ps.product_id
LEFT JOIN product_keywords pk ON p.id = pk.product_id;

-- Triggers for maintaining FTS index
CREATE TRIGGER IF NOT EXISTS products_ai AFTER INSERT ON products BEGIN
    INSERT INTO products_fts(
        product_name, brand_name, category_name, synonyms, keywords
    ) VALUES (
        NEW.name,
        (SELECT name FROM brands WHERE id = NEW.brand_id),
        (SELECT name FROM categories WHERE id = NEW.category_id),
        '',
        ''
    );
END;

CREATE TRIGGER IF NOT EXISTS products_ad AFTER DELETE ON products BEGIN
    DELETE FROM products_fts WHERE rowid = OLD.id;
END;

CREATE TRIGGER IF NOT EXISTS products_au AFTER UPDATE ON products BEGIN
    UPDATE products_fts SET
        product_name = NEW.name,
        brand_name = (SELECT name FROM brands WHERE id = NEW.brand_id),
        category_name = (SELECT name FROM categories WHERE id = NEW.category_id)
    WHERE rowid = OLD.id;
END;

-- Trigger to update synonyms in FTS
CREATE TRIGGER IF NOT EXISTS synonyms_ai AFTER INSERT ON product_synonyms BEGIN
    UPDATE products_fts SET
        synonyms = (
            SELECT GROUP_CONCAT(synonym, ' ')
            FROM product_synonyms 
            WHERE product_id = NEW.product_id
        )
    WHERE rowid = NEW.product_id;
END;

-- Trigger to update keywords in FTS
CREATE TRIGGER IF NOT EXISTS keywords_ai AFTER INSERT ON product_keywords BEGIN
    UPDATE products_fts SET
        keywords = (
            SELECT GROUP_CONCAT(keyword, ' ')
            FROM product_keywords 
            WHERE product_id = NEW.product_id
        )
    WHERE rowid = NEW.product_id;
END;
