"""Pydantic schemas for INGRES-Agent tools and API endpoints."""

from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field


class ToolResult(BaseModel):
    """Standard success result returned by DB functions."""
    value: Any = Field(..., description="The quantitative or categorical metric value")
    unit: str = Field(..., description="Measurement unit (e.g., 'mbgl', '%', 'ham', 'category')")
    year: Optional[Union[int, str]] = Field(None, description="Assessment year or period")
    location: str = Field(..., description="Canonical location name (District, State, or Block)")
    source: str = Field(
        default="INGRES (ingres.iith.ac.in) / CGWB Open Data",
        description="Data origin and provenance reference",
    )


class ToolError(BaseModel):
    """Standard error result when data cannot be found or matched."""
    error: str = Field(default="data_not_available", description="Error type indicator")
    detail: Optional[str] = Field(None, description="Descriptive reason for unavailable data")


class BlockDetail(BaseModel):
    """Details of a single assessment unit / block."""
    block: str
    district: str
    state: str
    category: Optional[str] = None
    stage_of_extraction_pct: Optional[float] = None
    pre_monsoon_water_level_mbgl: Optional[float] = None
    post_monsoon_water_level_mbgl: Optional[float] = None


class ListBlocksResult(BaseModel):
    """Result schema for list_blocks tool."""
    value: List[Dict[str, Any]] = Field(..., description="List of blocks with their details")
    unit: str = Field(default="blocks", description="Unit")
    year: Optional[Union[int, str]] = Field(None, description="Assessment year")
    location: str = Field(..., description="District or Region queried")
    source: str = Field(
        default="INGRES (ingres.iith.ac.in) / CGWB Open Data",
        description="Data origin reference",
    )
    total_count: int = Field(..., description="Total blocks matching the criteria")


class TrendPoint(BaseModel):
    year: int
    value: float


class TrendResult(BaseModel):
    """Result schema for get_trend tool."""
    value: List[Dict[str, Any]] = Field(..., description="Year-over-year metric points")
    unit: str
    year: str = Field(..., description="Time range (e.g. '2021-2023')")
    location: str
    source: str = Field(default="INGRES (ingres.iith.ac.in) / CGWB Open Data")
    delta: Optional[float] = Field(None, description="Net change over the period")
    direction: Optional[str] = Field(None, description="'increasing', 'decreasing', or 'stable'")


class ComparisonItem(BaseModel):
    location: str
    value: Any
    category: Optional[str] = None


class CompareLocationsResult(BaseModel):
    """Result schema for compare_locations tool."""
    value: List[Dict[str, Any]] = Field(..., description="Compared values per location")
    unit: str
    year: Optional[int] = None
    location: str = Field(..., description="Comma-separated compared locations")
    source: str = Field(default="INGRES (ingres.iith.ac.in) / CGWB Open Data")


class RankLocationsResult(BaseModel):
    """Result schema for rank_locations tool."""
    value: List[Dict[str, Any]] = Field(..., description="Ordered list of locations with rankings")
    unit: str
    year: Optional[int] = None
    location: str
    source: str = Field(default="INGRES (ingres.iith.ac.in) / CGWB Open Data")
    rank_order: str = Field(default="descending")
