"""Generate dashboard command for CLI."""

from pathlib import Path

import click

from ...assets import copy_fonts, copy_streamlit_config, list_assets


@click.command(name="generate-dashboard")
@click.option("--output-dir", default=".", help="Output directory for generated files")
@click.option("--name", default="my_dashboard.py", help="Name of the dashboard file")
@click.option("--data-dir", default="./data", help="Data directory for dashboard")
@click.option("--title", default="My Citation Dashboard", help="Dashboard title")
def generate_dashboard(output_dir, name, data_dir, title):
    """Generate a one-liner dashboard file and copy .streamlit config."""

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    # Generate one-liner dashboard file
    dashboard_content = f'''#!/usr/bin/env python3
"""
Generated ScholarImpact Dashboard
"""

from scholarimpact.dashboard import Dashboard

if __name__ == "__main__":
    dashboard = Dashboard(
        data_dir="{data_dir}",
        title="{title}"
    )
    dashboard.run()
'''

    dashboard_file = output_path / name
    with open(dashboard_file, "w", encoding="utf-8") as f:
        f.write(dashboard_content)

    # Make executable
    dashboard_file.chmod(0o755)

    click.echo(f" Generated dashboard file: {dashboard_file}")

    # Copy .streamlit config with fonts using bundled assets
    streamlit_dir = output_path / ".streamlit"
    streamlit_dir.mkdir(exist_ok=True)

    # Copy bundled Streamlit config
    config_copied = copy_streamlit_config(str(streamlit_dir), "streamlit/config.toml")
    if config_copied:
        click.echo(f" Copied bundled Streamlit config: {streamlit_dir / 'config.toml'}")
    else:
        # Fallback: create basic config
        config_content = """[theme]
primaryColor = "#1f77b4"
backgroundColor = "#ffffff"
secondaryBackgroundColor = "#f0f2f6"
textColor = "#262730"
font = "serif"

[server]
runOnSave = true
port = 8501
enableCORS = false
enableXsrfProtection = false

[browser]
gatherUsageStats = false
"""
        config_file = streamlit_dir / "config.toml"
        with open(config_file, "w", encoding="utf-8") as f:
            f.write(config_content)
        click.echo(f" Generated fallback Streamlit config: {config_file}")

    # Copy bundled fonts
    fonts_copied = copy_fonts(str(streamlit_dir))
    if fonts_copied > 0:
        click.echo(f" Copied {fonts_copied} bundled font(s) to {streamlit_dir}")
    else:
        # Create font setup guide if no bundled fonts
        fonts_note = streamlit_dir / "README_fonts.txt"
        with open(fonts_note, "w", encoding="utf-8") as f:
            f.write(
                """Font Setup Instructions:
1. Download your preferred fonts (e.g., Inter, Roboto, Source Sans Pro)
2. Place font files (.ttf, .otf, .woff) in this .streamlit directory
3. Update config.toml [theme] font setting if needed

Supported font families:
- "sans serif" (default)
- "serif" 
- "monospace"

For custom fonts, use the font family name after placing files here.
"""
            )
        click.echo(f" Created font setup guide: {fonts_note}")

    # Generate requirements.txt for deployment
    requirements_content = "scholarimpact\n"

    requirements_file = output_path / "requirements.txt"
    with open(requirements_file, "w", encoding="utf-8") as f:
        f.write(requirements_content)

    click.echo(f" Generated requirements.txt for deployment: {requirements_file}")

    # Show available bundled assets
    assets = list_assets()
    if assets:
        click.echo(f"Available bundled assets: {', '.join(assets)}")

    # Generate usage instructions
    click.echo(f"\nDashboard setup complete!")
    click.echo(f"To run your dashboard:")
    click.echo(f"  python {name}")
    click.echo(f"")
    click.echo(f"Or manually:")
    click.echo(f"  scholarimpact dashboard --data-dir {data_dir}")

    if data_dir != "./data":
        click.echo(f"\n Make sure your data is in: {data_dir}")
    else:
        click.echo(f"\n Place your citation data in the 'data' directory")
