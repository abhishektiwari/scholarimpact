"""Crawl citations command for CLI."""

import json
from pathlib import Path

import click

from ...core.crawler import CitationCrawler


@click.command(name="crawl-citations")
@click.argument("author_json")
@click.option("--openalex-email", help="OpenAlex email for enhanced data")
@click.option("--max-citations", type=int, help="Maximum citations per paper")
@click.option(
    "--delay-min", default=5.0, type=float, help="Minimum delay between requests (default: 5.0)"
)
@click.option(
    "--delay-max", default=10.0, type=float, help="Maximum delay between requests (default: 10.0)"
)
@click.option("--output-dir", help="Output directory (defaults to author.json directory)")
def crawl_citations(
    author_json,
    openalex_email,
    max_citations,
    delay_min,
    delay_max,
    output_dir,
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

    click.echo(f"Found {len(articles)} articles to process")

    # Initialize crawler
    delay_range = (delay_min, delay_max)
    crawler = CitationCrawler(delay_range=delay_range, openalex_email=openalex_email)

    # Process each article
    processed = 0
    skipped = 0
    errors = 0

    with click.progressbar(articles, label="Crawling citations") as article_bar:
        for article in article_bar:
            cites_id = article.get("cites_id")
            if not cites_id:
                skipped += 1
                continue

            # Check if already processed
            output_file = Path(output_dir) / f"cites-{cites_id.replace(',', '_')}.json"
            if output_file.exists():
                skipped += 1
                continue

            try:
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

                processed += 1

            except Exception as e:
                click.echo(f"\nError processing {article.get('title', 'Unknown')}: {e}")
                errors += 1

    # Summary
    click.echo(f"\n Citation crawling complete!")
    click.echo(f"   Processed: {processed}")
    click.echo(f"   Skipped (no ID or exists): {skipped}")
    if errors > 0:
        click.echo(f"   Errors: {errors}")
