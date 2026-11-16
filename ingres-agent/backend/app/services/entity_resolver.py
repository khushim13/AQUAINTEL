"""Entity resolution and fuzzy matching for geographic locations in INGRES."""

import re
import sqlite3
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from rapidfuzz import fuzz, process

from app.config import settings

# Common geographical aliases in India
COMMON_ALIASES: Dict[str, str] = {
    "bangalore": "Bengaluru Urban",
    "bengaluru": "Bengaluru Urban",
    "bangalore urban": "Bengaluru Urban",
    "gurgaon": "Gurugram",
    "bombay": "Mumbai",
    "madras": "Chennai",
    "calcutta": "Kolkata",
    "pondicherry": "Puducherry",
    "orissa": "Odisha",
    "baroda": "Vadodara",
    "trivandrum": "Thiruvananthapuram",
    "cochin": "Kochi",
    "banaras": "Varanasi",
    "kashi": "Varanasi",
    "mysore": "Mysuru",
}


def clean_query_string(query: str) -> str:
    """Strip common boilerplate like 'district', 'block', 'state'."""
    q = query.lower().strip()
    q = re.sub(r"\b(district|dist|block|tehsil|taluka|state|city|town)\b", "", q)
    q = re.sub(r"\s+", " ", q).strip()
    return q


class EntityResolver:
    """Resolves arbitrary user input strings to canonical database locations."""

    def __init__(self, db_path: Optional[Path] = None):
        self.db_path = db_path or settings.DB_PATH
        self._cache_locations()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def _cache_locations(self):
        """Preload location names into memory for ultra-fast fuzzy matching."""
        self.location_records: List[Dict] = []
        self.search_entries: List[Tuple[str, Dict]] = []

        if not self.db_path.exists():
            return

        conn = self._get_connection()
        cursor = conn.cursor()

        # Load all locations
        cursor.execute("SELECT id, state, district, block FROM locations")
        rows = cursor.fetchall()
        for r in rows:
            rec = {
                "id": r["id"],
                "state": r["state"],
                "district": r["district"],
                "block": r["block"],
            }
            self.location_records.append(rec)
            
            # Index standalone names as well as composite names
            if r["block"] == "All":
                self.search_entries.append((r["district"].lower(), rec))
                self.search_entries.append((f"{r['district']} {r['state']}".lower(), rec))
            else:
                self.search_entries.append((r["block"].lower(), rec))
                self.search_entries.append((f"{r['block']} {r['district']}".lower(), rec))
                self.search_entries.append((f"{r['block']} {r['district']} {r['state']}".lower(), rec))

        conn.close()

    def resolve(self, query: str) -> Optional[Dict]:
        """Resolve a location query to the best-matching database record.

        Returns:
            Dict with keys: id, state, district, block, score
            or None if no confident match.
        """
        if not self.search_entries:
            self._cache_locations()
            if not self.search_entries:
                return None

        cleaned = clean_query_string(query)
        if not cleaned:
            return None

        # 1. Direct alias dictionary check
        if cleaned in COMMON_ALIASES:
            cleaned = COMMON_ALIASES[cleaned].lower()

        # 2. Exact match check
        for name_str, rec in self.search_entries:
            if name_str == cleaned:
                return {**rec, "score": 100.0}

        # 3. Fuzzy search using RapidFuzz WRatio
        candidate_strings = [name_str for name_str, _ in self.search_entries]
        match = process.extractOne(
            cleaned,
            candidate_strings,
            scorer=fuzz.WRatio,
            score_cutoff=68.0,
        )

        if match:
            matched_str, score, idx = match
            matched_rec = self.search_entries[idx][1]
            return {**matched_rec, "score": score}

        return None


# Global singleton instance
resolver = EntityResolver()
