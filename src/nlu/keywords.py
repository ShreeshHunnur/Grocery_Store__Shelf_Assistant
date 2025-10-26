"""
Keyword dictionaries and patterns for query classification.
Provides location and information keywords with stemming and negation handling.
"""
import re
from typing import List, Dict, Set, Tuple
from dataclasses import dataclass

@dataclass
class KeywordPattern:
    """Represents a keyword pattern with weight and type."""
    pattern: str
    weight: float
    type: str  # 'location', 'information', 'negation'
    stemmed: bool = False

class KeywordDictionary:
    """Manages keyword dictionaries for query classification."""
    
    def __init__(self):
        """Initialize keyword dictionaries."""
        self.location_keywords = self._build_location_keywords()
        self.information_keywords = self._build_information_keywords()
        self.negation_patterns = self._build_negation_patterns()
        self.stemming_map = self._build_stemming_map()
        
    def _build_location_keywords(self) -> List[KeywordPattern]:
        """Build location-related keywords with weights."""
        return [
            # Direct location queries
            KeywordPattern("where", 1.0, "location"),
            KeywordPattern("find", 1.0, "location"),
            KeywordPattern("located", 1.0, "location"),
            KeywordPattern("locate", 1.0, "location"),
            KeywordPattern("position", 0.9, "location"),
            KeywordPattern("place", 0.9, "location"),
            KeywordPattern("spot", 0.8, "location"),
            
            # Aisle and section terms
            KeywordPattern("aisle", 1.0, "location"),
            KeywordPattern("section", 1.0, "location"),
            KeywordPattern("shelf", 1.0, "location"),
            KeywordPattern("bay", 0.9, "location"),
            KeywordPattern("row", 0.8, "location"),
            KeywordPattern("corridor", 0.7, "location"),
            KeywordPattern("hallway", 0.7, "location"),
            
            # Proximity terms
            KeywordPattern("near", 0.9, "location"),
            KeywordPattern("next to", 0.9, "location"),
            KeywordPattern("beside", 0.8, "location"),
            KeywordPattern("close to", 0.8, "location"),
            KeywordPattern("around", 0.7, "location"),
            KeywordPattern("by", 0.6, "location"),
            
            # Directional terms
            KeywordPattern("left", 0.6, "location"),
            KeywordPattern("right", 0.6, "location"),
            KeywordPattern("front", 0.6, "location"),
            KeywordPattern("back", 0.6, "location"),
            KeywordPattern("top", 0.5, "location"),
            KeywordPattern("bottom", 0.5, "location"),
            KeywordPattern("middle", 0.5, "location"),
            
            # Store layout terms
            KeywordPattern("entrance", 0.7, "location"),
            KeywordPattern("exit", 0.7, "location"),
            KeywordPattern("checkout", 0.6, "location"),
            KeywordPattern("register", 0.6, "location"),
            KeywordPattern("counter", 0.5, "location"),
            
            # Question words
            KeywordPattern("which aisle", 1.0, "location"),
            KeywordPattern("what aisle", 1.0, "location"),
            KeywordPattern("which section", 1.0, "location"),
            KeywordPattern("what section", 1.0, "location"),
            KeywordPattern("which shelf", 1.0, "location"),
            KeywordPattern("what shelf", 1.0, "location"),
        ]
    
    def _build_information_keywords(self) -> List[KeywordPattern]:
        """Build information-related keywords with weights."""
        return [
            # Nutrition and dietary
            KeywordPattern("ingredients", 1.0, "information"),
            KeywordPattern("nutrition", 1.0, "information"),
            KeywordPattern("calories", 1.0, "information"),
            KeywordPattern("calorie", 1.0, "information"),
            KeywordPattern("protein", 0.9, "information"),
            KeywordPattern("carbs", 0.9, "information"),
            KeywordPattern("carbohydrates", 0.9, "information"),
            KeywordPattern("fat", 0.9, "information"),
            KeywordPattern("sugar", 0.9, "information"),
            KeywordPattern("sodium", 0.9, "information"),
            KeywordPattern("fiber", 0.8, "information"),
            KeywordPattern("vitamins", 0.8, "information"),
            KeywordPattern("minerals", 0.8, "information"),
            
            # Dietary restrictions
            KeywordPattern("vegan", 1.0, "information"),
            KeywordPattern("vegetarian", 1.0, "information"),
            KeywordPattern("gluten-free", 1.0, "information"),
            KeywordPattern("gluten free", 1.0, "information"),
            KeywordPattern("dairy-free", 1.0, "information"),
            KeywordPattern("dairy free", 1.0, "information"),
            KeywordPattern("lactose-free", 1.0, "information"),
            KeywordPattern("lactose free", 1.0, "information"),
            KeywordPattern("halal", 1.0, "information"),
            KeywordPattern("kosher", 1.0, "information"),
            KeywordPattern("keto", 0.9, "information"),
            KeywordPattern("paleo", 0.9, "information"),
            KeywordPattern("organic", 0.8, "information"),
            KeywordPattern("natural", 0.8, "information"),
            KeywordPattern("non-gmo", 0.8, "information"),
            KeywordPattern("non gmo", 0.8, "information"),
            
            # Allergens
            KeywordPattern("allergens", 1.0, "information"),
            KeywordPattern("allergies", 1.0, "information"),
            KeywordPattern("allergic", 0.9, "information"),
            KeywordPattern("contains", 0.8, "information"),
            KeywordPattern("may contain", 0.8, "information"),
            KeywordPattern("nuts", 0.7, "information"),
            KeywordPattern("peanuts", 0.7, "information"),
            KeywordPattern("tree nuts", 0.7, "information"),
            KeywordPattern("soy", 0.7, "information"),
            KeywordPattern("eggs", 0.7, "information"),
            KeywordPattern("shellfish", 0.7, "information"),
            KeywordPattern("fish", 0.7, "information"),
            
            # Product details
            KeywordPattern("price", 1.0, "information"),
            KeywordPattern("cost", 1.0, "information"),
            KeywordPattern("expensive", 0.8, "information"),
            KeywordPattern("cheap", 0.8, "information"),
            KeywordPattern("size", 1.0, "information"),
            KeywordPattern("weight", 0.9, "information"),
            KeywordPattern("volume", 0.9, "information"),
            KeywordPattern("dimensions", 0.8, "information"),
            KeywordPattern("package", 0.8, "information"),
            KeywordPattern("container", 0.8, "information"),
            
            # Policies and guarantees
            KeywordPattern("return policy", 1.0, "information"),
            KeywordPattern("warranty", 1.0, "information"),
            KeywordPattern("guarantee", 1.0, "information"),
            KeywordPattern("expiration", 1.0, "information"),
            KeywordPattern("expiry", 1.0, "information"),
            KeywordPattern("expires", 1.0, "information"),
            KeywordPattern("best before", 1.0, "information"),
            KeywordPattern("sell by", 1.0, "information"),
            KeywordPattern("use by", 1.0, "information"),
            KeywordPattern("fresh", 0.8, "information"),
            KeywordPattern("frozen", 0.8, "information"),
            KeywordPattern("refrigerated", 0.8, "information"),
            
            # Usage and preparation
            KeywordPattern("how to", 0.9, "information"),
            KeywordPattern("how do", 0.9, "information"),
            KeywordPattern("cook", 0.8, "information"),
            KeywordPattern("prepare", 0.8, "information"),
            KeywordPattern("serve", 0.8, "information"),
            KeywordPattern("recipe", 0.8, "information"),
            KeywordPattern("instructions", 0.8, "information"),
            KeywordPattern("directions", 0.8, "information"),
            KeywordPattern("usage", 0.7, "information"),
            KeywordPattern("storage", 0.7, "information"),
            KeywordPattern("store", 0.7, "information"),
            
            # Quality and reviews
            KeywordPattern("quality", 0.8, "information"),
            KeywordPattern("rating", 0.8, "information"),
            KeywordPattern("review", 0.8, "information"),
            KeywordPattern("recommend", 0.8, "information"),
            KeywordPattern("popular", 0.7, "information"),
            KeywordPattern("best", 0.7, "information"),
            KeywordPattern("good", 0.6, "information"),
            KeywordPattern("bad", 0.6, "information"),
            
            # Question patterns
            KeywordPattern("what is", 0.9, "information"),
            KeywordPattern("what are", 0.9, "information"),
            KeywordPattern("tell me about", 0.9, "information"),
            KeywordPattern("explain", 0.8, "information"),
            KeywordPattern("describe", 0.8, "information"),
        ]
    
    def _build_negation_patterns(self) -> List[KeywordPattern]:
        """Build negation patterns for handling negative queries."""
        return [
            KeywordPattern("not", 1.0, "negation"),
            KeywordPattern("no", 1.0, "negation"),
            KeywordPattern("don't", 1.0, "negation"),
            KeywordPattern("dont", 1.0, "negation"),
            KeywordPattern("doesn't", 1.0, "negation"),
            KeywordPattern("doesnt", 1.0, "negation"),
            KeywordPattern("isn't", 1.0, "negation"),
            KeywordPattern("isnt", 1.0, "negation"),
            KeywordPattern("aren't", 1.0, "negation"),
            KeywordPattern("arent", 1.0, "negation"),
            KeywordPattern("wasn't", 1.0, "negation"),
            KeywordPattern("wasnt", 1.0, "negation"),
            KeywordPattern("weren't", 1.0, "negation"),
            KeywordPattern("werent", 1.0, "negation"),
            KeywordPattern("won't", 1.0, "negation"),
            KeywordPattern("wont", 1.0, "negation"),
            KeywordPattern("can't", 1.0, "negation"),
            KeywordPattern("cant", 1.0, "negation"),
            KeywordPattern("couldn't", 1.0, "negation"),
            KeywordPattern("couldnt", 1.0, "negation"),
            KeywordPattern("shouldn't", 1.0, "negation"),
            KeywordPattern("shouldnt", 1.0, "negation"),
            KeywordPattern("wouldn't", 1.0, "negation"),
            KeywordPattern("wouldnt", 1.0, "negation"),
            KeywordPattern("never", 0.9, "negation"),
            KeywordPattern("none", 0.9, "negation"),
            KeywordPattern("nothing", 0.9, "negation"),
            KeywordPattern("nobody", 0.9, "negation"),
            KeywordPattern("nowhere", 0.9, "negation"),
        ]
    
    def _build_stemming_map(self) -> Dict[str, str]:
        """Build stemming map for word normalization."""
        return {
            # Common stemming patterns
            "ingredients": "ingredient",
            "calories": "calorie",
            "allergens": "allergen",
            "allergies": "allergy",
            "vitamins": "vitamin",
            "minerals": "mineral",
            "carbohydrates": "carbohydrate",
            "dimensions": "dimension",
            "instructions": "instruction",
            "directions": "direction",
            "recommendations": "recommendation",
            "reviews": "review",
            "ratings": "rating",
            "policies": "policy",
            "guarantees": "guarantee",
            "warranties": "warranty",
            "expirations": "expiration",
            "expiries": "expiry",
            "containers": "container",
            "packages": "package",
            "products": "product",
            "items": "item",
            "brands": "brand",
            "categories": "category",
            "sections": "section",
            "aisles": "aisle",
            "shelves": "shelf",
            "bays": "bay",
            "rows": "row",
            "corridors": "corridor",
            "hallways": "hallway",
            "entrances": "entrance",
            "exits": "exit",
            "checkouts": "checkout",
            "registers": "register",
            "counters": "counter",
            "locations": "location",
            "positions": "position",
            "places": "place",
            "spots": "spot",
            "directions": "direction",
            "instructions": "instruction",
        }
    
    def stem_word(self, word: str) -> str:
        """Apply stemming to a word."""
        word_lower = word.lower()
        return self.stemming_map.get(word_lower, word_lower)
    
    def get_location_keywords(self) -> List[KeywordPattern]:
        """Get all location keywords."""
        return self.location_keywords
    
    def get_information_keywords(self) -> List[KeywordPattern]:
        """Get all information keywords."""
        return self.information_keywords
    
    def get_negation_patterns(self) -> List[KeywordPattern]:
        """Get all negation patterns."""
        return self.negation_patterns
    
    def find_matching_keywords(self, text: str, keyword_type: str) -> List[Tuple[KeywordPattern, float]]:
        """
        Find matching keywords in text with confidence scores.
        
        Args:
            text: Input text to search
            keyword_type: 'location', 'information', or 'negation'
            
        Returns:
            List of (pattern, confidence) tuples
        """
        text_lower = text.lower()
        matches = []
        
        if keyword_type == "location":
            keywords = self.location_keywords
        elif keyword_type == "information":
            keywords = self.information_keywords
        elif keyword_type == "negation":
            keywords = self.negation_patterns
        else:
            return matches
        
        for pattern in keywords:
            # Check for exact match
            if pattern.pattern in text_lower:
                confidence = pattern.weight
                matches.append((pattern, confidence))
            # Check for stemmed match
            elif pattern.stemmed:
                stemmed_pattern = self.stem_word(pattern.pattern)
                if stemmed_pattern in text_lower:
                    confidence = pattern.weight * 0.8  # Slightly lower confidence for stemmed
                    matches.append((pattern, confidence))
        
        return matches
    
    def has_negation(self, text: str) -> bool:
        """Check if text contains negation patterns."""
        negation_matches = self.find_matching_keywords(text, "negation")
        return len(negation_matches) > 0
    
    def calculate_location_score(self, text: str) -> float:
        """Calculate location intent score."""
        matches = self.find_matching_keywords(text, "location")
        if not matches:
            return 0.0
        
        # Sum weighted scores
        total_score = sum(confidence for _, confidence in matches)
        
        # Apply negation penalty
        if self.has_negation(text):
            total_score *= 0.3  # Significant penalty for negation
        
        return min(1.0, total_score)
    
    def calculate_information_score(self, text: str) -> float:
        """Calculate information intent score."""
        matches = self.find_matching_keywords(text, "information")
        if not matches:
            return 0.0
        
        # Sum weighted scores
        total_score = sum(confidence for _, confidence in matches)
        
        # Apply negation penalty
        if self.has_negation(text):
            total_score *= 0.3  # Significant penalty for negation
        
        return min(1.0, total_score)
