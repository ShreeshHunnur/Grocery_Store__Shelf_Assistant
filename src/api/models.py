"""
Pydantic models for API request/response schemas.
"""
from typing import List, Optional, Union
from pydantic import BaseModel, Field


class ProductMatch(BaseModel):
    """Individual product match for location queries."""
    product_id: str = Field(..., description="Unique product identifier")
    product_name: str = Field(..., description="Full product name")
    brand: str = Field(..., description="Product brand")
    category: str = Field(..., description="Product category")
    aisle: str = Field(..., description="Store aisle")
    bay: str = Field(..., description="Bay number")
    shelf: str = Field(..., description="Shelf level")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Match confidence score")


class ProductLocationResponse(BaseModel):
    """Response for product location queries."""
    query_type: str = Field(default="location", description="Query type identifier")
    normalized_product: str = Field(..., description="Normalized product name from query")
    matches: List[ProductMatch] = Field(..., description="List of matching products")
    disambiguation_needed: bool = Field(..., description="Whether user needs to clarify product choice")
    notes: Optional[str] = Field(None, description="Additional notes or instructions")


class ProductInfoResponse(BaseModel):
    """Response for product information queries."""
    query_type: str = Field(default="information", description="Query type identifier")
    normalized_product: str = Field(..., description="Normalized product name from query")
    answer: str = Field(..., description="LLM-generated answer about the product")
    caveats: Optional[str] = Field(None, description="Important disclaimers or limitations")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Response confidence score")


class TextQueryRequest(BaseModel):
    """Request for text-based queries."""
    query: str = Field(..., min_length=1, max_length=500, description="User's text query")
    session_id: Optional[str] = Field(None, description="Optional session identifier")


class VoiceQueryRequest(BaseModel):
    """Request for voice-based queries."""
    session_id: Optional[str] = Field(None, description="Optional session identifier")
    # Audio file will be handled as multipart form data


class HealthResponse(BaseModel):
    """Health check response."""
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="Application version")
    components: dict = Field(..., description="Component health status")


class ErrorResponse(BaseModel):
    """Error response schema."""
    error: str = Field(..., description="Error message")
    error_code: str = Field(..., description="Error code")
    details: Optional[dict] = Field(None, description="Additional error details")


# Union type for all possible responses
ResponseType = Union[ProductLocationResponse, ProductInfoResponse, ErrorResponse]
