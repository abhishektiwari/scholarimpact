"""Crawl citations command for CLI."""

import json
import logging
from pathlib import Path

import click

from ...core.crawler import CitationCrawler

logger = logging.getLogger(__name__)


@click.command(name="crawl-citations")
@click.argument("author_json")
@click.option("--openalex-api-key", help="OpenAlex API key (enables OpenAlex enrichment)")
@click.option("--max-citations", type=int, help="Maximum citations per paper")
@click.option(
    "--delay-min", default=5.0, type=float, help="Minimum delay between requests (default: 5.0)"
)
@click.option(
    "--delay-max", default=10.0, type=float, help="Maximum delay between requests (default: 10.0)"
)
@click.option("--output-dir", help="Output directory (defaults to author.json directory)")
@click.option("--cites-id", help="Crawl only a specific article by cites_id (Google Scholar citation ID)")
@click.option("--force", is_flag=True, help="Force re-crawl of articles with existing citations (overwrite existing files)")
def crawl_citations(
    author_json,
    openalex_api_key,
    max_citations,
    delay_min,
    delay_max,
    output_dir,
    cites_id,
    force,
):
    """Crawl citations for publications in author.json file."""

    click.echo(f"Loading author data from: {author_json}")

    # Load author data
    try:
        with open(author_json, "r", encoding="utf-8") as f:
            author_data = json.load(f)
    except FileNotFoundError:
        raise click.ClickException(f"Author file not found: {author_json}")
    except json.JSONDecodeError:
        raise click.ClickException(f"Invalid JSON in author file: {author_json}")

    # Determine output directory
    if not output_dir:
        output_dir = str(Path(author_json).parent)

    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Get articles from author data
    articles = author_data.get("articles", [])
    if not articles:
        click.echo("No articles found in author data")
        return

    # Filter articles if --cites-id option is provided
    if cites_id:
        matching_articles = [
            a for a in articles
            if a.get("cites_id") == cites_id
        ]
        if matching_articles:
            articles = matching_articles
            # Auto-enable force when targeting specific article (citations may have changed)
            force = True
            click.echo(f"Crawling article with cites_id '{cites_id}': {articles[0].get('title', 'Unknown title')}")
        else:
            raise click.ClickException(f"No article found with cites_id '{cites_id}'")

    click.echo(f"Processing {len(articles)} article(s)")

    # Initialize crawler
    delay_range = (delay_min, delay_max)
    crawler = CitationCrawler(delay_range=delay_range, openalex_api_key=openalex_api_key)

    # Process each article
    processed = 0
    skipped = 0
    errors = 0

    with click.progressbar(articles, label="Crawling citations") as article_bar:
        for article in article_bar:
            cites_id = article.get("cites_id")
            title = article.get("title", "Unknown")

            if not cites_id:
                logger.info(
                    f"Skipping '{title}': No cites_id found - article has no citations to crawl"
                )
                skipped += 1
                continue

            # Check if already processed
            output_file = Path(output_dir) / f"cites-{cites_id.replace(',', '_')}.json"
            skip_article = False
            skip_reason = None

            if output_file.exists():
                # Always check citation count in file
                try:
                    with open(output_file, "r", encoding="utf-8") as f:
                        citations = json.load(f)
                        total_citations = article.get("total_citations", 0)
                        file_citation_count = len(citations) if isinstance(citations, list) else 0

                        if file_citation_count == total_citations:
                            # Counts match - file is up to date
                            skip_article = True
                            skip_reason = (
                                f"Citation count unchanged - {total_citations} citations in author.json, "
                                f"{file_citation_count} citations in file"
                            )
                        elif file_citation_count < total_citations:
                            # Missing citations - need to crawl regardless of force flag
                            skip_article = False
                            logger.info(
                                f"Citation count increased - {total_citations} citations in author.json, "
                                f"{file_citation_count} in file (crawling to get new citations)"
                            )
                        elif not force:
                            # File has more citations than author.json (unusual) - skip unless force
                            skip_article = True
                            skip_reason = (
                                f"File has more citations - {total_citations} in author.json, "
                                f"{file_citation_count} in file (use --force to recrawl)"
                            )
                except (json.JSONDecodeError, IOError):
                    # If file is corrupted and force is not enabled, skip it
                    if not force:
                        skip_article = True
                        skip_reason = "Output file corrupted or unreadable"
                        logger.debug(f"Output file corrupted for '{title}'")
                    else:
                        logger.debug(f"Output file corrupted for '{title}', will re-crawl")

            if skip_article:
                logger.info(f"Skipping '{title}': {skip_reason}")
                skipped += 1
                continue

            try:
                logger.info(f"Crawling citations for '{title}' (cites_id: {cites_id})")

                # Crawl citations
                # Convert max_citations to max_pages (10 citations per page typically)
                max_pages = None if max_citations is None else (max_citations + 9) // 10
                citations = crawler.crawl_all_citations(
                    cites_id, max_pages=max_pages
                )

                # Limit citations if max_citations is specified
                if max_citations and citations and len(citations) > max_citations:
                    citations = citations[:max_citations]

                # Save citations to file
                if citations:
                    with open(output_file, "w", encoding="utf-8") as f:
                        json.dump(citations, f, ensure_ascii=False, indent=2)
                    logger.info(f"Saved {len(citations)} citations for '{title}' to {output_file.name}")
                else:
                    logger.info(f"No citations found for '{title}'")

                processed += 1

            except Exception as e:
                logger.error(f"Error crawling citations for '{title}': {e}")
                click.echo(f"\nError processing {article.get('title', 'Unknown')}: {e}")
                errors += 1

    # Summary
    click.echo(f"\n Citation crawling complete!")
    click.echo(f"   Processed: {processed}")
    click.echo(f"   Skipped (no ID or exists): {skipped}")
    if errors > 0:
        click.echo(f"   Errors: {errors}")
