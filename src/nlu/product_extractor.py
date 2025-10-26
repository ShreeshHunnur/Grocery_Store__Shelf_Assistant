"""
Product extractor using synonyms table and trigram similarity.
Extracts product names from text using database synonyms and fuzzy matching.
"""
import re
import sqlite3
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass
from difflib import SequenceMatcher

@dataclass
class ProductCandidate:
    """Represents a potential product match."""
    product_id: str
    product_name: str
    brand: str
    category: str
    confidence: float
    match_type: str  # 'exact', 'synonym', 'fuzzy', 'trigram'
    matched_text: str
    synonyms: List[str] = None

class ProductExtractor:
    """Extracts product names from text using various matching strategies."""
    
    def __init__(self, db_path: str):
        """Initialize with database path."""
        self.db_path = db_path
        self._synonym_cache = {}
        self._product_cache = {}
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection."""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def _load_synonyms(self) -> Dict[str, List[Tuple[str, str, str]]]:
        """Load synonyms from database with caching."""
        if self._synonym_cache:
            return self._synonym_cache
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT ps.synonym, p.id, p.name, b.name as brand_name
                FROM product_synonyms ps
                JOIN products p ON ps.product_id = p.id
                JOIN brands b ON p.brand_id = b.id
            """)
            
            synonyms = {}
            for row in cursor.fetchall():
                synonym = row[0].lower()
                if synonym not in synonyms:
                    synonyms[synonym] = []
                synonyms[synonym].append((row[1], row[2], row[3]))
            
            self._synonym_cache = synonyms
            return synonyms
            
        finally:
            conn.close()
    
    def _load_products(self) -> List[Tuple[str, str, str, str]]:
        """Load all products from database with caching."""
        if self._product_cache:
            return self._product_cache
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT p.id, p.name, b.name as brand_name, c.name as category_name
                FROM products p
                JOIN brands b ON p.brand_id = b.id
                JOIN categories c ON p.category_id = c.id
            """)
            
            products = []
            for row in cursor.fetchall():
                products.append((row[0], row[1], row[2], row[3]))
            
            self._product_cache = products
            return products
            
        finally:
            conn.close()
    
    def _normalize_text(self, text: str) -> str:
        """Normalize text for matching."""
        # Convert to lowercase
        normalized = text.lower().strip()
        
        # Remove punctuation except hyphens and apostrophes
        normalized = re.sub(r'[^\w\s\-\']', ' ', normalized)
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Strip final whitespace
        normalized = normalized.strip()
        
        return normalized
    
    def _calculate_trigram_similarity(self, text1: str, text2: str) -> float:
        """Calculate trigram similarity between two texts."""
        def get_trigrams(text: str) -> set:
            """Get trigrams from text."""
            text = text.lower().replace(' ', '')
            if len(text) < 3:
                return set()
            return set(text[i:i+3] for i in range(len(text) - 2))
        
        trigrams1 = get_trigrams(text1)
        trigrams2 = get_trigrams(text2)
        
        if not trigrams1 or not trigrams2:
            return 0.0
        
        intersection = len(trigrams1.intersection(trigrams2))
        union = len(trigrams1.union(trigrams2))
        
        return intersection / union if union > 0 else 0.0
    
    def _calculate_fuzzy_similarity(self, text1: str, text2: str) -> float:
        """Calculate fuzzy similarity using SequenceMatcher."""
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
    
    def extract_products(self, text: str, limit: int = 5) -> List[ProductCandidate]:
        """
        Extract product candidates from text.
        
        Args:
            text: Input text to extract products from
            limit: Maximum number of candidates to return
            
        Returns:
            List of ProductCandidate objects sorted by confidence
        """
        if not text or not text.strip():
            return []
        
        normalized_text = self._normalize_text(text)
        candidates = []
        
        # Strategy 1: Exact synonym matching
        exact_matches = self._find_exact_synonym_matches(normalized_text)
        candidates.extend(exact_matches)
        
        # Strategy 2: Fuzzy synonym matching
        fuzzy_matches = self._find_fuzzy_synonym_matches(normalized_text)
        candidates.extend(fuzzy_matches)
        
        # Strategy 3: Direct product name matching
        product_matches = self._find_product_name_matches(normalized_text)
        candidates.extend(product_matches)
        
        # Strategy 4: Trigram similarity matching
        trigram_matches = self._find_trigram_matches(normalized_text)
        candidates.extend(trigram_matches)
        
        # Remove duplicates and sort by confidence
        unique_candidates = self._deduplicate_candidates(candidates)
        sorted_candidates = sorted(unique_candidates, key=lambda x: x.confidence, reverse=True)
        
        return sorted_candidates[:limit]
    
    def _find_exact_synonym_matches(self, text: str) -> List[ProductCandidate]:
        """Find exact matches in synonyms."""
        synonyms = self._load_synonyms()
        candidates = []
        
        # Split text into words and phrases
        words = text.split()
        phrases = []
        
        # Generate phrases of different lengths
        for i in range(len(words)):
            for j in range(i + 1, min(i + 4, len(words) + 1)):  # Up to 3-word phrases
                phrase = ' '.join(words[i:j])
                phrases.append(phrase)
        
        # Check exact matches
        for phrase in phrases:
            if phrase in synonyms:
                for product_id, product_name, brand in synonyms[phrase]:
                    candidates.append(ProductCandidate(
                        product_id=product_id,
                        product_name=product_name,
                        brand=brand,
                        category="",  # Will be filled later
                        confidence=1.0,
                        match_type="synonym",
                        matched_text=phrase
                    ))
        
        return candidates
    
    def _find_fuzzy_synonym_matches(self, text: str) -> List[ProductCandidate]:
        """Find fuzzy matches in synonyms."""
        synonyms = self._load_synonyms()
        candidates = []
        
        words = text.split()
        phrases = []
        
        # Generate phrases
        for i in range(len(words)):
            for j in range(i + 1, min(i + 4, len(words) + 1)):
                phrase = ' '.join(words[i:j])
                phrases.append(phrase)
        
        # Check fuzzy matches
        for phrase in phrases:
            for synonym, products in synonyms.items():
                similarity = self._calculate_fuzzy_similarity(phrase, synonym)
                if similarity > 0.7:  # Threshold for fuzzy matching
                    for product_id, product_name, brand in products:
                        candidates.append(ProductCandidate(
                            product_id=product_id,
                            product_name=product_name,
                            brand=brand,
                            category="",
                            confidence=similarity * 0.8,  # Slightly lower than exact
                            match_type="fuzzy",
                            matched_text=phrase
                        ))
        
        return candidates
    
    def _find_product_name_matches(self, text: str) -> List[ProductCandidate]:
        """Find matches in product names."""
        products = self._load_products()
        candidates = []
        
        words = text.split()
        phrases = []
        
        # Generate phrases
        for i in range(len(words)):
            for j in range(i + 1, min(i + 5, len(words) + 1)):  # Up to 4-word phrases
                phrase = ' '.join(words[i:j])
                phrases.append(phrase)
        
        # Check product name matches
        for phrase in phrases:
            for product_id, product_name, brand, category in products:
                # Check if phrase is in product name
                if phrase in product_name.lower():
                    similarity = self._calculate_fuzzy_similarity(phrase, product_name)
                    candidates.append(ProductCandidate(
                        product_id=product_id,
                        product_name=product_name,
                        brand=brand,
                        category=category,
                        confidence=similarity * 0.9,  # High confidence for direct matches
                        match_type="exact",
                        matched_text=phrase
                    ))
        
        return candidates
    
    def _find_trigram_matches(self, text: str) -> List[ProductCandidate]:
        """Find matches using trigram similarity."""
        products = self._load_products()
        candidates = []
        
        words = text.split()
        phrases = []
        
        # Generate phrases
        for i in range(len(words)):
            for j in range(i + 1, min(i + 4, len(words) + 1)):
                phrase = ' '.join(words[i:j])
                phrases.append(phrase)
        
        # Check trigram similarity
        for phrase in phrases:
            for product_id, product_name, brand, category in products:
                trigram_sim = self._calculate_trigram_similarity(phrase, product_name)
                if trigram_sim > 0.6:  # Threshold for trigram matching
                    candidates.append(ProductCandidate(
                        product_id=product_id,
                        product_name=product_name,
                        brand=brand,
                        category=category,
                        confidence=trigram_sim * 0.7,  # Lower confidence for trigram
                        match_type="trigram",
                        matched_text=phrase
                    ))
        
        return candidates
    
    def _deduplicate_candidates(self, candidates: List[ProductCandidate]) -> List[ProductCandidate]:
        """Remove duplicate candidates, keeping the highest confidence."""
        seen = {}
        unique_candidates = []
        
        for candidate in candidates:
            key = candidate.product_id
            if key not in seen or candidate.confidence > seen[key].confidence:
                seen[key] = candidate
        
        return list(seen.values())
    
    def extract_single_product(self, text: str) -> Optional[ProductCandidate]:
        """Extract the best single product match."""
        candidates = self.extract_products(text, limit=1)
        return candidates[0] if candidates else None
    
    def extract_multiple_products(self, text: str, limit: int = 3) -> List[ProductCandidate]:
        """Extract multiple product candidates for disambiguation."""
        return self.extract_products(text, limit=limit)
    
    def get_product_synonyms(self, product_id: str) -> List[str]:
        """Get synonyms for a specific product."""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                SELECT synonym FROM product_synonyms 
                WHERE product_id = ?
            """, (product_id,))
            
            return [row[0] for row in cursor.fetchall()]
            
        finally:
            conn.close()
    
    def normalize_product_name(self, text: str) -> str:
        """Normalize product name from text."""
        candidate = self.extract_single_product(text)
        if candidate:
            return candidate.product_name
        return text.strip()
