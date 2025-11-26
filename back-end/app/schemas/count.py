# back-end/app/schemas/count.py

from pydantic import BaseModel, Field
from typing import List, Any, Optional
from datetime import datetime

class CountResponse(BaseModel):
    """Schema for a single count record."""
    id: int
    timestamp: datetime

class StatisticsResponse(BaseModel):
    """Schema for aggregated count statistics."""
    total_counts: int
    counts_today: int
    last_count_timestamp: Optional[datetime] = None
    query_timestamp: datetime = Field(default_factory=datetime.now)

class GrafanaTimeSeriesDatapoint(BaseModel):
    """
    Represents a single datapoint for Grafana's simple-json-datasource.
    Format: [value, timestamp_in_ms]
    """
    value: float
    timestamp: int

    def to_list(self) -> List[Any]:
        return [self.value, self.timestamp]

class GrafanaTimeSeriesResponse(BaseModel):
    """Schema for Grafana time series queries."""
    target: str
    datapoints: List[List[Any]] # List of [value, timestamp_ms]