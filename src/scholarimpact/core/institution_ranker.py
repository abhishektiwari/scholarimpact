"""Enrich citations with institution rankings."""

import csv
import json
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class InstitutionRankings:
    """Load and query institution rankings from Scimago."""

    def __init__(self, rankings_file: Optional[str] = None):
        """
        Initialize rankings loader.

        Args:
            rankings_file: Path to Scimago rankings CSV. If None, uses bundled file.
        """
        if rankings_file is None:
            # Use bundled Scimago file
            rankings_file = Path(__file__).parent.parent / "data" / "ScimagoIR2026-OverallRank.csv"

        self.rankings_file = Path(rankings_file)
        self._rankings = None
        self._institution_name_map = None

    def _load_rankings(self) -> Dict[str, Dict]:
        """Load rankings from CSV file."""
        if self._rankings is not None:
            return self._rankings

        self._rankings = {}
        self._institution_name_map = {}

        if not self.rankings_file.exists():
            logger.warning(f"Rankings file not found: {self.rankings_file}")
            return self._rankings

        try:
            with open(self.rankings_file, "r", encoding="utf-8") as f:
                reader = csv.DictReader(f, delimiter=";")
                for row in reader:
                    rank = int(row.get("Global Rank", 0))
                    institution = row.get("Institution", "").strip()
                    country = row.get("Country", "").strip()
                    sector = row.get("Sector", "").strip()

                    if institution and rank > 0:
                        self._rankings[institution] = {
                            "rank": rank,
                            "country": country,
                            "sector": sector,
                        }

                        # Create normalized names for matching
                        normalized = self._normalize_name(institution)
                        self._institution_name_map[normalized] = institution

            logger.info(f"Loaded {len(self._rankings)} institution rankings")
        except Exception as e:
            logger.error(f"Error loading rankings file: {e}")

        return self._rankings

    @staticmethod
    def _normalize_name(name: str) -> str:
        """Normalize institution name for matching."""
        return name.lower().strip()

    def get_rank(self, institution_name: str) -> Optional[int]:
        """
        Get global rank for an institution.

        Args:
            institution_name: Institution name to look up

        Returns:
            Global rank (1 = top), or None if not found
        """
        rankings = self._load_rankings()

        # Try exact match first
        if institution_name in rankings:
            return rankings[institution_name]["rank"]

        # Try normalized match
        normalized = self._normalize_name(institution_name)
        if normalized in self._institution_name_map:
            matched_name = self._institution_name_map[normalized]
            return rankings[matched_name]["rank"]

        # Try partial match (institution might have slight variations)
        normalized_parts = set(normalized.split())
        for ranked_inst, data in rankings.items():
            ranked_parts = set(self._normalize_name(ranked_inst).split())
            # If at least 70% of words match, consider it a match
            if ranked_parts and normalized_parts:
                overlap = len(normalized_parts & ranked_parts)
                similarity = overlap / max(len(normalized_parts), len(ranked_parts))
                if similarity >= 0.85:
                    return data["rank"]

        return None

    def get_rank_weight(self, institution_name: str, top_n: int = 100) -> float:
        """
        Get normalized weight (0-1) for institution based on rank.

        Args:
            institution_name: Institution name
            top_n: Consider top N institutions as "notable" (threshold)

        Returns:
            Weight from 0-1 (1.0 = top ranked, 0.0 = not in rankings)
        """
        rank = self.get_rank(institution_name)

        if rank is None:
            return 0.0

        if rank <= top_n:
            # Linear scaling: rank 1 = 1.0, rank top_n = some lower value
            return max(0.3, 1.0 - (rank - 1) / (top_n * 2))

        return 0.0

    def get_institution_info(self, institution_name: str) -> Optional[Dict]:
        """
        Get full info for an institution.

        Args:
            institution_name: Institution name

        Returns:
            Dict with rank, country, sector, or None if not found
        """
        rankings = self._load_rankings()

        # Try exact match
        if institution_name in rankings:
            return {"name": institution_name, **rankings[institution_name]}

        # Try normalized match
        normalized = self._normalize_name(institution_name)
        if normalized in self._institution_name_map:
            matched_name = self._institution_name_map[normalized]
            return {"name": matched_name, **rankings[matched_name]}

        return None

    def get_top_institutions(self, limit: int = 50, sector: Optional[str] = None) -> list:
        """
        Get top institutions by rank.

        Args:
            limit: Number of institutions to return
            sector: Filter by sector (e.g., "Universities", "Companies")

        Returns:
            List of institution dicts sorted by rank
        """
        rankings = self._load_rankings()

        institutions = []
        for name, data in rankings.items():
            if sector and data.get("sector") != sector:
                continue
            institutions.append({"name": name, **data})

        # Sort by rank and return top N
        institutions.sort(key=lambda x: x["rank"])
        return institutions[:limit]


# Global rankings instance
_rankings_instance = None


def get_rankings() -> InstitutionRankings:
    """Get singleton instance of institution rankings."""
    global _rankings_instance
    if _rankings_instance is None:
        _rankings_instance = InstitutionRankings()
    return _rankings_instance

logger = logging.getLogger(__name__)


class InstitutionRanker:
    """Enrich citation data with institution rankings."""

    def __init__(self):
        """Initialize institution ranker."""
        self.rankings = get_rankings()

    def enrich_citations_with_rankings(self, citations_file: str) -> Dict[str, any]:
        """
        Enrich citations JSON with institution ranking information.

        Adds institution_rank and institution_rank_weight to each citing author.

        Args:
            citations_file: Path to citations JSON file (will be updated in place)

        Returns:
            Dict with enrichment statistics
        """
        try:
            with open(citations_file, "r", encoding="utf-8") as f:
                citations = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.error(f"Error loading citations file: {e}")
            return {"error": str(e), "success": False}

        enriched_count = 0
        ranked_institutions = set()

        # Enrich each citation with institution rankings
        for citation in citations:
            citing_authors_details = citation.get("citing_authors_details", [])
            for author in citing_authors_details:
                if not isinstance(author, dict):
                    continue

                institution = author.get("institution_display_name")
                if institution and institution not in ["Unknown", ""]:
                    # Add ranking information
                    rank = self.rankings.get_rank(institution)
                    if rank:
                        author["institution_rank"] = rank
                        author["institution_rank_weight"] = self.rankings.get_rank_weight(
                            institution, top_n=100
                        )
                        ranked_institutions.add(institution)
                        enriched_count += 1

        # Write back to file
        try:
            with open(citations_file, "w", encoding="utf-8") as f:
                json.dump(citations, f, ensure_ascii=False, indent=2)
            logger.info(f"Enriched {enriched_count} author entries with rankings")
            logger.info(f"Found {len(ranked_institutions)} ranked institutions")
            return {
                "success": True,
                "file": citations_file,
                "enriched_entries": enriched_count,
                "ranked_institutions": len(ranked_institutions),
                "total_citations": len(citations),
            }
        except Exception as e:
            logger.error(f"Error writing enriched citations: {e}")
            return {"error": str(e), "success": False}
