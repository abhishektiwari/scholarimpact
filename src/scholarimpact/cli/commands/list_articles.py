"""List articles command for CLI."""

import json

import click


@click.command(name="list-articles")
@click.argument("author_json")
@click.option(
    "--format",
    type=click.Choice(["table", "json"]),
    default="table",
    help="Output format (table or json)",
)
def list_articles(author_json, format):
    """List all articles from author.json with their cites_id and title."""

    click.echo(f"Loading author data from: {author_json}")

    # Load author data
    try:
        with open(author_json, "r", encoding="utf-8") as f:
            author_data = json.load(f)
    except FileNotFoundError:
        raise click.ClickException(f"Author file not found: {author_json}")
    except json.JSONDecodeError:
        raise click.ClickException(f"Invalid JSON in author file: {author_json}")

    # Get articles
    articles = author_data.get("articles", [])
    if not articles:
        click.echo("No articles found in author data")
        return

    author_name = author_data.get("name", "Unknown")
    click.echo(f"\nAuthor: {author_name}")
    click.echo(f"Total articles: {len(articles)}\n")

    if format == "json":
        # JSON output
        output = [
            {
                "index": i,
                "cites_id": article.get("cites_id"),
                "title": article.get("title"),
                "year": article.get("year"),
                "citations": article.get("total_citations", 0),
            }
            for i, article in enumerate(articles)
        ]
        click.echo(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        # Table output
        click.echo(f"{'#':<3} {'Cites ID':<50} {'Title':<60} {'Year':<6} {'Cit':<4}")
        click.echo("-" * 130)

        for i, article in enumerate(articles):
            cites_id = article.get("cites_id", "N/A")
            # Truncate long cites_id for display
            if len(cites_id) > 49:
                cites_id_display = cites_id[:46] + "..."
            else:
                cites_id_display = cites_id

            title = article.get("title", "Unknown")
            # Truncate long title for display
            if len(title) > 59:
                title_display = title[:56] + "..."
            else:
                title_display = title

            year = str(article.get("year", "N/A"))
            citations = str(article.get("total_citations", 0))

            click.echo(
                f"{i:<3} {cites_id_display:<50} {title_display:<60} {year:<6} {citations:<4}"
            )

        click.echo("\n" + "=" * 130)
        click.echo(f"Total: {len(articles)} articles")
        click.echo("\nTo crawl citations for a specific article, use:")
        click.echo(
            "  scholarimpact crawl-citations author.json --cites-id <CITES_ID>"
        )
