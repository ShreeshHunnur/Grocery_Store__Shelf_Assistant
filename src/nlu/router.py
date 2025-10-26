"""
Keyword router and normalization for query classification.
Implements lightweight keyword-and-pattern classifier with confidence scoring.
"""
import re
from typing import List, Dict, Tuple, Optional
from dataclasses import dataclass

from .keywords import KeywordDictionary
from .product_extractor import ProductExtractor, ProductCandidate

@dataclass
class ClassificationResult:
    """Result of query classification."""
    route: str  # 'location' or 'information'
    confidence: float
    normalized_product: str
    disambiguation_needed: bool
    candidates: List[ProductCandidate] = None
    reasoning: str = ""

class QueryRouter:
    """Main router for classifying queries and extracting products."""
    
    def __init__(self, db_path: str):
        """Initialize router with database path."""
        self.db_path = db_path
        self.keyword_dict = KeywordDictionary()
        self.product_extractor = ProductExtractor(db_path)
        
        # Configuration thresholds
        self.location_threshold = 0.3
        self.information_threshold = 0.3
        self.disambiguation_threshold = 0.7
        self.confidence_threshold = 0.6
    
    def classify_query(self, text: str) -> ClassificationResult:
        """
        Classify a query as location or information intent.
        
        Args:
            text: Input query text
            
        Returns:
            ClassificationResult with route, confidence, and product info
        """
        if not text or not text.strip():
            return ClassificationResult(
                route="information",
                confidence=0.0,
                normalized_product="",
                disambiguation_needed=False,
                reasoning="Empty query"
            )
        
        # Calculate intent scores
        location_score = self.keyword_dict.calculate_location_score(text)
        information_score = self.keyword_dict.calculate_information_score(text)
        
        # Determine route and confidence
        if location_score > information_score:
            route = "location"
            confidence = location_score
            reasoning = f"Location keywords detected (score: {location_score:.2f})"
        elif information_score > location_score:
            route = "information"
            confidence = information_score
            reasoning = f"Information keywords detected (score: {information_score:.2f})"
        else:
            # Tie-breaker: prefer location if close, otherwise information
            if location_score > 0.1:
                route = "location"
                confidence = location_score
                reasoning = f"Tie-breaker: location preferred (score: {location_score:.2f})"
            else:
                route = "information"
                confidence = information_score
                reasoning = f"Tie-breaker: information preferred (score: {information_score:.2f})"
        
        # Extract product information
        product_candidates = self.product_extractor.extract_products(text, limit=3)
        
        # Determine if disambiguation is needed
        disambiguation_needed = self._needs_disambiguation(product_candidates, confidence)
        
        # Get normalized product name
        normalized_product = self._get_normalized_product(product_candidates, text)
        
        return ClassificationResult(
            route=route,
            confidence=confidence,
            normalized_product=normalized_product,
            disambiguation_needed=disambiguation_needed,
            candidates=product_candidates,
            reasoning=reasoning
        )
    
    def extract_product(self, text: str) -> Tuple[str, List[ProductCandidate]]:
        """
        Extract product information from text.
        
        Args:
            text: Input text
            
        Returns:
            Tuple of (normalized_product_name, candidates)
        """
        candidates = self.product_extractor.extract_products(text, limit=5)
        normalized_product = self._get_normalized_product(candidates, text)
        return normalized_product, candidates
    
    def _needs_disambiguation(self, candidates: List[ProductCandidate], confidence: float) -> bool:
        """Determine if disambiguation is needed."""
        if not candidates:
            return False
        
        # Need disambiguation if:
        # 1. Multiple candidates with similar confidence
        # 2. Top candidate confidence is below threshold
        # 3. Multiple candidates above a certain confidence level
        
        if len(candidates) < 2:
            return False
        
        top_confidence = candidates[0].confidence
        second_confidence = candidates[1].confidence if len(candidates) > 1 else 0.0
        
        # Multiple high-confidence candidates
        if top_confidence > self.disambiguation_threshold and second_confidence > self.disambiguation_threshold:
            return True
        
        # Close confidence scores
        if top_confidence > 0.5 and abs(top_confidence - second_confidence) < 0.2:
            return True
        
        # Low overall confidence
        if top_confidence < self.confidence_threshold:
            return True
        
        return False
    
    def _get_normalized_product(self, candidates: List[ProductCandidate], original_text: str) -> str:
        """Get normalized product name from candidates or original text."""
        if not candidates:
            return original_text.strip()
        
        # Use the highest confidence candidate
        best_candidate = candidates[0]
        return best_candidate.product_name
    
    def get_route_explanation(self, text: str) -> str:
        """Get detailed explanation of routing decision."""
        location_score = self.keyword_dict.calculate_location_score(text)
        information_score = self.keyword_dict.calculate_information_score(text)
        
        location_matches = self.keyword_dict.find_matching_keywords(text, "location")
        information_matches = self.keyword_dict.find_matching_keywords(text, "information")
        
        explanation = f"Query: '{text}'\n"
        explanation += f"Location score: {location_score:.2f}\n"
        explanation += f"Information score: {information_score:.2f}\n"
        
        if location_matches:
            explanation += f"Location keywords found: {[m[0].pattern for m in location_matches]}\n"
        
        if information_matches:
            explanation += f"Information keywords found: {[m[0].pattern for m in information_matches]}\n"
        
        if self.keyword_dict.has_negation(text):
            explanation += "Negation detected - confidence reduced\n"
        
        return explanation
    
    def handle_ambiguous_query(self, text: str) -> ClassificationResult:
        """Handle ambiguous queries that need disambiguation."""
        # Extract multiple product candidates
        candidates = self.product_extractor.extract_products(text, limit=5)
        
        # Classify intent
        location_score = self.keyword_dict.calculate_location_score(text)
        information_score = self.keyword_dict.calculate_information_score(text)
        
        route = "location" if location_score > information_score else "information"
        confidence = max(location_score, information_score)
        
        return ClassificationResult(
            route=route,
            confidence=confidence,
            normalized_product="",
            disambiguation_needed=True,
            candidates=candidates[:3],  # Top 3 candidates
            reasoning=f"Ambiguous query - {len(candidates)} candidates found"
        )
    
    def validate_classification(self, text: str, expected_route: str) -> bool:
        """Validate classification against expected route."""
        result = self.classify_query(text)
        return result.route == expected_route
    
    def get_classification_stats(self, test_cases: List[Tuple[str, str]]) -> Dict[str, float]:
        """
        Get classification statistics for test cases.
        
        Args:
            test_cases: List of (query, expected_route) tuples
            
        Returns:
            Dictionary with accuracy and other metrics
        """
        correct = 0
        total = len(test_cases)
        
        for query, expected_route in test_cases:
            result = self.classify_query(query)
            if result.route == expected_route:
                correct += 1
        
        accuracy = correct / total if total > 0 else 0.0
        
        return {
            "accuracy": accuracy,
            "correct": correct,
            "total": total,
            "incorrect": total - correct
        }
    
    def batch_classify(self, queries: List[str]) -> List[ClassificationResult]:
        """Classify multiple queries in batch."""
        results = []
        for query in queries:
            result = self.classify_query(query)
            results.append(result)
        return results
    
    def get_confidence_distribution(self, queries: List[str]) -> Dict[str, List[float]]:
        """Get confidence score distribution for queries."""
        location_confidences = []
        information_confidences = []
        
        for query in queries:
            result = self.classify_query(query)
            if result.route == "location":
                location_confidences.append(result.confidence)
            else:
                information_confidences.append(result.confidence)
        
        return {
            "location": location_confidences,
            "information": information_confidences
        }
