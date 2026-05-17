#!/usr/bin/env python3
"""
ScholarImpact CLI - Command line interface for citation analysis.
"""

import logging
from pathlib import Path

import click

# Import commands
from .commands import add_rankings, crawl, dashboard, extract, generate, list_articles

# Setup logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)


@click.group()
@click.version_option()
@click.option("--verbose", "-v", is_flag=True, help="Verbose output")
@click.pass_context
def cli(ctx, verbose):
    """ScholarImpact - Citation Analysis and Dashboard Tool."""
    ctx.ensure_object(dict)
    ctx.obj["verbose"] = verbose

    if verbose:
        logging.getLogger().setLevel(logging.DEBUG)


# Add commands
cli.add_command(extract.extract_author)
cli.add_command(crawl.crawl_citations)
cli.add_command(list_articles.list_articles)
cli.add_command(add_rankings.add_rankings)
cli.add_command(dashboard.dashboard)
cli.add_command(generate.generate_dashboard)
# cli.add_command(assets.assets)  # Removed for simplified version


# Quick start command
@cli.command()
@click.argument("scholar_id")
@click.option("--openalex-api-key", help="OpenAlex API key (enables OpenAlex enrichment)")
@click.option("--altmetric-api-key", help="Altmetric API key (enables Altmetric enrichment)")
@click.option("--output-dir", default="./data", help="Output directory")
@click.option(
    "--launch-dashboard/--no-dashboard", default=True, help="Launch dashboard after analysis"
)
@click.pass_context
def quick_start(ctx, scholar_id, openalex_api_key, altmetric_api_key, output_dir, launch_dashboard):
    """Complete analysis pipeline from Scholar ID to dashboard."""
    click.echo(f"Starting complete analysis for Scholar ID: {scholar_id}")

    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Extract author data
    click.echo("1. Extracting author publications...")
    ctx.invoke(extract.extract_author, scholar_id=scholar_id, output_dir=output_dir, openalex_api_key=openalex_api_key, altmetric_api_key=altmetric_api_key)

    # Crawl citations
    click.echo("2. Crawling citations...")
    ctx.invoke(
        crawl.crawl_citations,
        author_json=f"{output_dir}/author.json",
        openalex_api_key=openalex_api_key,
    )

    # Launch dashboard
    if launch_dashboard:
        click.echo("3. Launching dashboard...")
        ctx.invoke(dashboard.dashboard, data_dir=output_dir)

    click.echo(" Analysis complete!")


if __name__ == "__main__":
    cli()
