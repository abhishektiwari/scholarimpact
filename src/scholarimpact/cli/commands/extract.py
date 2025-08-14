"""Extract author command for CLI."""

from pathlib import Path

import click

from ...core.extractor import AuthorExtractor


@click.command(name="extract-author")
@click.argument("scholar_id")
@click.option("--max-papers", type=int, help="Maximum number of papers to analyze")
@click.option("--output-dir", default="./data", help="Output directory")
@click.option("--output-file", help="Output file path (overrides output-dir)")
@click.option("--delay", default=2.0, type=float, help="Delay between requests")
def extract_author(scholar_id, max_papers, output_dir, output_file, delay):
    """Extract author publications from Google Scholar."""

    click.echo(f"Extracting author data for Scholar ID: {scholar_id}")

    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Initialize extractor
    extractor = AuthorExtractor(delay=delay)

    try:
        # Extract author data
        author_data = extractor.extract(
            scholar_id, max_papers=max_papers, output_file=output_file, output_dir=output_dir
        )

        click.echo(f" Successfully extracted data for {author_data['name']}")
        click.echo(f"   Publications: {author_data['total_publications']}")
        click.echo(f"   Total Citations: {author_data['total_citations']}")
        click.echo(f"   h-index: {author_data['hindex']}")

        if output_file:
            click.echo(f"   Data saved to: {output_file}")
        else:
            click.echo(f"   Data saved to: {output_dir}/author.json")

    except Exception as e:
        click.echo(f"Error extracting author data: {e}", err=True)
        raise click.ClickException(str(e))
