"""
Analytics Service for ShelfSense AI
Comprehensive tracking and analysis of user queries, performance, and usage patterns.
"""
import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from pathlib import Path
import logging
from dataclasses import dataclass, asdict
import random
import string

logger = logging.getLogger(__name__)

@dataclass
class QueryAnalytics:
    """Data class for query analytics."""
    session_id: str
    query_text: str
    query_type: str
    input_method: str
    response_time_ms: int
    confidence_score: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None

@dataclass
class ProductSearch:
    """Data class for product search tracking."""
    query_id: int
    normalized_product: str
    original_product: str
    found: bool = False
    match_count: int = 0
    best_match_confidence: Optional[float] = None
    disambiguation_needed: bool = False

@dataclass
class LocationQuery:
    """Data class for location query tracking."""
    query_id: int
    product_name: str
    aisle: Optional[str] = None
    bay: Optional[str] = None
    shelf: Optional[str] = None
    confidence: Optional[float] = None

@dataclass
class InformationQuery:
    """Data class for information query tracking."""
    query_id: int
    product_name: str
    info_type: str
    found: bool = False
    response_length: int = 0

class AnalyticsService:
    """Service for tracking and analyzing user queries and system performance."""
    
    def __init__(self, db_path: str):
        self.db_path = Path(db_path)
        self.init_database()
        self._populate_sample_data()
    
    def init_database(self):
        """Initialize the analytics database with schema."""
        try:
            # Look for schema file in the database directory (not src/database)
            schema_path = Path(__file__).parent.parent.parent / "database" / "analytics_schema.sql"
            if schema_path.exists():
                with open(schema_path, 'r') as f:
                    schema_sql = f.read()
                
                with sqlite3.connect(self.db_path) as conn:
                    conn.executescript(schema_sql)
                    conn.commit()
                logger.info("Analytics database initialized successfully")
            else:
                logger.warning(f"Analytics schema file not found: {schema_path}")
        except Exception as e:
            logger.error(f"Failed to initialize analytics database: {e}")
    
    def track_query(self, analytics: QueryAnalytics) -> int:
        """Track a user query and return the query ID."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO query_analytics 
                    (session_id, query_text, query_type, input_method, response_time_ms, 
                     confidence_score, success, error_message, user_agent, ip_address)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    analytics.session_id, analytics.query_text, analytics.query_type,
                    analytics.input_method, analytics.response_time_ms, analytics.confidence_score,
                    analytics.success, analytics.error_message, analytics.user_agent, analytics.ip_address
                ))
                query_id = cursor.lastrowid
                
                # Update session analytics using the same connection
                self._update_session_analytics_with_conn(conn, analytics.session_id, analytics)
                
                # Update search trends using the same connection
                self._update_search_trends_with_conn(conn, analytics.query_text, analytics.query_type)
                
                conn.commit()
                return query_id
        except Exception as e:
            logger.error(f"Failed to track query: {e}")
            return -1
    
    def track_product_search(self, search: ProductSearch):
        """Track a product search query."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO product_searches 
                    (query_id, normalized_product, original_product, found, match_count, 
                     best_match_confidence, disambiguation_needed)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    search.query_id, search.normalized_product, search.original_product,
                    search.found, search.match_count, search.best_match_confidence,
                    search.disambiguation_needed
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to track product search: {e}")
    
    def track_location_query(self, location: LocationQuery):
        """Track a location query."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO location_queries 
                    (query_id, product_name, aisle, bay, shelf, confidence)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    location.query_id, location.product_name, location.aisle,
                    location.bay, location.shelf, location.confidence
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to track location query: {e}")
    
    def track_information_query(self, info: InformationQuery):
        """Track an information query."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO information_queries 
                    (query_id, product_name, info_type, found, response_length)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    info.query_id, info.product_name, info.info_type,
                    info.found, info.response_length
                ))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to track information query: {e}")
    
    def track_performance_metric(self, name: str, value: float, unit: str = "", category: str = ""):
        """Track a performance metric."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO performance_metrics (metric_name, metric_value, unit, category)
                    VALUES (?, ?, ?, ?)
                """, (name, value, unit, category))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to track performance metric: {e}")
    
    def track_error(self, error_type: str, error_message: str, query_text: str = "",
                   input_method: str = "", session_id: str = "", stack_trace: str = ""):
        """Track an error occurrence."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO error_analytics 
                    (error_type, error_message, query_text, input_method, session_id, stack_trace)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (error_type, error_message, query_text, input_method, session_id, stack_trace))
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to track error: {e}")
    
    def get_dashboard_metrics(self, days: int = 30) -> Dict[str, Any]:
        """Get comprehensive dashboard metrics for the specified number of days."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                
                # Date range for filtering
                end_date = datetime.now()
                start_date = end_date - timedelta(days=days)
                
                # Overall metrics
                overall_metrics = self._get_overall_metrics(conn, start_date, end_date)
                
                # Query trends
                query_trends = self._get_query_trends(conn, start_date, end_date)
                
                # Popular products
                popular_products = self._get_popular_products(conn, start_date, end_date)
                
                # Location analytics
                location_analytics = self._get_location_analytics(conn, start_date, end_date)
                
                # Performance metrics
                performance_metrics = self._get_performance_metrics(conn, start_date, end_date)
                
                # Input method distribution
                input_methods = self._get_input_method_distribution(conn, start_date, end_date)
                
                # Success rates
                success_rates = self._get_success_rates(conn, start_date, end_date)
                
                # Recent activities
                recent_activities = self._get_recent_activities(conn, limit=50)
                
                # Peak hours
                peak_hours = self._get_peak_hours(conn, start_date, end_date)
                
                return {
                    "overview": overall_metrics,
                    "query_trends": query_trends,
                    "popular_products": popular_products,
                    "location_analytics": location_analytics,
                    "performance_metrics": performance_metrics,
                    "input_methods": input_methods,
                    "success_rates": success_rates,
                    "recent_activities": recent_activities,
                    "peak_hours": peak_hours,
                    "date_range": {
                        "start": start_date.isoformat(),
                        "end": end_date.isoformat(),
                        "days": days
                    }
                }
        except Exception as e:
            logger.error(f"Failed to get dashboard metrics: {e}")
            return {}
    
    def get_recent_activities(self, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent query activities directly from the database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                return self._get_recent_activities(conn, limit)
        except Exception as e:
            logger.error(f"Failed to get recent activities: {e}")
            return []
    
    def _get_overall_metrics(self, conn, start_date, end_date) -> Dict[str, Any]:
        """Get overall metrics for the dashboard."""
        cursor = conn.cursor()
        
        # Total queries
        cursor.execute("""
            SELECT COUNT(*) FROM query_analytics 
            WHERE timestamp BETWEEN ? AND ?
        """, (start_date, end_date))
        total_queries = cursor.fetchone()[0]
        
        # Unique sessions
        cursor.execute("""
            SELECT COUNT(DISTINCT session_id) FROM query_analytics 
            WHERE timestamp BETWEEN ? AND ?
        """, (start_date, end_date))
        unique_sessions = cursor.fetchone()[0]
        
        # Average response time
        cursor.execute("""
            SELECT AVG(response_time_ms) FROM query_analytics 
            WHERE timestamp BETWEEN ? AND ? AND success = 1
        """, (start_date, end_date))
        avg_response_time = cursor.fetchone()[0] or 0
        
        # Success rate
        cursor.execute("""
            SELECT 
                COUNT(CASE WHEN success = 1 THEN 1 END) * 100.0 / COUNT(*) as success_rate
            FROM query_analytics 
            WHERE timestamp BETWEEN ? AND ?
        """, (start_date, end_date))
        success_rate = cursor.fetchone()[0] or 0
        
        # Average confidence
        cursor.execute("""
            SELECT AVG(confidence_score) FROM query_analytics 
            WHERE timestamp BETWEEN ? AND ? AND confidence_score IS NOT NULL
        """, (start_date, end_date))
        avg_confidence = cursor.fetchone()[0] or 0
        
        return {
            "total_queries": total_queries,
            "unique_sessions": unique_sessions,
            "avg_response_time": round(avg_response_time, 2),
            "success_rate": round(success_rate, 2),
            "avg_confidence": round(avg_confidence * 100, 2) if avg_confidence else 0
        }
    
    def _get_query_trends(self, conn, start_date, end_date) -> List[Dict[str, Any]]:
        """Get query trends over time."""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                DATE(timestamp) as date,
                COUNT(*) as total_queries,
                COUNT(CASE WHEN query_type = 'location' THEN 1 END) as location_queries,
                COUNT(CASE WHEN query_type = 'information' THEN 1 END) as information_queries,
                AVG(response_time_ms) as avg_response_time
            FROM query_analytics 
            WHERE timestamp BETWEEN ? AND ?
            GROUP BY DATE(timestamp)
            ORDER BY date DESC
            LIMIT 30
        """, (start_date, end_date))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def _get_popular_products(self, conn, start_date, end_date) -> List[Dict[str, Any]]:
        """Get most searched products."""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                ps.normalized_product,
                COUNT(*) as search_count,
                AVG(ps.best_match_confidence) as avg_confidence,
                COUNT(CASE WHEN ps.found = 1 THEN 1 END) as found_count,
                MAX(ps.timestamp) as last_searched
            FROM product_searches ps
            JOIN query_analytics qa ON ps.query_id = qa.id
            WHERE qa.timestamp BETWEEN ? AND ?
            GROUP BY ps.normalized_product
            ORDER BY search_count DESC
            LIMIT 20
        """, (start_date, end_date))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def _get_location_analytics(self, conn, start_date, end_date) -> Dict[str, Any]:
        """Get location-based analytics."""
        cursor = conn.cursor()
        
        # Busiest aisles
        cursor.execute("""
            SELECT 
                COALESCE(lq.aisle, 'Unknown') as aisle,
                COUNT(*) as query_count,
                AVG(lq.confidence) as avg_confidence
            FROM location_queries lq
            JOIN query_analytics qa ON lq.query_id = qa.id
            WHERE qa.timestamp BETWEEN ? AND ?
            GROUP BY lq.aisle
            ORDER BY query_count DESC
            LIMIT 10
        """, (start_date, end_date))
        busiest_aisles = [dict(row) for row in cursor.fetchall()]
        
        # Busiest bays
        cursor.execute("""
            SELECT 
                COALESCE(lq.aisle, 'Unknown') as aisle,
                COALESCE(lq.bay, 'Unknown') as bay,
                COUNT(*) as query_count
            FROM location_queries lq
            JOIN query_analytics qa ON lq.query_id = qa.id
            WHERE qa.timestamp BETWEEN ? AND ?
            GROUP BY lq.aisle, lq.bay
            ORDER BY query_count DESC
            LIMIT 15
        """, (start_date, end_date))
        busiest_bays = [dict(row) for row in cursor.fetchall()]
        
        return {
            "busiest_aisles": busiest_aisles,
            "busiest_bays": busiest_bays
        }
    
    def _get_performance_metrics(self, conn, start_date, end_date) -> Dict[str, Any]:
        """Get performance metrics."""
        cursor = conn.cursor()
        
        # Response time distribution
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN response_time_ms < 1000 THEN 'Under 1s'
                    WHEN response_time_ms < 3000 THEN '1-3s'
                    WHEN response_time_ms < 5000 THEN '3-5s'
                    WHEN response_time_ms < 10000 THEN '5-10s'
                    ELSE 'Over 10s'
                END as time_range,
                COUNT(*) as count
            FROM query_analytics 
            WHERE timestamp BETWEEN ? AND ?
            GROUP BY time_range
            ORDER BY 
                CASE time_range
                    WHEN 'Under 1s' THEN 1
                    WHEN '1-3s' THEN 2
                    WHEN '3-5s' THEN 3
                    WHEN '5-10s' THEN 4
                    ELSE 5
                END
        """, (start_date, end_date))
        response_time_distribution = [dict(row) for row in cursor.fetchall()]
        
        # Error rates by type
        cursor.execute("""
            SELECT 
                error_type,
                COUNT(*) as error_count
            FROM error_analytics 
            WHERE timestamp BETWEEN ? AND ?
            GROUP BY error_type
            ORDER BY error_count DESC
        """, (start_date, end_date))
        error_rates = [dict(row) for row in cursor.fetchall()]
        
        return {
            "response_time_distribution": response_time_distribution,
            "error_rates": error_rates
        }
    
    def _get_input_method_distribution(self, conn, start_date, end_date) -> List[Dict[str, Any]]:
        """Get input method usage distribution."""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                input_method,
                COUNT(*) as count,
                ROUND(COUNT(*) * 100.0 / (SELECT COUNT(*) FROM query_analytics WHERE timestamp BETWEEN ? AND ?), 2) as percentage,
                AVG(response_time_ms) as avg_response_time,
                AVG(confidence_score) as avg_confidence
            FROM query_analytics 
            WHERE timestamp BETWEEN ? AND ?
            GROUP BY input_method
            ORDER BY count DESC
        """, (start_date, end_date, start_date, end_date))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def _get_success_rates(self, conn, start_date, end_date) -> Dict[str, Any]:
        """Get success rates by different dimensions."""
        cursor = conn.cursor()
        
        # Success rate by query type
        cursor.execute("""
            SELECT 
                query_type,
                COUNT(*) as total,
                COUNT(CASE WHEN success = 1 THEN 1 END) as successful,
                ROUND(COUNT(CASE WHEN success = 1 THEN 1 END) * 100.0 / COUNT(*), 2) as success_rate
            FROM query_analytics 
            WHERE timestamp BETWEEN ? AND ?
            GROUP BY query_type
        """, (start_date, end_date))
        by_query_type = [dict(row) for row in cursor.fetchall()]
        
        # Success rate by input method
        cursor.execute("""
            SELECT 
                input_method,
                COUNT(*) as total,
                COUNT(CASE WHEN success = 1 THEN 1 END) as successful,
                ROUND(COUNT(CASE WHEN success = 1 THEN 1 END) * 100.0 / COUNT(*), 2) as success_rate
            FROM query_analytics 
            WHERE timestamp BETWEEN ? AND ?
            GROUP BY input_method
        """, (start_date, end_date))
        by_input_method = [dict(row) for row in cursor.fetchall()]
        
        return {
            "by_query_type": by_query_type,
            "by_input_method": by_input_method
        }
    
    def _get_recent_activities(self, conn, limit: int = 50) -> List[Dict[str, Any]]:
        """Get recent query activities."""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT DISTINCT
                qa.timestamp,
                qa.query_text,
                qa.query_type,
                qa.input_method,
                qa.response_time_ms,
                qa.confidence_score,
                qa.success,
                COALESCE(ps.normalized_product, '') as product,
                COALESCE(
                    (SELECT GROUP_CONCAT(DISTINCT lq2.aisle) 
                     FROM location_queries lq2 
                     WHERE lq2.query_id = qa.id AND lq2.aisle IS NOT NULL), 
                    ''
                ) as aisle,
                COALESCE(
                    (SELECT GROUP_CONCAT(DISTINCT lq2.bay) 
                     FROM location_queries lq2 
                     WHERE lq2.query_id = qa.id AND lq2.bay IS NOT NULL), 
                    ''
                ) as bay
            FROM query_analytics qa
            LEFT JOIN product_searches ps ON qa.id = ps.query_id
            ORDER BY qa.timestamp DESC
            LIMIT ?
        """, (limit,))
        
        # Convert rows to dictionaries manually
        columns = [description[0] for description in cursor.description]
        activities = []
        for row in cursor.fetchall():
            activity = {}
            for i, value in enumerate(row):
                activity[columns[i]] = value
            activities.append(activity)
        
        return activities
    
    def _get_peak_hours(self, conn, start_date, end_date) -> List[Dict[str, Any]]:
        """Get peak usage hours."""
        cursor = conn.cursor()
        cursor.execute("""
            SELECT 
                CAST(strftime('%H', timestamp) as INTEGER) as hour,
                COUNT(*) as query_count,
                AVG(response_time_ms) as avg_response_time
            FROM query_analytics 
            WHERE timestamp BETWEEN ? AND ?
            GROUP BY hour
            ORDER BY hour
        """, (start_date, end_date))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def _update_session_analytics(self, session_id: str, analytics: QueryAnalytics):
        """Update session analytics."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                self._update_session_analytics_with_conn(conn, session_id, analytics)
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to update session analytics: {e}")
    
    def _update_session_analytics_with_conn(self, conn, session_id: str, analytics: QueryAnalytics):
        """Update session analytics using provided connection."""
        try:
            cursor = conn.cursor()
            
            # Check if session exists
            cursor.execute("SELECT id FROM session_analytics WHERE session_id = ?", (session_id,))
            if cursor.fetchone():
                # Update existing session
                cursor.execute("""
                    UPDATE session_analytics SET
                        end_time = CURRENT_TIMESTAMP,
                        total_queries = total_queries + 1,
                        voice_queries = voice_queries + CASE WHEN ? = 'voice' THEN 1 ELSE 0 END,
                        text_queries = text_queries + CASE WHEN ? = 'text' THEN 1 ELSE 0 END,
                        vision_queries = vision_queries + CASE WHEN ? = 'vision' THEN 1 ELSE 0 END,
                        successful_queries = successful_queries + CASE WHEN ? THEN 1 ELSE 0 END
                    WHERE session_id = ?
                """, (analytics.input_method, analytics.input_method, analytics.input_method, 
                     analytics.success, session_id))
            else:
                # Create new session
                cursor.execute("""
                    INSERT INTO session_analytics 
                    (session_id, total_queries, voice_queries, text_queries, vision_queries, 
                     successful_queries, user_agent, ip_address)
                    VALUES (?, 1, ?, ?, ?, ?, ?, ?)
                """, (session_id,
                     1 if analytics.input_method == 'voice' else 0,
                     1 if analytics.input_method == 'text' else 0,
                     1 if analytics.input_method == 'vision' else 0,
                     1 if analytics.success else 0,
                     analytics.user_agent, analytics.ip_address))
        except Exception as e:
            logger.error(f"Failed to update session analytics with connection: {e}")
    
    def _update_search_trends(self, query_text: str, query_type: str):
        """Update search trends."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                self._update_search_trends_with_conn(conn, query_text, query_type)
                conn.commit()
        except Exception as e:
            logger.error(f"Failed to update search trends: {e}")
    
    def _update_search_trends_with_conn(self, conn, query_text: str, query_type: str):
        """Update search trends using provided connection."""
        try:
            # Extract key terms from query text
            terms = self._extract_search_terms(query_text)
            
            cursor = conn.cursor()
            for term in terms:
                cursor.execute("""
                    INSERT INTO search_trends (search_term, category, search_count, last_searched)
                    VALUES (?, ?, 1, CURRENT_TIMESTAMP)
                    ON CONFLICT(search_term, category) DO UPDATE SET
                        search_count = search_count + 1,
                        last_searched = CURRENT_TIMESTAMP
                """, (term, query_type))
        except Exception as e:
            logger.error(f"Failed to update search trends with connection: {e}")
    
    def _extract_search_terms(self, query_text: str) -> List[str]:
        """Extract meaningful search terms from query text."""
        # Simple extraction - can be enhanced with NLP
        stop_words = {'is', 'are', 'the', 'a', 'an', 'where', 'what', 'how', 'do', 'does', 'can', 'i', 'you'}
        words = query_text.lower().split()
        terms = [word.strip('.,!?;:') for word in words if len(word) > 2 and word.lower() not in stop_words]
        return terms[:5]  # Limit to top 5 terms
    
    def _populate_sample_data(self):
        """Populate database with realistic sample data for demonstration."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if we already have data
                cursor.execute("SELECT COUNT(*) FROM query_analytics")
                if cursor.fetchone()[0] > 0:
                    return  # Already has data
                
                logger.info("Populating analytics database with sample data...")
                
                # Sample products from the grocery database
                sample_products = [
                    "milk", "bread", "eggs", "apples", "chicken breast", "yogurt",
                    "cheese", "bananas", "ground beef", "pasta", "rice", "tomatoes",
                    "onions", "potatoes", "carrots", "broccoli", "salmon", "orange juice",
                    "butter", "cereal", "peanut butter", "jelly", "pizza", "ice cream"
                ]
                
                sample_queries = [
                    "Where is {}?", "Find {}", "Where can I find {}?", "What aisle is {} in?",
                    "What are the ingredients in {}?", "Is {} gluten free?", "How much does {} cost?",
                    "What's the nutrition information for {}?", "Is {} organic?", "Where is the {} section?"
                ]
                
                # Generate sample data for the last 30 days
                base_time = datetime.now() - timedelta(days=30)
                
                for day in range(30):
                    current_date = base_time + timedelta(days=day)
                    
                    # Generate 20-50 queries per day
                    daily_queries = random.randint(20, 50)
                    
                    for _ in range(daily_queries):
                        # Random time within the day
                        hour = random.randint(8, 22)  # Store hours
                        minute = random.randint(0, 59)
                        timestamp = current_date.replace(hour=hour, minute=minute)
                        
                        # Generate random query
                        product = random.choice(sample_products)
                        query_template = random.choice(sample_queries)
                        query_text = query_template.format(product)
                        
                        # Determine query type
                        if "where" in query_text.lower() or "aisle" in query_text.lower():
                            query_type = "location"
                        elif "ingredients" in query_text.lower() or "nutrition" in query_text.lower() or "cost" in query_text.lower():
                            query_type = "information"
                        else:
                            query_type = "general"
                        
                        # Random input method
                        input_method = random.choices(
                            ["voice", "text", "vision"],
                            weights=[50, 40, 10]
                        )[0]
                        
                        # Random performance metrics
                        response_time = random.randint(800, 5000)
                        confidence_score = random.uniform(0.7, 0.95)
                        success = random.choices([True, False], weights=[90, 10])[0]
                        
                        # Generate session ID
                        session_id = f"session_{''.join(random.choices(string.ascii_letters + string.digits, k=8))}"
                        
                        # Insert query analytics
                        cursor.execute("""
                            INSERT INTO query_analytics 
                            (session_id, timestamp, query_text, query_type, input_method, 
                             response_time_ms, confidence_score, success)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (session_id, timestamp, query_text, query_type, input_method,
                             response_time, confidence_score, success))
                        
                        query_id = cursor.lastrowid
                        
                        # Insert related data based on query type
                        if query_type == "location":
                            aisle = random.randint(1, 20)
                            bay = random.choice(['A', 'B', 'C', 'D'])
                            shelf = random.randint(1, 5)
                            
                            cursor.execute("""
                                INSERT INTO location_queries 
                                (query_id, product_name, aisle, bay, shelf, confidence)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (query_id, product, str(aisle), bay, str(shelf), confidence_score))
                        
                        # Insert product search data
                        found = random.choices([True, False], weights=[85, 15])[0]
                        match_count = random.randint(1, 5) if found else 0
                        
                        cursor.execute("""
                            INSERT INTO product_searches 
                            (query_id, normalized_product, original_product, found, 
                             match_count, best_match_confidence)
                            VALUES (?, ?, ?, ?, ?, ?)
                        """, (query_id, product.lower(), product, found, match_count, confidence_score))
                
                # Generate some performance metrics
                for day in range(30):
                    metric_date = base_time + timedelta(days=day)
                    
                    # System metrics
                    cursor.execute("""
                        INSERT INTO performance_metrics 
                        (timestamp, metric_name, metric_value, unit, category)
                        VALUES (?, ?, ?, ?, ?)
                    """, (metric_date, "avg_response_time", random.uniform(1500, 3000), "ms", "performance"))
                    
                    cursor.execute("""
                        INSERT INTO performance_metrics 
                        (timestamp, metric_name, metric_value, unit, category)
                        VALUES (?, ?, ?, ?, ?)
                    """, (metric_date, "accuracy_rate", random.uniform(85, 95), "percentage", "accuracy"))
                
                conn.commit()
                logger.info("Sample analytics data populated successfully")
                
        except Exception as e:
            logger.error(f"Failed to populate sample data: {e}")