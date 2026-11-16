#!/usr/bin/env python3
"""INGRES Open Data Ingestion & Inspection Script.

Usage:
    # 1. Inspect raw files and print sample rows:
    python scripts/ingest.py --inspect

    # 2. Ingest and load into SQLite once schema is confirmed:
    python scripts/ingest.py --load

    # 3. Print validation report on existing SQLite database:
    python scripts/ingest.py --report
"""

import argparse
import os
import re
import sqlite3
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

# Paths
SCRIPT_DIR = Path(__file__).resolve().parent
BACKEND_DIR = SCRIPT_DIR.parent
RAW_DATA_DIR = BACKEND_DIR / "data" / "raw"
DEFAULT_DB_PATH = BACKEND_DIR / "data" / "ingres.db"


def to_snake_case(col_name: str) -> str:
    """Normalize arbitrary header text to clean snake_case."""
    # Replace unit indicators and special symbols
    s = col_name.strip()
    s = re.sub(r"[%\(\)\[\]/\\,\.\-\:]+", " ", s)
    s = re.sub(r"\s+", "_", s)
    s = re.sub(r"[^a-zA-Z0-9_]", "", s)
    s = re.sub(r"_+", "_", s)
    return s.strip("_").lower()


def clean_name(val: Any) -> Optional[str]:
    """Clean and title-case state/district/block names."""
    if pd.isna(val):
        return None
    s = str(val).strip()
    if not s or s.lower() in ("nan", "none", "null", "-", "nil"):
        return None
    # Normalize multiple whitespaces
    s = re.sub(r"\s+", " ", s)
    return s.title()


def find_raw_files(raw_dir: Path) -> List[Path]:
    """Find all CSV and Excel files in the raw data directory."""
    patterns = ["*.csv", "*.xlsx", "*.xls"]
    files: List[Path] = []
    for pattern in patterns:
        files.extend(raw_dir.glob(pattern))
    return sorted(files)


def load_file_dataframe(file_path: Path) -> pd.DataFrame:
    """Load CSV or Excel file into pandas DataFrame."""
    suffix = file_path.suffix.lower()
    if suffix == ".csv":
        # Try UTF-8 with automatic fallback for regional encodings
        for encoding in ["utf-8", "utf-8-sig", "latin1", "cp1252"]:
            try:
                return pd.read_csv(file_path, encoding=encoding)
            except UnicodeDecodeError:
                continue
        return pd.read_csv(file_path, encoding="utf-8", errors="replace")
    elif suffix in (".xlsx", ".xls"):
        return pd.read_excel(file_path)
    else:
        raise ValueError(f"Unsupported file format: {file_path}")


def inspect_files(raw_dir: Path) -> Dict[str, Any]:
    """Step 1: Inspect files in raw_dir and print column names & sample rows."""
    files = find_raw_files(raw_dir)
    print("=" * 80)
    print("INGRES RAW DATA INSPECTION")
    print("=" * 80)
    print(f"Inspection Directory: {raw_dir.resolve()}")
    print(f"Files Detected      : {len(files)}")

    if not files:
        print("\n[!] No files found in backend/data/raw/.")
        print("    Please drop your INGRES CSV/Excel files into:")
        print(f"    -> {raw_dir.resolve()}")
        print("\nSupported formats: .csv, .xlsx, .xls")
        return {"files": []}

    inspection_results = {}
    for idx, f in enumerate(files, 1):
        print("\n" + "-" * 80)
        print(f"[{idx}/{len(files)}] File: {f.name} (Size: {f.stat().st_size / 1024:.1f} KB)")
        try:
            df = load_file_dataframe(f)
            original_cols = list(df.columns)
            normalized_cols = [to_snake_case(c) for c in original_cols]

            print(f"Total Rows: {len(df):,} | Total Columns: {len(original_cols)}")
            print("\nOriginal vs Normalized Columns:")
            for orig, norm in zip(original_cols, normalized_cols):
                sample_val = df[orig].dropna().iloc[0] if not df[orig].dropna().empty else "ALL_NULL"
                print(f"  • {orig!r:<40} -> {norm:<35} (e.g. {sample_val!r})")

            print("\nSample Rows (First 3):")
            sample_df = df.head(3).copy()
            # Truncate long string values for clean display
            pd.set_option("display.max_columns", None)
            pd.set_option("display.width", 120)
            pd.set_option("display.max_colwidth", 25)
            print(sample_df.to_string(index=False))

            inspection_results[f.name] = {
                "path": str(f),
                "rows": len(df),
                "columns": original_cols,
                "normalized_columns": normalized_cols,
            }
        except Exception as e:
            print(f"  [ERROR] Failed to read {f.name}: {e}")

    print("\n" + "=" * 80)
    print("INSPECTION SUMMARY & SCHEMA PROPOSAL READY")
    print("=" * 80)
    return inspection_results


def identify_key_columns(columns: List[str]) -> Dict[str, Optional[str]]:
    """Heuristic identification of state, district, block, and year columns."""
    norm_to_orig = {to_snake_case(c): c for c in columns}
    keys = {
        "state": None,
        "district": None,
        "block": None,
        "year": None,
    }
    for norm, orig in norm_to_orig.items():
        if not keys["state"] and any(k in norm for k in ["state_name", "state", "st_name"]):
            keys["state"] = orig
        elif not keys["district"] and any(k in norm for k in ["district_name", "district", "dist_name", "dist"]):
            keys["district"] = orig
        elif not keys["block"] and any(k in norm for k in ["block_name", "block", "tehsil", "taluk", "assessment_unit"]):
            keys["block"] = orig
        elif not keys["year"] and any(k in norm for k in ["year", "assessment_year", "period"]):
            keys["year"] = orig
    return keys


def init_database(db_path: Path, dynamic_assessment_cols: List[str]) -> sqlite3.Connection:
    """Initialize SQLite database with locations, assessments, and name_aliases tables."""
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # 1. Locations Table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS locations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            state TEXT NOT NULL,
            district TEXT NOT NULL,
            block TEXT NOT NULL DEFAULT 'All',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(state, district, block)
        );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_loc_state ON locations(state);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_loc_district ON locations(district);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_loc_block ON locations(block);")

    # 2. Dynamic Assessments Table
    # Start with base columns, then add dynamic metric columns from raw files
    base_cols = [
        "id INTEGER PRIMARY KEY AUTOINCREMENT",
        "location_id INTEGER NOT NULL",
        "year INTEGER",
        "source_file TEXT",
    ]
    
    # Filter out location and year keys from dynamic metrics
    filtered_metric_cols = [
        col for col in dynamic_assessment_cols
        if col not in ("id", "location_id", "year", "source_file", "state", "district", "block")
    ]
    
    metric_definitions = [f"{col} REAL" if not col.endswith(("_category", "_status", "_type", "_name")) else f"{col} TEXT" for col in filtered_metric_cols]
    
    all_col_defs = base_cols + metric_definitions + [
        "FOREIGN KEY(location_id) REFERENCES locations(id)",
        "UNIQUE(location_id, year, source_file)"
    ]
    
    create_assessments_sql = f"""
        CREATE TABLE IF NOT EXISTS assessments (
            {', '.join(all_col_defs)}
        );
    """
    cursor.execute(create_assessments_sql)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_assess_loc ON assessments(location_id);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_assess_year ON assessments(year);")

    # 3. Name Aliases Table (for fuzzy match & synonyms)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS name_aliases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            canonical_name TEXT NOT NULL,
            alias_name TEXT NOT NULL,
            entity_type TEXT NOT NULL, -- 'state', 'district', 'block'
            location_id INTEGER,
            FOREIGN KEY(location_id) REFERENCES locations(id)
        );
    """)
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_alias_canonical ON name_aliases(canonical_name);")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_alias_name ON name_aliases(alias_name);")

    conn.commit()
    return conn


def load_data_into_db(raw_dir: Path, db_path: Path):
    """Step 2 & 3: Normalize, clean, and load raw data into SQLite."""
    files = find_raw_files(raw_dir)
    if not files:
        print("[!] No files found to load in backend/data/raw/.")
        return

    print("\nStarting Ingestion Pipeline...")
    # First pass: collect all dynamic columns
    all_normalized_cols = set()
    file_dfs = []

    for f in files:
        df = load_file_dataframe(f)
        col_map = {orig: to_snake_case(orig) for orig in df.columns}
        df_norm = df.rename(columns=col_map)
        all_normalized_cols.update(df_norm.columns)
        file_dfs.append((f.name, df, df_norm))

    # Initialize SQLite database
    conn = init_database(db_path, sorted(list(all_normalized_cols)))
    cursor = conn.cursor()

    total_locations_added = 0
    total_assessments_added = 0
    aliases_added = 0

    for filename, orig_df, df in file_dfs:
        print(f"\nProcessing {filename} ({len(df):,} rows)...")
        key_cols = identify_key_columns(list(orig_df.columns))
        state_col = to_snake_case(key_cols["state"]) if key_cols["state"] else None
        dist_col = to_snake_case(key_cols["district"]) if key_cols["district"] else None
        block_col = to_snake_case(key_cols["block"]) if key_cols["block"] else None
        year_col = to_snake_case(key_cols["year"]) if key_cols["year"] else None

        for _, row in df.iterrows():
            state = clean_name(row[state_col]) if state_col and state_col in row else "Unknown State"
            district = clean_name(row[dist_col]) if dist_col and dist_col in row else "Unknown District"
            block = clean_name(row[block_col]) if block_col and block_col in row else "All"

            if not state or not district:
                continue

            # Insert or get location
            cursor.execute("""
                INSERT OR IGNORE INTO locations (state, district, block)
                VALUES (?, ?, ?)
            """, (state, district, block))
            if cursor.rowcount > 0:
                total_locations_added += 1

            cursor.execute("""
                SELECT id FROM locations WHERE state = ? AND district = ? AND block = ?
            """, (state, district, block))
            loc_id = cursor.fetchone()[0]

            # Populate default alias (original to title-cased)
            cursor.execute("""
                INSERT OR IGNORE INTO name_aliases (canonical_name, alias_name, entity_type, location_id)
                VALUES (?, ?, 'district', ?)
            """, (district, district.lower(), loc_id))

            # Assessment data
            year = None
            if year_col and year_col in row and not pd.isna(row[year_col]):
                # Parse year if formatted like '2022-23' or '2023'
                year_match = re.search(r"(\d{4})", str(row[year_col]))
                if year_match:
                    year = int(year_match.group(1))

            # Prepare dynamic columns insert
            metric_data = {}
            for col in df.columns:
                if col not in (state_col, dist_col, block_col, year_col):
                    val = row[col]
                    if pd.isna(val):
                        continue
                    # Convert to float if numeric
                    try:
                        metric_data[col] = float(val)
                    except (ValueError, TypeError):
                        metric_data[col] = str(val).strip()

            cols = ["location_id", "year", "source_file"] + list(metric_data.keys())
            placeholders = ["?"] * len(cols)
            values = [loc_id, year, filename] + list(metric_data.values())

            update_clause = ", ".join([f"{c}=excluded.{c}" for c in metric_data.keys()])
            sql = f"""
                INSERT INTO assessments ({', '.join(cols)})
                VALUES ({', '.join(placeholders)})
                ON CONFLICT(location_id, year, source_file) DO UPDATE SET
                {update_clause if update_clause else 'year=excluded.year'}
            """
            try:
                cursor.execute(sql, values)
                total_assessments_added += 1
            except Exception as e:
                pass

        conn.commit()

    print(f"\n[✓] Ingestion Complete!")
    print(f"    - Unique Locations Inserted: {total_locations_added}")
    print(f"    - Assessment Records Added : {total_assessments_added}")
    conn.close()


def print_validation_report(db_path: Path):
    """Step 4: Print validation report (row counts, null %, years, states)."""
    if not db_path.exists():
        print(f"[!] Database file does not exist: {db_path}")
        return

    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    print("=" * 80)
    print("INGRES DATABASE VALIDATION REPORT")
    print("=" * 80)
    print(f"Database Path: {db_path.resolve()}")

    # Table row counts
    tables = ["locations", "assessments", "name_aliases"]
    print("\n1. Table Summary:")
    for t in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {t}")
            cnt = cursor.fetchone()[0]
            print(f"   • {t:<15}: {cnt:,} rows")
        except sqlite3.OperationalError:
            print(f"   • {t:<15}: NOT FOUND")

    # States covered
    print("\n2. Geographic Coverage:")
    cursor.execute("SELECT COUNT(DISTINCT state), COUNT(DISTINCT district), COUNT(DISTINCT block) FROM locations")
    num_states, num_districts, num_blocks = cursor.fetchone()
    print(f"   • States Covered    : {num_states}")
    print(f"   • Districts Covered : {num_districts}")
    print(f"   • Blocks Covered    : {num_blocks}")

    cursor.execute("SELECT state, COUNT(DISTINCT district) FROM locations GROUP BY state ORDER BY 2 DESC LIMIT 10")
    print("\n   Top States by Districts Count:")
    for st, d_count in cursor.fetchall():
        print(f"     - {st:<25}: {d_count} districts")

    # Years covered
    print("\n3. Temporal Coverage:")
    cursor.execute("SELECT DISTINCT year FROM assessments WHERE year IS NOT NULL ORDER BY year")
    years = [str(r[0]) for r in cursor.fetchall()]
    print(f"   • Years Available: {', '.join(years) if years else 'None specified'}")

    # Null analysis on assessments
    cursor.execute("PRAGMA table_info(assessments)")
    columns = [row[1] for row in cursor.fetchall()]

    cursor.execute("SELECT COUNT(*) FROM assessments")
    total_assess = cursor.fetchone()[0]

    if total_assess > 0:
        print(f"\n4. Field Completeness & Null Analysis (Total Assessments = {total_assess:,}):")
        print(f"   {'Column Name':<35} | {'Null Count':<12} | {'Null %':<8}")
        print("   " + "-" * 60)
        for col in columns:
            cursor.execute(f"SELECT COUNT(*) FROM assessments WHERE {col} IS NULL")
            null_count = cursor.fetchone()[0]
            null_pct = (null_count / total_assess) * 100
            print(f"   {col:<35} | {null_count:<12,} | {null_pct:>6.1f}%")

    print("\n" + "=" * 80)
    conn.close()


def main():
    parser = argparse.ArgumentParser(description="INGRES Open Data Ingestion & Inspection Script")
    parser.add_argument("--inspect", action="store_true", help="Inspect raw files in backend/data/raw/")
    parser.add_argument("--load", action="store_true", help="Load normalized data into SQLite database")
    parser.add_argument("--report", action="store_true", help="Print validation report of the SQLite database")
    parser.add_argument("--raw-dir", type=Path, default=RAW_DATA_DIR, help="Custom raw data folder path")
    parser.add_argument("--db-path", type=Path, default=DEFAULT_DB_PATH, help="Target SQLite database path")

    args = parser.parse_args()

    # If no flags are given, inspect by default
    if not (args.inspect or args.load or args.report):
        args.inspect = True

    if args.inspect:
        inspect_files(args.raw_dir)

    if args.load:
        load_data_into_db(args.raw_dir, args.db_path)
        print_validation_report(args.db_path)

    if args.report and not args.load:
        print_validation_report(args.db_path)


if __name__ == "__main__":
    main()
