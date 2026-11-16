"""Entity resolution module for geographic names in the INGRES database.

Uses RapidFuzz to resolve user-entered state, district, and block names
to canonical database entities with confidence scores and ambiguity detection.
"""

import re
import sqlite3
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union
from pydantic import BaseModel, Field
from rapidfuzz import fuzz, process

from app.config import settings

# Geographic aliases mapping colloquial / historical names to canonical names
GEOGRAPHIC_ALIASES: Dict[str, str] = {
    "bangalore": "Bengaluru Urban",
    "banglore": "Bengaluru Urban",
    "bengaluru": "Bengaluru Urban",
    "bangalore urban": "Bengaluru Urban",
    "bombay": "Mumbai",
    "madras": "Chennai",
    "calcutta": "Kolkata",
    "kolkatta": "Kolkata",
    "banaras": "Varanasi",
    "benares": "Varanasi",
    "kashi": "Varanasi",
    "mysore": "Mysuru",
    "gurgaon": "Gurugram",
    "poona": "Pune",
    "orissa": "Odisha",
    "pondicherry": "Puducherry",
    "baroda": "Vadodara",
    "trivandrum": "Thiruvananthapuram",
    "cochin": "Kochi",
    "ludhiana city": "Ludhiana",
    "jaipur city": "Jaipur",
}


class Candidate(BaseModel):
    """Candidate match when resolving a location."""
    canonical_name: str
    entity_type: str  # 'state', 'district', 'block'
    location_id: Optional[int] = None
    state: str
    district: Optional[str] = None
    block: Optional[str] = None
    score: float = Field(..., description="Fuzzy match confidence score (0-100)")


class ResolutionResult(BaseModel):
    """Structured result of resolving a location name."""
    status: str = Field(..., description="'resolved', 'ambiguous', or 'unresolved'")
    query: str
    canonical_name: Optional[str] = None
    entity_type: Optional[str] = None
    location_id: Optional[int] = None
    state: Optional[str] = None
    district: Optional[str] = None
    block: Optional[str] = None
    score: float = 0.0
    candidates: Optional[List[Candidate]] = None
    message: Optional[str] = None

    def __bool__(self) -> bool:
        return self.status == "resolved"

    def __getitem__(self, item: str) -> Any:
        if item == "id":
            return self.location_id
        return getattr(self, item)

    def __contains__(self, item: str) -> bool:
        return hasattr(self, item) or item == "id"


def clean_query(query: str) -> str:
    """Normalize input query text: strip punctuation, extra whitespace, and boilerplate."""
    q = query.lower().strip()
    # Strip common administrative affixes
    q = re.sub(r"\b(district|dist|block|tehsil|taluka|mandal|state|city|town)\b", "", q)
    q = re.sub(r"[^\w\s]", " ", q)
    q = re.sub(r"\s+", " ", q).strip()
    return q


def name_similarity_scorer(s1: str, s2: str, **kwargs) -> float:
    """Robust string similarity scorer for geographic names with length penalty."""
    len_diff = abs(len(s1) - len(s2))
    max_len = max(len(s1), len(s2))
    if max_len > 0 and (len_diff / max_len) > 0.5:
        # Significant length disparity -> heavily penalized
        return 0.0
    return float(max(fuzz.ratio(s1, s2), fuzz.token_sort_ratio(s1, s2)))


class LocationResolver:
    """High-performance entity resolver using RapidFuzz over SQLite locations."""

    def __init__(
        self,
        db_path: Optional[Path] = None,
        match_threshold: float = 70.0,
        ambiguity_margin: float = 5.0,
    ):
        self.db_path = db_path or settings.DB_PATH
        self.match_threshold = match_threshold
        self.ambiguity_margin = ambiguity_margin
        self._entries: List[Dict[str, Any]] = []
        self._corpus: List[str] = []
        self.load_corpus()

    def _get_connection(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self.db_path))
        conn.row_factory = sqlite3.Row
        return conn

    def load_corpus(self):
        """Build search corpus from locations in the database."""
        if not self.db_path.exists():
            return

        self._entries.clear()
        self._corpus.clear()

        conn = self._get_connection()
        cursor = conn.cursor()

        # 1. Index States
        cursor.execute("SELECT DISTINCT state FROM locations")
        for row in cursor.fetchall():
            state_name = row["state"]
            entry = {
                "canonical_name": state_name,
                "entity_type": "state",
                "location_id": None,
                "state": state_name,
                "district": None,
                "block": None,
            }
            self._entries.append(entry)
            self._corpus.append(state_name.lower())

        # 2. Index Districts
        cursor.execute("SELECT id, state, district FROM locations WHERE block = 'All'")
        for row in cursor.fetchall():
            dist_name = row["district"]
            entry = {
                "canonical_name": dist_name,
                "entity_type": "district",
                "location_id": row["id"],
                "state": row["state"],
                "district": dist_name,
                "block": "All",
            }
            self._entries.append(entry)
            self._corpus.append(dist_name.lower())

        # 3. Index Blocks
        cursor.execute("SELECT id, state, district, block FROM locations WHERE block != 'All'")
        for row in cursor.fetchall():
            block_name = row["block"]
            entry = {
                "canonical_name": block_name,
                "entity_type": "block",
                "location_id": row["id"],
                "state": row["state"],
                "district": row["district"],
                "block": block_name,
            }
            self._entries.append(entry)
            self._corpus.append(block_name.lower())

        conn.close()

    def resolve(
        self,
        query: str,
        entity_type: Optional[str] = None,
        threshold: Optional[float] = None,
        ambiguity_margin: Optional[float] = None,
    ) -> ResolutionResult:
        """Resolve a raw query string to a canonical location.

        Args:
            query: User-supplied name (e.g. "Ludhiyana", "Banglore", "Jaipur district").
            entity_type: Optional filter ('state', 'district', 'block').
            threshold: Minimum score threshold (default 70.0).
            ambiguity_margin: Score difference between top-2 candidates to trigger ambiguity (default 5.0).

        Returns:
            ResolutionResult indicating 'resolved', 'ambiguous', or 'unresolved'.
        """
        if not self._corpus:
            self.load_corpus()

        thresh = threshold if threshold is not None else self.match_threshold
        margin = ambiguity_margin if ambiguity_margin is not None else self.ambiguity_margin

        cleaned = clean_query(query)
        raw_lower = query.lower().strip()

        if not cleaned:
            return ResolutionResult(
                status="unresolved",
                query=query,
                message="Query is empty after normalization",
            )

        # Check aliases dictionary (e.g. "banglore" -> "Bengaluru Urban")
        alias_target = GEOGRAPHIC_ALIASES.get(raw_lower) or GEOGRAPHIC_ALIASES.get(cleaned)
        effective_query = alias_target.lower() if alias_target else cleaned

        # Filter candidates by entity_type if requested
        eligible_indices = [
            i for i, entry in enumerate(self._entries)
            if entity_type is None or entry["entity_type"] == entity_type
        ]

        if not eligible_indices:
            return ResolutionResult(
                status="unresolved",
                query=query,
                message=f"No entities matching entity_type '{entity_type}'",
            )

        candidate_corpus = [self._corpus[i] for i in eligible_indices]

        # 1. Exact match pass
        exact_matches = []
        for orig_idx, corpus_name in zip(eligible_indices, candidate_corpus):
            if corpus_name == effective_query:
                entry = self._entries[orig_idx]
                exact_matches.append(Candidate(score=100.0, **entry))

        if len(exact_matches) == 1:
            match = exact_matches[0]
            return ResolutionResult(
                status="resolved",
                query=query,
                canonical_name=match.canonical_name,
                entity_type=match.entity_type,
                location_id=match.location_id,
                state=match.state,
                district=match.district,
                block=match.block,
                score=100.0,
            )
        elif len(exact_matches) > 1:
            return ResolutionResult(
                status="ambiguous",
                query=query,
                candidates=exact_matches,
                score=100.0,
                message=f"Multiple exact matches found for '{query}'. Please clarify.",
            )

        # 2. Fuzzy search using RapidFuzz extract
        scored_results = process.extract(
            effective_query,
            candidate_corpus,
            scorer=name_similarity_scorer,
            limit=5,
        )

        # Filter above threshold
        qualifying: List[Tuple[float, Dict[str, Any]]] = []
        seen_keys = set()

        for match_str, score, local_idx in scored_results:
            if score >= thresh:
                orig_idx = eligible_indices[local_idx]
                entry = self._entries[orig_idx]
                # Unique key to avoid duplicate representations
                key = (entry["canonical_name"], entry["entity_type"], entry["state"], entry["district"])
                if key not in seen_keys:
                    seen_keys.add(key)
                    qualifying.append((score, entry))

        if not qualifying:
            return ResolutionResult(
                status="unresolved",
                query=query,
                message=f"No matching location found above threshold ({thresh})",
            )

        # Sort descending by score
        qualifying.sort(key=lambda x: x[0], reverse=True)
        top_score, top_entry = qualifying[0]

        # Check for ambiguity among qualifying candidates
        close_candidates = [
            Candidate(score=round(s, 2), **e)
            for s, e in qualifying
            if (top_score - s) <= margin and (e["canonical_name"] != top_entry["canonical_name"] or e["entity_type"] != top_entry["entity_type"] or e["district"] != top_entry["district"])
        ]

        if close_candidates:
            all_ambiguous = [Candidate(score=round(top_score, 2), **top_entry)] + close_candidates
            return ResolutionResult(
                status="ambiguous",
                query=query,
                candidates=all_ambiguous,
                score=round(top_score, 2),
                message=f"Query '{query}' is ambiguous between {len(all_ambiguous)} candidates.",
            )

        # Single confident match
        return ResolutionResult(
            status="resolved",
            query=query,
            canonical_name=top_entry["canonical_name"],
            entity_type=top_entry["entity_type"],
            location_id=top_entry["location_id"],
            state=top_entry["state"],
            district=top_entry["district"],
            block=top_entry["block"],
            score=round(top_score, 2),
        )


# Global singleton instance for app-wide use
resolver = LocationResolver()


def resolve_location(
    query: str,
    entity_type: Optional[str] = None,
    threshold: float = 70.0,
    ambiguity_margin: float = 5.0,
) -> ResolutionResult:
    """Convenience helper to resolve a location string using the global resolver."""
    return resolver.resolve(
        query=query,
        entity_type=entity_type,
        threshold=threshold,
        ambiguity_margin=ambiguity_margin,
    )
