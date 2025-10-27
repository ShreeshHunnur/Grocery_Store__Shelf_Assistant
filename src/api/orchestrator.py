"""
Backend orchestration service that wires router, DB, and LLM services.
Provides unified API with schema-compliant responses.
"""
import logging
import time
import uuid
from typing import Dict, Any, Optional
from dataclasses import dataclass
import os
import sqlite3
from pathlib import Path

from ..nlu.router import QueryRouter, ClassificationResult
from ..services.db_queries import DatabaseService
from ..services.llm_service import LLMService
from ..api.models import ProductLocationResponse, ProductInfoResponse, ErrorResponse
from config.settings import DATABASE_CONFIG, LLM_CONFIG

# Configure logging
logger = logging.getLogger(__name__)

@dataclass
class ProcessingMetrics:
    """Metrics for request processing."""
    trace_id: str
    route: str
    latency_ms: float
    confidence: float
    product_extracted: bool
    disambiguation_needed: bool

class BackendOrchestrator:
    """Main orchestration service for the retail assistant."""
    
    def __init__(self, db_path: str = None):
        """Initialize orchestrator with database path."""
        self.db_path = db_path or str(DATABASE_CONFIG["path"])
        self.router = QueryRouter(self.db_path)
        self.db_service = DatabaseService(self.db_path)
        self.llm_service = LLMService()
        # Embedding / FAISS setup (optional)
        self.embedding_model = None
        self.faiss_index = None
        self.faiss_map = {}

        try:
            # Lazy import to avoid hard dependency if not available
            # Compatibility: some versions of huggingface_hub removed
            # `cached_download` in favor of `hf_hub_download`. Patch the
            # module if present so downstream imports (sentence-transformers
            # or its dependencies) that expect cached_download continue to work.
            try:
                import huggingface_hub as _hf_hub
                # If hf_hub_download exists but cached_download does not,
                # provide a compatibility wrapper that accepts the older
                # `cached_download(url=...)` call pattern used in some
                # downstream packages. If a URL is supplied, download it
                # via requests to a temporary file; otherwise forward to
                # hf_hub_download.
                if not hasattr(_hf_hub, 'cached_download') and hasattr(_hf_hub, 'hf_hub_download'):
                    def _cached_download(url=None, *args, **kwargs):
                        # Direct URL download path (older callers pass url=...)
                        if url:
                            try:
                                import requests
                                import tempfile
                                import os
                                resp = requests.get(url, stream=True, timeout=30)
                                resp.raise_for_status()
                                filename = os.path.basename(url.split('?')[0]) or ''
                                tmp = tempfile.NamedTemporaryFile(delete=False, suffix=filename)
                                for chunk in resp.iter_content(8192):
                                    if chunk:
                                        tmp.write(chunk)
                                tmp.close()
                                return tmp.name
                            except Exception:
                                # If direct download fails, attempt to call
                                # hf_hub_download as a fallback.
                                return _hf_hub.hf_hub_download(*args, **kwargs)
                        # Otherwise forward to hf_hub_download
                        return _hf_hub.hf_hub_download(*args, **kwargs)

                    _hf_hub.cached_download = _cached_download
            except Exception:
                # Ignore patch errors; we'll catch failures on import below
                pass

            from sentence_transformers import SentenceTransformer
            import faiss

            # Load embedding model
            try:
                self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
            except Exception as e:
                logger.warning(f"Failed to load embedding model: {e}")
                self.embedding_model = None

            # Load FAISS index if present
            data_dir = Path(self.db_path).parent
            index_path = data_dir / 'faiss_index.bin'
            if index_path.exists():
                try:
                    self.faiss_index = faiss.read_index(str(index_path))
                    # Load mapping from DB
                    conn = sqlite3.connect(self.db_path)
                    cur = conn.cursor()
                    cur.execute("SELECT faiss_idx, product_id FROM faiss_mapping ORDER BY faiss_idx")
                    rows = cur.fetchall()
                    for idx, pid in rows:
                        self.faiss_map[int(idx)] = int(pid)
                    conn.close()
                    logger.info(f"Loaded FAISS index with {len(self.faiss_map)} entries from {index_path}")
                except Exception as e:
                    logger.warning(f"Failed to load FAISS index: {e}")
            else:
                logger.info("No FAISS index found; vector search disabled")
        except Exception as e:
            # Log the exception so the real cause (missing packages, import
            # errors, or model download failures) is visible in logs. Keep
            # behavior backward-compatible by disabling vector search.
            logger.info(f"FAISS or sentence-transformers not installed; vector search disabled: {e}")
        
    def _get_trace_id(self) -> str:
        """Generate unique trace ID for request tracking."""
        return str(uuid.uuid4())[:8]
    
    def _log_request(self, trace_id: str, query: str, route: str, confidence: float):
        """Log request details with trace ID."""
        logger.info(f"[{trace_id}] Processing query: '{query}' -> {route} (confidence: {confidence:.3f})")
    
    def _log_response(self, trace_id: str, metrics: ProcessingMetrics):
        """Log response metrics."""
        logger.info(f"[{trace_id}] Response: {metrics.route}, {metrics.latency_ms:.1f}ms, "
                   f"confidence: {metrics.confidence:.3f}, products: {metrics.product_extracted}")
    
    def _get_llm_service(self):
        """Get LLM service instance."""
        return self.llm_service
    
    def process_text_query(self, query: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Process text query through the full pipeline.
        
        Args:
            query: User's text query
            session_id: Optional session identifier
            
        Returns:
            Schema-compliant JSON response
        """
        start_time = time.time()
        trace_id = self._get_trace_id()
        
        try:
            # Step 1: Classify query
            classification = self.router.classify_query(query)
            self._log_request(trace_id, query, classification.route, classification.confidence)
            
            # Step 2: Route to appropriate service
            if classification.route == "location":
                response = self._handle_location_query(query, classification, trace_id)
                product_extracted_flag = bool(classification.normalized_product)
            else:
                response = self._handle_information_query(query, classification, trace_id)
                # For information routes we intentionally do not extract or use
                # product data; report product_extracted as False in metrics.
                product_extracted_flag = False
            
            # Step 3: Calculate metrics
            latency_ms = (time.time() - start_time) * 1000
            metrics = ProcessingMetrics(
                trace_id=trace_id,
                route=classification.route,
                latency_ms=latency_ms,
                confidence=classification.confidence,
                product_extracted=product_extracted_flag,
                disambiguation_needed=classification.disambiguation_needed
            )
            
            self._log_response(trace_id, metrics)
            
            return response
            
        except Exception as e:
            logger.error(f"[{trace_id}] Error processing query: {e}", exc_info=True)
            return self._create_error_response("Internal processing error", "PROCESSING_ERROR", trace_id)
    
    def _handle_location_query(self, query: str, classification: ClassificationResult, trace_id: str) -> Dict[str, Any]:
        """Handle location queries using database service."""
        try:
            # Extract product from query
            normalized_product, candidates = self.router.extract_product(query)

            # If FAISS index and embedding model are available, prefer vector retrieval
            if self.faiss_index is not None and self.embedding_model is not None:
                try:
                    match = self._retrieve_top_product_by_embedding(query)
                    if match:
                        logger.info(f"[{trace_id}] Returning top FAISS match: {match.product_name} (id={match.product_id})")
                        matches = [{
                            "product_id": match.product_id,
                            "product_name": match.product_name,
                            "brand": match.brand,
                            "category": match.category,
                            "aisle": match.aisle,
                            "bay": match.bay,
                            "shelf": match.shelf,
                            "confidence": match.confidence
                        }]

                        return ProductLocationResponse(
                            normalized_product=normalized_product or query,
                            matches=matches,
                            disambiguation_needed=False,
                            notes="Top vector-match result"
                        ).dict()
                except Exception as e:
                    logger.warning(f"[{trace_id}] FAISS retrieval failed, falling back to SQL: {e}")
            
            # Add debug logging
            logger.info(f"[{trace_id}] Extracted product: '{normalized_product}', candidates: {len(candidates)}")
            for i, candidate in enumerate(candidates[:5]):
                logger.info(f"[{trace_id}] Candidate {i+1}: {candidate.product_name} (confidence: {candidate.confidence:.3f})")
            
            if not candidates:
                # No products found
                logger.warning(f"[{trace_id}] No product candidates found for query: '{query}'")
                return ProductLocationResponse(
                    normalized_product=normalized_product or query,
                    matches=[],
                    disambiguation_needed=False,
                    notes="No products found matching your query"
                ).dict()
            
            # Get location data for candidates
            matches = []
            for candidate in candidates[:5]:  # Limit to top 5
                logger.info(f"[{trace_id}] Looking up location for: {candidate.product_name}")
                db_matches = self.db_service.find_product_locations(candidate.product_name, limit=1)
                logger.info(f"[{trace_id}] Found {len(db_matches)} locations for {candidate.product_name}")
                
                if db_matches:
                    match = db_matches[0]
                    matches.append({
                        "product_id": match.product_id,
                        "product_name": match.product_name,
                        "brand": match.brand,
                        "category": match.category,
                        "aisle": match.aisle,
                        "bay": match.bay,
                        "shelf": match.shelf,
                        "confidence": match.confidence
                    })
            
            # Add more debug logging
            logger.info(f"[{trace_id}] Final matches: {len(matches)}")
            
            # Determine if disambiguation is needed
            disambiguation_needed = classification.disambiguation_needed or len(matches) > 1
            
            return ProductLocationResponse(
                normalized_product=normalized_product,
                matches=matches,
                disambiguation_needed=disambiguation_needed,
                notes=f"Found {len(matches)} product(s) matching your query"
            ).dict()
            
        except Exception as e:
            logger.error(f"[{trace_id}] Error in location query: {e}", exc_info=True)
            return self._create_error_response("Database query failed", "DB_ERROR", trace_id)
    
    def _handle_information_query(self, query: str, classification: ClassificationResult, trace_id: str) -> Dict[str, Any]:
        """Handle information queries using LLM service."""
        try:
            # For informational queries, do NOT include DB product attributes.
            # Pass an empty string for normalized_product so Pydantic models
            # that expect a string do not raise validation errors.
            llm_service = self._get_llm_service()
            response = llm_service.generate_info_answer("", query, {})
            return response.dict()
            
        except Exception as e:
            logger.error(f"[{trace_id}] Error in information query: {e}")
            return self._create_error_response("LLM processing failed", "LLM_ERROR", trace_id)
    
    def _get_product_attributes(self, normalized_product: str, candidates: list) -> Dict[str, Any]:
        """Get product attributes from database for LLM context."""
        attributes = {}
        
        if candidates:
            # Get attributes from the first candidate
            candidate = candidates[0]
            try:
                # Get product details from database
                product_details = self.db_service.get_product_by_id(candidate.product_id)
                if product_details:
                    attributes["brand"] = product_details.brand
                    attributes["category"] = product_details.category
                    # Add more attributes as needed
            except Exception as e:
                logger.warning(f"Failed to get product attributes: {e}")
        
        return attributes

    def _retrieve_top_product_by_embedding(self, query_text: str):
        """Use embedding model + FAISS index to retrieve the top product match.

        Returns a ProductMatch-like object from DatabaseService.get_product_by_id or None.
        """
        if not self.embedding_model or not self.faiss_index or not self.faiss_map:
            return None

        try:
            import numpy as np
            from numpy import linalg as LA
            # Compute embedding
            vec = self.embedding_model.encode([query_text], convert_to_numpy=True)
            # Normalize
            faiss_vec = vec.astype('float32')
            try:
                import faiss
                faiss.normalize_L2(faiss_vec)
            except Exception:
                # If normalization fails, proceed without it
                pass

            D, I = self.faiss_index.search(faiss_vec, 1)
            idx = int(I[0][0])
            if idx < 0:
                return None

            product_id = self.faiss_map.get(idx)
            if not product_id:
                return None

            # Fetch product by id
            product = self.db_service.get_product_by_id(product_id)
            return product
        except Exception as e:
            logger.warning(f"Embedding retrieval error: {e}")
            return None
    
    def _determine_caveats(self, confidence: float, candidates: list) -> Optional[str]:
        """Determine caveats based on confidence and candidates."""
        caveats = []
        
        if confidence < 0.7:
            caveats.append("Low confidence in answer")
        
        if not candidates:
            caveats.append("No specific product identified")
        elif len(candidates) > 1:
            caveats.append("Multiple products may match your query")
        
        return "; ".join(caveats) if caveats else None
    
    def _create_error_response(self, error_message: str, error_code: str, trace_id: str) -> Dict[str, Any]:
        """Create standardized error response."""
        return ErrorResponse(
            error=error_message,
            error_code=error_code,
            details={"trace_id": trace_id}
        ).dict()
    
    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of all services."""
        try:
            # Check database
            db_stats = self.db_service.get_database_stats()
            db_healthy = db_stats.get('products', 0) > 0
            
            # Check LLM service
            llm_health = self.llm_service.get_health_status()
            llm_healthy = llm_health.get("status") == "healthy"
            
            return {
                "database": "healthy" if db_healthy else "unhealthy",
                "llm": "healthy" if llm_healthy else "unhealthy",
                "router": "healthy",
                "overall": "healthy" if db_healthy and llm_healthy else "degraded"
            }
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return {
                "database": "unhealthy",
                "llm": "unhealthy", 
                "router": "unhealthy",
                "overall": "unhealthy"
            }

