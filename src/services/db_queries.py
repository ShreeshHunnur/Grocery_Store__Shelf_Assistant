"""
Database query functions for the Retail Shelf Assistant.
Provides functions for product location search, synonym matching, and name normalization.
"""
import sqlite3
import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
import logging

logger = logging.getLogger(__name__)

@dataclass
class ProductMatch:
    """Represents a product match with location and confidence data."""
    product_id: str
    product_name: str
    brand: str
    category: str
    aisle: str
    bay: str
    shelf: str
    confidence: float
    synonyms: List[str] = None
    keywords: List[str] = None

class DatabaseService:
    """Service class for database operations."""
    
    def __init__(self, db_path: str):
        """Initialize with database path."""
        self.db_path = db_path
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection with row factory."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def normalize_product_name(self, query: str) -> str:
        """
        Normalize product name for consistent searching.
        
        Args:
            query: Raw user query
            
        Returns:
            Normalized product name
        """
        if not query:
            return ""
        
        # Convert to lowercase
        normalized = query.lower().strip()
        
        # Remove common articles and prepositions
        articles = ['the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by']
        words = normalized.split()
        words = [word for word in words if word not in articles]
        
        # Remove punctuation except hyphens and apostrophes
        words = [re.sub(r'[^\w\-\']', '', word) for word in words]
        
        # Remove empty words
        words = [word for word in words if word]
        
        return ' '.join(words)
    
    def find_product_locations(self, query: str, limit: int = 10) -> List[ProductMatch]:
        """
        Find product locations based on query.
        
        Args:
            query: Search query
            limit: Maximum number of results
            
        Returns:
            List of ProductMatch objects
        """
        if not query:
            return []
        
        normalized_query = self.normalize_product_name(query)
        if not normalized_query:
            return []
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Try exact match first
            exact_matches = self._find_exact_matches(cursor, normalized_query, limit)
            if exact_matches:
                return exact_matches
            
            # Try fuzzy matching
            fuzzy_matches = self._find_fuzzy_matches(cursor, normalized_query, limit)
            if fuzzy_matches:
                return fuzzy_matches
            
            # Try synonym matching
            synonym_matches = self._find_synonym_matches(cursor, normalized_query, limit)
            if synonym_matches:
                return synonym_matches
            
            # Try partial matching
            partial_matches = self._find_partial_matches(cursor, normalized_query, limit)
            return partial_matches
            
        finally:
            conn.close()
    
    def _find_exact_matches(self, cursor, query: str, limit: int) -> List[ProductMatch]:
        """Find exact matches for product names."""
        cursor.execute("""
            SELECT DISTINCT
                p.id as product_id,
                p.name as product_name,
                b.name as brand_name,
                c.name as category_name,
                il.aisle,
                il.bay,
                il.shelf,
                il.position,
                pp.popularity_score
            FROM products p
            JOIN brands b ON p.brand_id = b.id
            JOIN categories c ON p.category_id = c.id
            LEFT JOIN inventory_locations il ON p.id = il.product_id
            LEFT JOIN product_popularity pp ON p.id = pp.product_id
            WHERE LOWER(p.name) = ?
            ORDER BY pp.popularity_score DESC, p.name
            LIMIT ?
        """, (query, limit))
        
        return self._convert_to_matches(cursor.fetchall(), confidence=1.0)
    
    def _find_fuzzy_matches(self, cursor, query: str, limit: int) -> List[ProductMatch]:
        """Find fuzzy matches using LIKE patterns."""
        # Split query into words
        words = query.split()
        if not words:
            return []
        
        # Create LIKE patterns for each word
        like_patterns = [f"%{word}%" for word in words]
        
        # Build dynamic WHERE clause
        where_conditions = []
        params = []
        
        for pattern in like_patterns:
            where_conditions.append("LOWER(p.name) LIKE ?")
            params.append(pattern)
        
        where_clause = " AND ".join(where_conditions)
        
        cursor.execute(f"""
            SELECT DISTINCT
                p.id as product_id,
                p.name as product_name,
                b.name as brand_name,
                c.name as category_name,
                il.aisle,
                il.bay,
                il.shelf,
                il.position,
                pp.popularity_score
            FROM products p
            JOIN brands b ON p.brand_id = b.id
            JOIN categories c ON p.category_id = c.id
            LEFT JOIN inventory_locations il ON p.id = il.product_id
            LEFT JOIN product_popularity pp ON p.id = pp.product_id
            WHERE {where_clause}
            ORDER BY pp.popularity_score DESC, p.name
            LIMIT ?
        """, params + [limit])
        
        # Calculate confidence based on word matches
        results = cursor.fetchall()
        matches = []
        
        for row in results:
            confidence = self._calculate_fuzzy_confidence(query, row['product_name'])
            matches.append(self._convert_row_to_match(row, confidence))
        
        return sorted(matches, key=lambda x: x.confidence, reverse=True)[:limit]
    
    def _find_synonym_matches(self, cursor, query: str, limit: int) -> List[ProductMatch]:
        """Find matches using product synonyms."""
        cursor.execute("""
            SELECT DISTINCT
                p.id as product_id,
                p.name as product_name,
                b.name as brand_name,
                c.name as category_name,
                il.aisle,
                il.bay,
                il.shelf,
                il.position,
                pp.popularity_score,
                ps.synonym
            FROM products p
            JOIN brands b ON p.brand_id = b.id
            JOIN categories c ON p.category_id = c.id
            LEFT JOIN inventory_locations il ON p.id = il.product_id
            LEFT JOIN product_popularity pp ON p.id = pp.product_id
            JOIN product_synonyms ps ON p.id = ps.product_id
            WHERE LOWER(ps.synonym) LIKE ?
            ORDER BY pp.popularity_score DESC, p.name
            LIMIT ?
        """, (f"%{query}%", limit))
        
        results = cursor.fetchall()
        matches = []
        
        for row in results:
            confidence = self._calculate_synonym_confidence(query, row['synonym'])
            matches.append(self._convert_row_to_match(row, confidence))
        
        return sorted(matches, key=lambda x: x.confidence, reverse=True)[:limit]
    
    def _find_partial_matches(self, cursor, query: str, limit: int) -> List[ProductMatch]:
        """Find partial matches using keyword search."""
        cursor.execute("""
            SELECT DISTINCT
                p.id as product_id,
                p.name as product_name,
                b.name as brand_name,
                c.name as category_name,
                il.aisle,
                il.bay,
                il.shelf,
                il.position,
                pp.popularity_score
            FROM products p
            JOIN brands b ON p.brand_id = b.id
            JOIN categories c ON p.category_id = c.id
            LEFT JOIN inventory_locations il ON p.id = il.product_id
            LEFT JOIN product_popularity pp ON p.id = pp.product_id
            LEFT JOIN product_keywords pk ON p.id = pk.product_id
            WHERE LOWER(p.name) LIKE ? 
               OR LOWER(b.name) LIKE ?
               OR LOWER(c.name) LIKE ?
               OR LOWER(pk.keyword) LIKE ?
            ORDER BY pp.popularity_score DESC, p.name
            LIMIT ?
        """, (f"%{query}%", f"%{query}%", f"%{query}%", f"%{query}%", limit))
        
        results = cursor.fetchall()
        matches = []
        
        for row in results:
            confidence = self._calculate_partial_confidence(query, row['product_name'], row['brand_name'])
            matches.append(self._convert_row_to_match(row, confidence))
        
        return sorted(matches, key=lambda x: x.confidence, reverse=True)[:limit]
    
    def find_candidates_by_synonym(self, synonym: str, limit: int = 10) -> List[ProductMatch]:
        """
        Find product candidates by synonym.
        
        Args:
            synonym: Synonym to search for
            limit: Maximum number of results
            
        Returns:
            List of ProductMatch objects
        """
        if not synonym:
            return []
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT DISTINCT
                    p.id as product_id,
                    p.name as product_name,
                    b.name as brand_name,
                    c.name as category_name,
                    il.aisle,
                    il.bay,
                    il.shelf,
                    il.position,
                    pp.popularity_score,
                    ps.synonym
                FROM products p
                JOIN brands b ON p.brand_id = b.id
                JOIN categories c ON p.category_id = c.id
                LEFT JOIN inventory_locations il ON p.id = il.product_id
                LEFT JOIN product_popularity pp ON p.id = pp.product_id
                JOIN product_synonyms ps ON p.id = ps.product_id
                WHERE LOWER(ps.synonym) = LOWER(?)
                ORDER BY pp.popularity_score DESC, p.name
                LIMIT ?
            """, (synonym, limit))
            
            results = cursor.fetchall()
            return self._convert_to_matches(results, confidence=0.9)
            
        finally:
            conn.close()
    
    def get_product_by_id(self, product_id: str) -> Optional[ProductMatch]:
        """Get product details by ID."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT DISTINCT
                    p.id as product_id,
                    p.name as product_name,
                    b.name as brand_name,
                    c.name as category_name,
                    il.aisle,
                    il.bay,
                    il.shelf,
                    il.position,
                    pp.popularity_score
                FROM products p
                JOIN brands b ON p.brand_id = b.id
                JOIN categories c ON p.category_id = c.id
                LEFT JOIN inventory_locations il ON p.id = il.product_id
                LEFT JOIN product_popularity pp ON p.id = pp.product_id
                WHERE p.id = ?
            """, (product_id,))
            
            row = cursor.fetchone()
            if row:
                return self._convert_row_to_match(row, confidence=1.0)
            return None
            
        finally:
            conn.close()
    
    def search_products_fulltext(self, query: str, limit: int = 10) -> List[ProductMatch]:
        """Search products using full-text search."""
        if not query:
            return []
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT DISTINCT
                    p.id as product_id,
                    p.name as product_name,
                    b.name as brand_name,
                    c.name as category_name,
                    il.aisle,
                    il.bay,
                    il.shelf,
                    il.position,
                    pp.popularity_score,
                    fts.rank
                FROM products_fts fts
                JOIN products p ON fts.rowid = p.id
                JOIN brands b ON p.brand_id = b.id
                JOIN categories c ON p.category_id = c.id
                LEFT JOIN inventory_locations il ON p.id = il.product_id
                LEFT JOIN product_popularity pp ON p.id = pp.product_id
                WHERE products_fts MATCH ?
                ORDER BY fts.rank, pp.popularity_score DESC
                LIMIT ?
            """, (query, limit))
            
            results = cursor.fetchall()
            matches = []
            
            for row in results:
                # Convert rank to confidence (lower rank = higher confidence)
                # Handle case where rank might be None or invalid
                rank = row['rank'] if row['rank'] is not None else 0
                confidence = max(0.1, min(1.0, 1.0 - (rank / 100.0)))
                matches.append(self._convert_row_to_match(row, confidence))
            
            return matches
            
        finally:
            conn.close()
    
    def _calculate_fuzzy_confidence(self, query: str, product_name: str) -> float:
        """Calculate confidence score for fuzzy matches."""
        query_words = set(query.lower().split())
        product_words = set(product_name.lower().split())
        
        if not query_words or not product_words:
            return 0.0
        
        # Calculate Jaccard similarity
        intersection = len(query_words.intersection(product_words))
        union = len(query_words.union(product_words))
        
        if union == 0:
            return 0.0
        
        similarity = intersection / union
        
        # Boost confidence for exact word matches
        exact_matches = sum(1 for word in query_words if word in product_words)
        word_boost = exact_matches / len(query_words) if query_words else 0
        
        return min(1.0, similarity + word_boost * 0.3)
    
    def _calculate_synonym_confidence(self, query: str, synonym: str) -> float:
        """Calculate confidence score for synonym matches."""
        if query.lower() == synonym.lower():
            return 0.9
        elif query.lower() in synonym.lower():
            return 0.7
        elif synonym.lower() in query.lower():
            return 0.6
        else:
            return 0.5
    
    def _calculate_partial_confidence(self, query: str, product_name: str, brand_name: str) -> float:
        """Calculate confidence score for partial matches."""
        query_lower = query.lower()
        product_lower = product_name.lower()
        brand_lower = brand_name.lower()
        
        confidence = 0.0
        
        # Check product name match
        if query_lower in product_lower:
            confidence += 0.6
        
        # Check brand name match
        if query_lower in brand_lower:
            confidence += 0.3
        
        # Check word overlap
        query_words = set(query_lower.split())
        product_words = set(product_lower.split())
        brand_words = set(brand_lower.split())
        
        all_words = product_words.union(brand_words)
        if query_words and all_words:
            overlap = len(query_words.intersection(all_words))
            confidence += (overlap / len(query_words)) * 0.4
        
        return min(1.0, confidence)
    
    def _convert_to_matches(self, rows: List[sqlite3.Row], confidence: float) -> List[ProductMatch]:
        """Convert database rows to ProductMatch objects."""
        matches = []
        for row in rows:
            matches.append(self._convert_row_to_match(row, confidence))
        return matches
    
    def _convert_row_to_match(self, row: sqlite3.Row, confidence: float) -> ProductMatch:
        """Convert a database row to a ProductMatch object."""
        return ProductMatch(
            product_id=str(row['product_id']),
            product_name=row['product_name'],
            brand=row['brand_name'],
            category=row['category_name'],
            aisle=row['aisle'] or 'Unknown',
            bay=row['bay'] or 'Unknown',
            shelf=row['shelf'] or 'Unknown',
            confidence=confidence,
            synonyms=[],
            keywords=[]
        )
    
    def get_database_stats(self) -> Dict[str, int]:
        """Get database statistics."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            stats = {}
            
            # Count products
            cursor.execute("SELECT COUNT(*) FROM products")
            stats['products'] = cursor.fetchone()[0]
            
            # Count categories
            cursor.execute("SELECT COUNT(*) FROM categories")
            stats['categories'] = cursor.fetchone()[0]
            
            # Count brands
            cursor.execute("SELECT COUNT(*) FROM brands")
            stats['brands'] = cursor.fetchone()[0]
            
            # Count synonyms
            cursor.execute("SELECT COUNT(*) FROM product_synonyms")
            stats['synonyms'] = cursor.fetchone()[0]
            
            # Count keywords
            cursor.execute("SELECT COUNT(*) FROM product_keywords")
            stats['keywords'] = cursor.fetchone()[0]
            
            return stats
            
        finally:
            conn.close()

# Convenience functions for direct use
def find_product_locations(db_path: str, query: str, limit: int = 10) -> List[ProductMatch]:
    """Find product locations using the database service."""
    service = DatabaseService(db_path)
    return service.find_product_locations(query, limit)

def find_candidates_by_synonym(db_path: str, synonym: str, limit: int = 10) -> List[ProductMatch]:
    """Find product candidates by synonym using the database service."""
    service = DatabaseService(db_path)
    return service.find_candidates_by_synonym(synonym, limit)

def normalize_product_name(query: str) -> str:
    """Normalize product name for consistent searching."""
    service = DatabaseService("")  # Empty path since we only need the normalization
    return service.normalize_product_name(query)
