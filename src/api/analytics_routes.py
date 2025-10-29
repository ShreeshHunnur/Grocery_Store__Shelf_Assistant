"""
Analytics API routes for ShelfSense AI
Provides comprehensive analytics endpoints for dashboard and reporting.
"""
from fastapi import APIRouter, HTTPException, Query
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
import logging
from pathlib import Path

from ..services.analytics_service import AnalyticsService
from config.settings import BASE_DIR

logger = logging.getLogger(__name__)

# Initialize analytics service
analytics_db_path = BASE_DIR / "data" / "products.db"  # Use same database as main app
analytics_service = AnalyticsService(str(analytics_db_path))

analytics_router = APIRouter(prefix="/analytics", tags=["Analytics"])

@analytics_router.get("/dashboard")
async def get_dashboard_metrics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze")
) -> Dict[str, Any]:
    """
    Get comprehensive dashboard metrics for the specified number of days.
    
    Returns:
    - Overview metrics (total queries, sessions, response times, success rates)
    - Query trends over time
    - Popular products and search terms
    - Location analytics (busiest aisles, bays)
    - Performance metrics
    - Input method distribution
    - Success rates by various dimensions
    - Recent activities
    - Peak usage hours
    """
    try:
        metrics = analytics_service.get_dashboard_metrics(days)
        if not metrics:
            raise HTTPException(status_code=500, detail="Failed to retrieve analytics data")
        
        return {
            "status": "success",
            "data": metrics,
            "generated_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Failed to get dashboard metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Analytics error: {str(e)}")

@analytics_router.get("/overview")
async def get_analytics_overview(
    days: int = Query(7, ge=1, le=90, description="Number of days for overview")
) -> Dict[str, Any]:
    """Get high-level analytics overview."""
    try:
        full_metrics = analytics_service.get_dashboard_metrics(days)
        
        if not full_metrics:
            return {
                "status": "success",
                "data": {
                    "total_queries": 0,
                    "unique_sessions": 0,
                    "avg_response_time": 0,
                    "success_rate": 0,
                    "top_products": [],
                    "busiest_aisle": "N/A"
                }
            }
        
        overview = full_metrics.get("overview", {})
        popular_products = full_metrics.get("popular_products", [])
        location_analytics = full_metrics.get("location_analytics", {})
        
        # Get top product
        top_product = popular_products[0]["normalized_product"] if popular_products else "N/A"
        
        # Get busiest aisle
        busiest_aisles = location_analytics.get("busiest_aisles", [])
        busiest_aisle = busiest_aisles[0]["aisle"] if busiest_aisles else "N/A"
        
        return {
            "status": "success",
            "data": {
                "total_queries": overview.get("total_queries", 0),
                "unique_sessions": overview.get("unique_sessions", 0),
                "avg_response_time": overview.get("avg_response_time", 0),
                "success_rate": overview.get("success_rate", 0),
                "avg_confidence": overview.get("avg_confidence", 0),
                "top_product": top_product,
                "busiest_aisle": busiest_aisle,
                "date_range": full_metrics.get("date_range", {})
            }
        }
    except Exception as e:
        logger.error(f"Failed to get overview: {e}")
        raise HTTPException(status_code=500, detail=f"Overview error: {str(e)}")

@analytics_router.get("/trends")
async def get_query_trends(
    days: int = Query(30, ge=1, le=90, description="Number of days for trends"),
    granularity: str = Query("daily", regex="^(hourly|daily)$", description="Trend granularity")
) -> Dict[str, Any]:
    """Get query trends over time with specified granularity."""
    try:
        full_metrics = analytics_service.get_dashboard_metrics(days)
        
        if not full_metrics:
            return {"status": "success", "data": {"trends": []}}
        
        trends = full_metrics.get("query_trends", [])
        peak_hours = full_metrics.get("peak_hours", [])
        
        return {
            "status": "success",
            "data": {
                "daily_trends": trends,
                "hourly_patterns": peak_hours,
                "granularity": granularity
            }
        }
    except Exception as e:
        logger.error(f"Failed to get trends: {e}")
        raise HTTPException(status_code=500, detail=f"Trends error: {str(e)}")

@analytics_router.get("/products")
async def get_product_analytics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of products to return")
) -> Dict[str, Any]:
    """Get detailed product search analytics."""
    try:
        full_metrics = analytics_service.get_dashboard_metrics(days)
        
        if not full_metrics:
            return {"status": "success", "data": {"products": []}}
        
        products = full_metrics.get("popular_products", [])[:limit]
        
        # Calculate additional metrics
        total_searches = sum(p.get("search_count", 0) for p in products)
        
        # Add percentage for each product
        for product in products:
            if total_searches > 0:
                product["percentage"] = round((product.get("search_count", 0) / total_searches) * 100, 2)
            else:
                product["percentage"] = 0
        
        return {
            "status": "success",
            "data": {
                "products": products,
                "total_unique_products": len(products),
                "total_searches": total_searches
            }
        }
    except Exception as e:
        logger.error(f"Failed to get product analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Product analytics error: {str(e)}")

@analytics_router.get("/locations")
async def get_location_analytics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze")
) -> Dict[str, Any]:
    """Get detailed location-based analytics."""
    try:
        full_metrics = analytics_service.get_dashboard_metrics(days)
        
        if not full_metrics:
            return {"status": "success", "data": {"aisles": [], "bays": []}}
        
        location_data = full_metrics.get("location_analytics", {})
        
        return {
            "status": "success",
            "data": {
                "busiest_aisles": location_data.get("busiest_aisles", []),
                "busiest_bays": location_data.get("busiest_bays", []),
                "total_location_queries": sum(
                    aisle.get("query_count", 0) 
                    for aisle in location_data.get("busiest_aisles", [])
                )
            }
        }
    except Exception as e:
        logger.error(f"Failed to get location analytics: {e}")
        raise HTTPException(status_code=500, detail=f"Location analytics error: {str(e)}")

@analytics_router.get("/performance")
async def get_performance_metrics(
    days: int = Query(30, ge=1, le=365, description="Number of days to analyze")
) -> Dict[str, Any]:
    """Get detailed performance metrics and system health."""
    try:
        full_metrics = analytics_service.get_dashboard_metrics(days)
        
        if not full_metrics:
            return {"status": "success", "data": {}}
        
        performance = full_metrics.get("performance_metrics", {})
        overview = full_metrics.get("overview", {})
        input_methods = full_metrics.get("input_methods", [])
        success_rates = full_metrics.get("success_rates", {})
        
        return {
            "status": "success",
            "data": {
                "response_time_distribution": performance.get("response_time_distribution", []),
                "error_rates": performance.get("error_rates", []),
                "input_method_performance": input_methods,
                "success_rates": success_rates,
                "overall_metrics": {
                    "avg_response_time": overview.get("avg_response_time", 0),
                    "success_rate": overview.get("success_rate", 0),
                    "avg_confidence": overview.get("avg_confidence", 0)
                }
            }
        }
    except Exception as e:
        logger.error(f"Failed to get performance metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Performance metrics error: {str(e)}")

@analytics_router.get("/recent")
async def get_recent_activities(
    limit: int = Query(50, ge=1, le=200, description="Number of recent activities to return")
) -> Dict[str, Any]:
    """Get recent query activities."""
    try:
        activities = analytics_service.get_recent_activities(limit)
        
        return {
            "status": "success",
            "data": {
                "activities": activities,
                "total_activities": len(activities)
            }
        }
    except Exception as e:
        logger.error(f"Failed to get recent activities: {e}")
        raise HTTPException(status_code=500, detail=f"Recent activities error: {str(e)}")

@analytics_router.get("/real-time")
async def get_realtime_metrics() -> Dict[str, Any]:
    """Get real-time metrics for live dashboard updates."""
    try:
        # Get metrics for the last 24 hours
        full_metrics = analytics_service.get_dashboard_metrics(1)
        
        if not full_metrics:
            return {
                "status": "success",
                "data": {
                    "queries_last_hour": 0,
                    "active_sessions": 0,
                    "avg_response_time": 0,
                    "success_rate": 0,
                    "last_updated": datetime.now().isoformat()
                }
            }
        
        overview = full_metrics.get("overview", {})
        recent_activities = full_metrics.get("recent_activities", [])
        
        # Calculate queries in the last hour
        one_hour_ago = datetime.now() - timedelta(hours=1)
        queries_last_hour = len([
            activity for activity in recent_activities 
            if datetime.fromisoformat(activity.get("timestamp", "").replace("Z", "+00:00")) > one_hour_ago
        ])
        
        return {
            "status": "success",
            "data": {
                "queries_last_hour": queries_last_hour,
                "queries_today": overview.get("total_queries", 0),
                "active_sessions": overview.get("unique_sessions", 0),
                "avg_response_time": overview.get("avg_response_time", 0),
                "success_rate": overview.get("success_rate", 0),
                "avg_confidence": overview.get("avg_confidence", 0),
                "last_updated": datetime.now().isoformat()
            }
        }
    except Exception as e:
        logger.error(f"Failed to get real-time metrics: {e}")
        raise HTTPException(status_code=500, detail=f"Real-time metrics error: {str(e)}")

@analytics_router.get("/export")
async def export_analytics_data(
    days: int = Query(30, ge=1, le=365, description="Number of days to export"),
    format: str = Query("json", regex="^(json|csv)$", description="Export format")
) -> Dict[str, Any]:
    """Export analytics data in specified format."""
    try:
        full_metrics = analytics_service.get_dashboard_metrics(days)
        
        if not full_metrics:
            return {"status": "success", "data": {}}
        
        if format == "json":
            return {
                "status": "success",
                "format": "json",
                "data": full_metrics,
                "exported_at": datetime.now().isoformat()
            }
        elif format == "csv":
            # For CSV, return a simplified structure
            # In a real implementation, you'd generate actual CSV content
            return {
                "status": "success",
                "format": "csv",
                "message": "CSV export functionality can be implemented based on specific requirements",
                "available_data": list(full_metrics.keys()),
                "exported_at": datetime.now().isoformat()
            }
        
    except Exception as e:
        logger.error(f"Failed to export analytics data: {e}")
        raise HTTPException(status_code=500, detail=f"Export error: {str(e)}")

@analytics_router.get("/health")
async def analytics_health_check() -> Dict[str, Any]:
    """Check analytics service health and data availability."""
    try:
        # Try to get basic metrics to test database connectivity
        overview_data = analytics_service.get_dashboard_metrics(1)
        
        return {
            "status": "healthy",
            "database_connected": True,
            "data_available": bool(overview_data),
            "last_query_count": overview_data.get("overview", {}).get("total_queries", 0) if overview_data else 0,
            "checked_at": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Analytics health check failed: {e}")
        return {
            "status": "unhealthy",
            "database_connected": False,
            "error": str(e),
            "checked_at": datetime.now().isoformat()
        }