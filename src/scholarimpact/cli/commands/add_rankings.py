"""Add institution rankings to citations command for CLI."""

import json
import logging
from pathlib import Path

import click

from ...core.institution_ranker import InstitutionRanker

logger = logging.getLogger(__name__)


@click.command(name="add-rankings")
@click.argument("citations_json")
@click.option(
    "--rankings-file",
    default="./data/ScimagoIR2026-OverallRank.csv",
    help="Path to Scimago Institution Rankings CSV file",
)
def add_rankings(citations_json, rankings_file):
    """Add Scimago Institution Ranking to citation data.

    This command enriches the citations JSON file with institution ranking data
    from Scimago, adding institution_rank and institution_rank_weight to each
    citing author.

    The enriched data can then be used by the dashboard to display top citing
    institutions and their prominence.

    CITATIONS_JSON: Path to citations JSON file (from crawl-citations command)
    """

    click.echo(f"Processing citation file: {citations_json}")

    # Check if rankings file exists
    rankings_path = Path(rankings_file)

    # If default location and file not found, also check for alternate filename
    if not rankings_path.exists() and rankings_file == "./data/ScimagoIR2026-OverallRank.csv":
        alternate_path = Path("./data/ScimagoIR 2026 - Overall Rank.csv")
        if alternate_path.exists():
            rankings_path = alternate_path

    if not rankings_path.exists():
        raise click.ClickException(
            f"Scimago rankings file not found: {rankings_path}\n"
            f"Please download it from: https://www.scimagoir.com\n"
            f"And place it in the data/ folder as one of:\n"
            f"  - ScimagoIR2026-OverallRank.csv\n"
            f"  - ScimagoIR 2026 - Overall Rank.csv\n"
            f"Or specify the path with: --rankings-file /path/to/file.csv"
        )

    click.echo(f"Using rankings file: {rankings_path.resolve()}")

    # Initialize ranker
    try:
        ranker = InstitutionRanker(rankings_file=str(rankings_path))
    except ImportError as e:
        raise click.ClickException(
            f"Required package missing: {e}. Install with: pip install networkx"
        )

    # Enrich citations with rankings
    click.echo("Adding institution rankings...")
    enrichment_result = ranker.enrich_citations_with_rankings(citations_json)

    if not enrichment_result.get("success"):
        raise click.ClickException(enrichment_result.get("error", "Unknown error"))

    # Display enrichment results
    click.echo("\n" + "=" * 80)
    click.echo("RANKINGS ADDED")
    click.echo("=" * 80)
    click.echo(f"\nFile: {enrichment_result['file']}")
    click.echo(f"Enriched entries: {enrichment_result['enriched_entries']}")
    click.echo(f"Ranked institutions: {enrichment_result['ranked_institutions']}")
    click.echo(f"Total citations: {enrichment_result['total_citations']}")

    click.echo("\n" + "=" * 80)
    click.echo("✓ Institution rankings added successfully!")
    click.echo("Ready for dashboard visualization showing top citing institutions.")
    click.echo("=" * 80)
