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
Generated ScholarImpact
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

    # Generate .env file for widget configuration
    env_content = """# ScholarImpact Dashboard Configuration
# Widget visibility control (comma-separated list of widgets to hide)
SCHOLARIMPACT_HIDE_WIDGETS=Altmetric_Attention

# Available widgets to hide:
# - Altmetric_Attention
# - Top_Citing_Countries
# - Citation_Distribution_by_Country
# - Citations_Distribution_by_Year
# - Research_Domain_Analysis
# - Interdisciplinary_Impact_Metrics
# - Top_Citing_Institutions
# - Notable_Citations
# - Detailed_Citations_Table

# Example: Hide multiple widgets
# SCHOLARIMPACT_HIDE_WIDGETS=Altmetric_Attention,Top_Citing_Countries,Research_Domain_Analysis
"""

    env_file = output_path / ".env"
    with open(env_file, "w", encoding="utf-8") as f:
        f.write(env_content)

    click.echo(f" Generated .env configuration file: {env_file}")

    # Generate Dockerfile for containerization
    dockerfile_content = """# app/Dockerfile
FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \\
    build-essential \\
    curl \\
    && rm -rf /var/lib/apt/lists/*

# Copy local files instead of cloning from git
COPY requirements.txt .
RUN pip3 install -r requirements.txt

COPY . .

EXPOSE 8501

HEALTHCHECK CMD curl --fail http://localhost:8501/_stcore/health

ENTRYPOINT ["streamlit", "run", "app.py", "--server.port=8501", "--server.address=0.0.0.0"]
"""

    dockerfile = output_path / "Dockerfile"
    with open(dockerfile, "w", encoding="utf-8") as f:
        f.write(dockerfile_content)

    click.echo(f" Generated Dockerfile for containerization: {dockerfile}")

    # Generate docker-compose.yml for orchestration
    compose_content = """version: '3.8'

services:
  web-scholarimpact-dashboard:
    # Build an image from the Dockerfile in the current directory
    build:
      context: .
      dockerfile: Dockerfile
      platforms:
        - linux/amd64
    image: scholarimpact-dashboard:latest
    environment:
      - ENV=production
      # Widget visibility configuration (see .env for available widgets)
      # Uncomment and set to hide specific widgets in the dashboard
      #- SCHOLARIMPACT_HIDE_WIDGETS=Altmetric_Attention
    restart: unless-stopped
    deploy:
      replicas: 1
      resources:
        limits:
          cpus: '1'
          memory: 512M
        reservations:
          cpus: '1'
          memory: 512M
    x-ports:
      - scholarimpact.d3ml.org:8501/https
"""

    compose_file = output_path / "docker-compose.yml"
    with open(compose_file, "w", encoding="utf-8") as f:
        f.write(compose_content)

    click.echo(f" Generated docker-compose.yml for orchestration: {compose_file}")

    # Show available bundled assets
    assets = list_assets()
    if assets:
        click.echo(f"Available bundled assets: {', '.join(assets)}")

    # Generate usage instructions
    click.echo(f"\nDashboard setup complete!")
    click.echo(f"To run your dashboard:")
    click.echo(f"  python {name}")
    click.echo(f"")
    click.echo(f"Or with Docker Compose:")
    click.echo(f"  docker-compose up -d")
    click.echo(f"")
    click.echo(f"Or with Docker:")
    click.echo(f"  docker build -t scholarimpact-dashboard .")
    click.echo(f"  docker run -p 8501:8501 scholarimpact-dashboard")
    click.echo(f"")
    click.echo(f"Or manually:")
    click.echo(f"  ScholarImpact --data-dir {data_dir}")

    if data_dir != "./data":
        click.echo(f"\n Make sure your data is in: {data_dir}")
    else:
        click.echo(f"\n Place your citation data in the 'data' directory")
