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
@click.option("--openalex-api-key", help="API key for OpenAlex (enables OpenAlex enrichment)")
@click.option("--altmetric-api-key", help="API key for Altmetric (enables Altmetric enrichment)")
def extract_author(scholar_id, max_papers, output_dir, output_file, delay, openalex_api_key, altmetric_api_key):
    """Extract author publications from Google Scholar."""

    click.echo(f"Extracting author data for Scholar ID: {scholar_id}")

    # OpenAlex is enabled only if API key is provided
    use_openalex = bool(openalex_api_key)

    # Altmetric is enabled only if API key is provided AND OpenAlex is enabled
    use_altmetric = bool(altmetric_api_key) and use_openalex

    if use_openalex:
        click.echo("OpenAlex enrichment enabled with API key")
    else:
        click.echo("OpenAlex enrichment disabled")

    if use_altmetric:
        click.echo("Altmetric enrichment enabled with API key")
    elif altmetric_api_key and not use_openalex:
        click.echo("Warning: Altmetric enrichment requires OpenAlex API key. Disabling Altmetric.", err=True)

    # Create output directory
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    # Initialize extractor
    extractor = AuthorExtractor(
        delay=delay,
        use_openalex=use_openalex,
        openalex_api_key=openalex_api_key,
        use_altmetric=use_altmetric,
        altmetric_api_key=altmetric_api_key if use_altmetric else None
    )

    try:
        # Extract author data
        author_data = extractor.extract(
            scholar_id, max_papers=max_papers, output_file=output_file, output_dir=output_dir
        )

        click.echo(f" Successfully extracted data for {author_data['name']}")
        click.echo(f"   Publications: {author_data['total_publications']}")
        click.echo(f"   Total Citations: {author_data['total_citations']}")
        click.echo(f"   h-index: {author_data['hindex']}")
        
        if use_openalex and 'articles' in author_data:
            enriched_count = sum(1 for art in author_data['articles'] if 'openalex_ids' in art and art['openalex_ids'])
            click.echo(f"   OpenAlex enriched: {enriched_count}/{len(author_data['articles'])} papers")
        
        if use_altmetric and 'articles' in author_data:
            altmetric_count = sum(1 for art in author_data['articles'] if 'altmetric_score' in art)
            click.echo(f"   Altmetric enriched: {altmetric_count}/{len(author_data['articles'])} papers")

        if output_file:
            click.echo(f"   Data saved to: {output_file}")
        else:
            click.echo(f"   Data saved to: {output_dir}/author.json")

    except Exception as e:
        click.echo(f"Error extracting author data: {e}", err=True)
        raise click.ClickException(str(e))
