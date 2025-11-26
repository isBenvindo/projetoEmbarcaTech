# back-end/app/api/routes/counts.py

import logging
from fastapi import APIRouter, Depends, HTTPException, Query
from psycopg2.extensions import connection
from psycopg2.extras import RealDictCursor

from app.db.session import db_dependency
from app.schemas.count import CountResponse, StatisticsResponse, GrafanaTimeSeriesResponse

router = APIRouter()
logger = logging.getLogger(__name__)

# =====================================================================
# Standard API Endpoints
# =====================================================================

@router.get("/counts", response_model=list[CountResponse])
async def get_counts(
    db: connection = Depends(db_dependency),
    limit: int = Query(100, le=1000),
    offset: int = Query(0)
):
    """Retrieves a paginated list of all pizza counts."""
    try:
        with db.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(
                "SELECT id, timestamp FROM pizza_counts ORDER BY timestamp DESC LIMIT %s OFFSET %s",
                (limit, offset)
            )
            results = cur.fetchall()
        return results
    except Exception as e:
        logger.error(f"Error fetching counts: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch counts.")

@router.get("/counts/statistics", response_model=StatisticsResponse)
async def get_statistics(db: connection = Depends(db_dependency)):
    """Retrieves aggregated statistics about the counts."""
    try:
        with db.cursor() as cur:
            # Total counts
            cur.execute("SELECT COUNT(*) FROM pizza_counts")
            total_counts = cur.fetchone()[0]

            # Counts today
            cur.execute(
                "SELECT COUNT(*) FROM pizza_counts WHERE DATE(timestamp) = CURRENT_DATE"
            )
            counts_today = cur.fetchone()[0]

            # Last count timestamp
            cur.execute(
                "SELECT timestamp FROM pizza_counts ORDER BY timestamp DESC LIMIT 1"
            )
            last_count_row = cur.fetchone()
            last_count_timestamp = last_count_row[0] if last_count_row else None

            return StatisticsResponse(
                total_counts=total_counts,
                counts_today=counts_today,
                last_count_timestamp=last_count_timestamp
            )
    except Exception as e:
        logger.error(f"Error fetching statistics: {e}")
        raise HTTPException(status_code=500, detail="Failed to fetch statistics.")

# =====================================================================
# Grafana API Endpoints (for simple-json-datasource)
# =====================================================================
# Note: Grafana expects datapoints as [value, timestamp_in_milliseconds]

async def _fetch_grafana_timeseries(db: connection, view_name: str, target_name: str, value_column: str, days_limit: int = 30):
    """Generic helper to fetch time series data from a database view."""
    try:
        with db.cursor() as cur:
            # Ensure column names are safe before embedding in the query
            if not (view_name.isalnum() and value_column.isalnum()):
                raise ValueError("Invalid view or column name")

            query = f"""
                SELECT 
                    {value_column} AS value,
                    timestamp_unix * 1000 AS ts_ms 
                FROM {view_name}
                WHERE timestamp_unix >= EXTRACT(EPOCH FROM (CURRENT_DATE - INTERVAL '%s days'))
                ORDER BY ts_ms
            """
            cur.execute(query, (days_limit,))
            results = cur.fetchall()
            
            datapoints = [[row[0], int(row[1])] for row in results]
            
            return [GrafanaTimeSeriesResponse(target=target_name, datapoints=datapoints)]
            
    except Exception as e:
        logger.error(f"Error fetching Grafana data from view '{view_name}': {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch data for {target_name}")

@router.get("/grafana", response_model=dict)
async def grafana_root():
    """Root endpoint for Grafana datasource to confirm connectivity."""
    return {"status": "ok"}

@router.get("/grafana/search", response_model=list[str])
async def grafana_search():
    """Provides a list of available metrics for Grafana variables."""
    return [
        "hourly_counts",
        "daily_counts",
        "production_speed",
        "today_stats_table", # For table panels
        "recent_counts"      # For time series
    ]

@router.post("/grafana/query", response_model=list)
async def grafana_query(request: dict, db: connection = Depends(db_dependency)):
    """
    Main query endpoint for Grafana.
    It receives targets from a dashboard and returns the corresponding data.
    """
    target = request.get("targets", [{}])[0].get("target")
    logger.info(f"Grafana query received for target: {target}")

    if not target:
        return []

    if target == "hourly_counts":
        return await _fetch_grafana_timeseries(db, "hourly_counts", "Pizzas per Hour", "total_counts", days_limit=7)
    
    if target == "daily_counts":
        return await _fetch_grafana_timeseries(db, "daily_counts", "Pizzas per Day", "total_counts", days_limit=365)

    if target == "production_speed":
        return await _fetch_grafana_timeseries(db, "production_speed", "Production Speed (pizzas/h)", "pizzas_per_hour", days_limit=2)

    if target == "recent_counts":
        return await _fetch_grafana_timeseries(db, "recent_counts_24h", "Real-time Counts", "id", days_limit=1) # Value is not used here, just the timestamp matters

    if target == "today_stats_table":
        try:
            with db.cursor(cursor_factory=RealDictCursor) as cur:
                cur.execute("SELECT * FROM today_stats LIMIT 1")
                stats = cur.fetchone() or {}
                return [{
                    "type": "table",
                    "columns": [
                        {"text": "Total Counts Today", "type": "number"},
                        {"text": "First Count Time", "type": "string"},
                        {"text": "Last Count Time", "type": "string"},
                    ],
                    "rows": [
                        [
                            stats.get("total_counts", 0),
                            str(stats.get("first_count_time", "N/A")),
                            str(stats.get("last_count_time", "N/A")),
                        ]
                    ]
                }]
        except Exception as e:
            logger.error(f"Error fetching Grafana table data for 'today_stats': {e}")
            raise HTTPException(status_code=500, detail="Failed to fetch table data")
    
    return []