"""Typed, pure Python functions querying the INGRES groundwater database.

Each tool function returns either a structured success dictionary:
    {"value": ..., "unit": ..., "year": ..., "location": ..., "source": ...}
or an error dictionary:
    {"error": "data_not_available"}
"""

import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from app.config import settings
from app.services.entity_resolver import resolver

INGRES_SOURCE = "INGRES (ingres.iith.ac.in) / CGWB Open Data"


def get_db_connection(db_path: Optional[Path] = None) -> sqlite3.Connection:
    """Create a SQLite connection with row factory enabled."""
    path = db_path or settings.DB_PATH
    conn = sqlite3.connect(str(path))
    conn.row_factory = sqlite3.Row
    return conn


def _get_latest_year(conn: sqlite3.Connection, location_id: int) -> Optional[int]:
    """Find the latest assessment year for a given location."""
    cursor = conn.cursor()
    cursor.execute(
        "SELECT MAX(year) as max_year FROM assessments WHERE location_id = ?",
        (location_id,),
    )
    row = cursor.fetchone()
    return row["max_year"] if row and row["max_year"] else None


def _format_location_name(loc: Dict) -> str:
    """Format canonical location string: 'District, State' or 'Block, District, State'."""
    if loc["block"] == "All":
        return f"{loc['district']}, {loc['state']}"
    return f"{loc['block']} Block, {loc['district']}, {loc['state']}"


def get_groundwater_level(
    location: str,
    year: Optional[int] = None,
    season: Optional[str] = "pre_monsoon",
    db_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Retrieve depth to groundwater level (in meters below ground level / mbgl).

    Args:
        location: Name of district, block, or city.
        year: Assessment year (e.g. 2023). Defaults to latest year.
        season: 'pre_monsoon' or 'post_monsoon'. Defaults to 'pre_monsoon'.
    """
    loc = resolver.resolve(location)
    if not loc:
        return {"error": "data_not_available"}

    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    target_year = year or _get_latest_year(conn, loc["id"])
    if not target_year:
        conn.close()
        return {"error": "data_not_available"}

    season_col = (
        "post_monsoon_water_level_mbgl"
        if season and "post" in season.lower()
        else "pre_monsoon_water_level_mbgl"
    )

    query = f"""
        SELECT {season_col} as val, year
        FROM assessments
        WHERE location_id = ? AND year = ? AND {season_col} IS NOT NULL
        LIMIT 1
    """
    cursor.execute(query, (loc["id"], target_year))
    row = cursor.fetchone()
    conn.close()

    if not row or row["val"] is None:
        return {"error": "data_not_available"}

    return {
        "value": float(row["val"]),
        "unit": "mbgl",
        "year": int(row["year"]),
        "location": _format_location_name(loc),
        "source": INGRES_SOURCE,
    }


def get_stage_of_extraction(
    location: str,
    year: Optional[int] = None,
    db_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Retrieve the Stage of Groundwater Extraction percentage (SOE %).

    SOE = (Total Annual Extraction / Annual Extractable Resource) * 100
    """
    loc = resolver.resolve(location)
    if not loc:
        return {"error": "data_not_available"}

    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    target_year = year or _get_latest_year(conn, loc["id"])
    if not target_year:
        conn.close()
        return {"error": "data_not_available"}

    query = """
        SELECT stage_of_extraction_pct as val, year
        FROM assessments
        WHERE location_id = ? AND year = ? AND stage_of_extraction_pct IS NOT NULL
        LIMIT 1
    """
    cursor.execute(query, (loc["id"], target_year))
    row = cursor.fetchone()
    conn.close()

    if not row or row["val"] is None:
        return {"error": "data_not_available"}

    return {
        "value": float(row["val"]),
        "unit": "%",
        "year": int(row["year"]),
        "location": _format_location_name(loc),
        "source": INGRES_SOURCE,
    }


def get_category(
    location: str,
    year: Optional[int] = None,
    db_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Retrieve groundwater assessment category (Safe, Semi-Critical, Critical, Over-Exploited)."""
    loc = resolver.resolve(location)
    if not loc:
        return {"error": "data_not_available"}

    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    target_year = year or _get_latest_year(conn, loc["id"])
    if not target_year:
        conn.close()
        return {"error": "data_not_available"}

    query = """
        SELECT category as val, year
        FROM assessments
        WHERE location_id = ? AND year = ? AND category IS NOT NULL
        LIMIT 1
    """
    cursor.execute(query, (loc["id"], target_year))
    row = cursor.fetchone()
    conn.close()

    if not row or not row["val"]:
        return {"error": "data_not_available"}

    return {
        "value": str(row["val"]),
        "unit": "category",
        "year": int(row["year"]),
        "location": _format_location_name(loc),
        "source": INGRES_SOURCE,
    }


def get_recharge(
    location: str,
    year: Optional[int] = None,
    db_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Retrieve Annual Extractable Groundwater Resource (in ham / hectare-meters)."""
    loc = resolver.resolve(location)
    if not loc:
        return {"error": "data_not_available"}

    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    target_year = year or _get_latest_year(conn, loc["id"])
    if not target_year:
        conn.close()
        return {"error": "data_not_available"}

    query = """
        SELECT annual_extractable_resources_ham as val, year
        FROM assessments
        WHERE location_id = ? AND year = ? AND annual_extractable_resources_ham IS NOT NULL
        LIMIT 1
    """
    cursor.execute(query, (loc["id"], target_year))
    row = cursor.fetchone()
    conn.close()

    if not row or row["val"] is None:
        return {"error": "data_not_available"}

    return {
        "value": float(row["val"]),
        "unit": "ham",
        "year": int(row["year"]),
        "location": _format_location_name(loc),
        "source": INGRES_SOURCE,
    }


def get_extraction(
    location: str,
    year: Optional[int] = None,
    usage: Optional[str] = "total",
    db_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Retrieve Current Annual Groundwater Extraction (in ham).

    Args:
        location: District, block, or city name.
        year: Assessment year. Defaults to latest.
        usage: 'total', 'irrigation', or 'domestic'. Defaults to 'total'.
    """
    loc = resolver.resolve(location)
    if not loc:
        return {"error": "data_not_available"}

    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    target_year = year or _get_latest_year(conn, loc["id"])
    if not target_year:
        conn.close()
        return {"error": "data_not_available"}

    u = (usage or "total").lower()
    if "irr" in u:
        col = "current_extraction_irrigation_ham"
    elif "dom" in u or "ind" in u:
        col = "current_extraction_domestic_ham"
    else:
        col = "current_extraction_total_ham"

    query = f"""
        SELECT {col} as val, year
        FROM assessments
        WHERE location_id = ? AND year = ? AND {col} IS NOT NULL
        LIMIT 1
    """
    cursor.execute(query, (loc["id"], target_year))
    row = cursor.fetchone()
    conn.close()

    if not row or row["val"] is None:
        return {"error": "data_not_available"}

    return {
        "value": float(row["val"]),
        "unit": "ham",
        "year": int(row["year"]),
        "location": _format_location_name(loc),
        "source": INGRES_SOURCE,
    }


def compare_locations(
    locations: List[str],
    metric: str,
    year: Optional[int] = None,
    db_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Compare a groundwater metric across multiple locations."""
    if not locations:
        return {"error": "data_not_available"}

    metric_lower = metric.lower()
    results = []
    unit = ""
    resolved_year = year

    for loc_str in locations:
        res = None
        if "stage" in metric_lower or "soe" in metric_lower or "%" in metric_lower or "extract" in metric_lower and "pct" in metric_lower:
            res = get_stage_of_extraction(loc_str, year, db_path)
        elif "cat" in metric_lower or "status" in metric_lower:
            res = get_category(loc_str, year, db_path)
        elif "level" in metric_lower or "depth" in metric_lower or "mbgl" in metric_lower:
            season = "post_monsoon" if "post" in metric_lower else "pre_monsoon"
            res = get_groundwater_level(loc_str, year, season, db_path)
        elif "recharge" in metric_lower or "resource" in metric_lower:
            res = get_recharge(loc_str, year, db_path)
        else:
            res = get_extraction(loc_str, year, "total", db_path)

        if "error" not in res:
            unit = res["unit"]
            resolved_year = res["year"]
            results.append({
                "location": res["location"],
                "value": res["value"],
            })

    if not results:
        return {"error": "data_not_available"}

    return {
        "value": results,
        "unit": unit,
        "year": resolved_year,
        "location": ", ".join([r["location"] for r in results]),
        "source": INGRES_SOURCE,
    }


def get_trend(
    location: str,
    metric: str,
    start_year: Optional[int] = None,
    end_year: Optional[int] = None,
    db_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Retrieve multi-year historical trend for a metric at a specific location."""
    loc = resolver.resolve(location)
    if not loc:
        return {"error": "data_not_available"}

    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    metric_lower = metric.lower()
    if "stage" in metric_lower or "soe" in metric_lower or "%" in metric_lower:
        col = "stage_of_extraction_pct"
        unit = "%"
    elif "post" in metric_lower:
        col = "post_monsoon_water_level_mbgl"
        unit = "mbgl"
    elif "level" in metric_lower or "depth" in metric_lower or "mbgl" in metric_lower:
        col = "pre_monsoon_water_level_mbgl"
        unit = "mbgl"
    elif "recharge" in metric_lower:
        col = "annual_extractable_resources_ham"
        unit = "ham"
    else:
        col = "current_extraction_total_ham"
        unit = "ham"

    query = f"""
        SELECT year, {col} as val
        FROM assessments
        WHERE location_id = ? AND {col} IS NOT NULL
        ORDER BY year ASC
    """
    cursor.execute(query, (loc["id"],))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return {"error": "data_not_available"}

    filtered_points = []
    for r in rows:
        yr = int(r["year"])
        if start_year and yr < start_year:
            continue
        if end_year and yr > end_year:
            continue
        filtered_points.append({"year": yr, "value": float(r["val"])})

    if len(filtered_points) == 0:
        return {"error": "data_not_available"}

    delta = None
    direction = "stable"
    if len(filtered_points) >= 2:
        delta = round(filtered_points[-1]["value"] - filtered_points[0]["value"], 2)
        if delta > 0.05:
            direction = "increasing"
        elif delta < -0.05:
            direction = "decreasing"

    year_label = f"{filtered_points[0]['year']}-{filtered_points[-1]['year']}" if len(filtered_points) > 1 else str(filtered_points[0]["year"])

    return {
        "value": filtered_points,
        "unit": unit,
        "year": year_label,
        "location": _format_location_name(loc),
        "source": INGRES_SOURCE,
        "delta": delta,
        "direction": direction,
    }


def rank_locations(
    locations: List[str],
    metric: str,
    year: Optional[int] = None,
    ascending: bool = False,
    db_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """Rank given locations by a specific metric."""
    comp = compare_locations(locations, metric, year, db_path)
    if "error" in comp:
        return comp

    items = comp["value"]
    # Filter only numeric values for sorting
    numeric_items = [it for it in items if isinstance(it["value"], (int, float))]
    if not numeric_items:
        return {"error": "data_not_available"}

    sorted_items = sorted(numeric_items, key=lambda x: x["value"], reverse=not ascending)
    ranked = [
        {"rank": idx + 1, "location": it["location"], "value": it["value"]}
        for idx, it in enumerate(sorted_items)
    ]

    return {
        "value": ranked,
        "unit": comp["unit"],
        "year": comp["year"],
        "location": comp["location"],
        "source": INGRES_SOURCE,
        "rank_order": "ascending" if ascending else "descending",
    }


def list_blocks(
    district: str,
    category: Optional[str] = None,
    year: Optional[int] = None,
    db_path: Optional[Path] = None,
) -> Dict[str, Any]:
    """List all assessment blocks in a district, optionally filtered by category.

    Args:
        district: Name of the district.
        category: Optional filter (e.g. 'Over-Exploited', 'Critical', 'Safe', 'Semi-Critical').
        year: Assessment year.
    """
    loc = resolver.resolve(district)
    if not loc:
        return {"error": "data_not_available"}

    conn = get_db_connection(db_path)
    cursor = conn.cursor()

    target_year = year or 2023

    # Query all blocks for this district (excluding 'All')
    query = """
        SELECT l.block, l.district, l.state, a.category, a.stage_of_extraction_pct,
               a.pre_monsoon_water_level_mbgl, a.post_monsoon_water_level_mbgl, a.year
        FROM locations l
        LEFT JOIN assessments a ON l.id = a.location_id AND a.year = ?
        WHERE l.district = ? AND l.block != 'All'
        ORDER BY l.block ASC
    """
    cursor.execute(query, (target_year, loc["district"]))
    rows = cursor.fetchall()
    conn.close()

    if not rows:
        return {"error": "data_not_available"}

    blocks = []
    category_filter = category.lower().strip() if category else None

    for r in rows:
        cat = r["category"]
        if category_filter:
            if not cat or category_filter not in cat.lower():
                continue
        blocks.append({
            "block": r["block"],
            "district": r["district"],
            "state": r["state"],
            "category": cat,
            "stage_of_extraction_pct": float(r["stage_of_extraction_pct"]) if r["stage_of_extraction_pct"] is not None else None,
            "pre_monsoon_water_level_mbgl": float(r["pre_monsoon_water_level_mbgl"]) if r["pre_monsoon_water_level_mbgl"] is not None else None,
            "post_monsoon_water_level_mbgl": float(r["post_monsoon_water_level_mbgl"]) if r["post_monsoon_water_level_mbgl"] is not None else None,
        })

    if not blocks:
        return {"error": "data_not_available"}

    return {
        "value": blocks,
        "unit": "blocks",
        "year": target_year,
        "location": f"{loc['district']}, {loc['state']}",
        "source": INGRES_SOURCE,
        "total_count": len(blocks),
    }
