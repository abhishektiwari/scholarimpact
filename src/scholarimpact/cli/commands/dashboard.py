"""Dashboard command for CLI."""

import subprocess
import sys
from pathlib import Path

import click

from ...dashboard.app import Dashboard


@click.command(name="dashboard")
@click.option("--data-dir", default="./data", help="Data directory")
@click.option("--title", default="Citation Analysis Dashboard", help="Dashboard title")
@click.option("--port", default=8501, type=int, help="Port to run dashboard")
@click.option("--host", default="localhost", help="Host to bind to")
@click.option("--debug/--no-debug", default=False, help="Debug mode")
def dashboard(data_dir, title, port, host, debug):
    """Launch the citation analysis dashboard."""

    click.echo(f"Starting dashboard with data from: {data_dir}")

    # Check if data directory exists
    data_path = Path(data_dir)
    if not data_path.exists():
        click.echo(f"Warning: Data directory {data_dir} does not exist")
        if not click.confirm("Continue anyway?"):
            return

    # Check for author.json
    author_file = data_path / "author.json"
    if not author_file.exists():
        click.echo(f"Warning: No author.json found in {data_dir}")

    # Initialize dashboard
    try:
        dashboard_app = Dashboard(data_dir=data_dir, title=title, host=host, port=port)

        click.echo(f" Launching dashboard at http://{host}:{port}")
        click.echo("Press Ctrl+C to stop the dashboard")

        # Run dashboard
        dashboard_app.run(port=port, debug=debug)

    except KeyboardInterrupt:
        click.echo("\nDashboard stopped")
    except Exception as e:
        click.echo(f"Error starting dashboard: {e}")
        raise click.ClickException(str(e))
