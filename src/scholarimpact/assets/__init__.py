"""
Assets module for ScholarImpact package.

Contains bundled configuration files, fonts, and other static assets.
"""

import shutil
from pathlib import Path
from typing import Optional

from importlib.resources import files


def get_asset_path(asset_name: str) -> Optional[Path]:
    """
    Get path to bundled asset.

    Args:
        asset_name: Name of asset file

    Returns:
        Path to asset or None if not found
    """
    try:
        # Try to get asset from package using importlib.resources
        assets_pkg = files("scholarimpact.assets")
        asset_ref = assets_pkg / asset_name
        if asset_ref.is_file():
            # Return a Path object that can be used directly
            return Path(str(asset_ref))
    except Exception:
        pass

    # Fallback to local assets
    assets_dir = Path(__file__).parent
    asset_file = assets_dir / asset_name
    if asset_file.exists():
        return asset_file

    return None


def copy_streamlit_config(output_dir: str, config_name: str = "config.toml") -> bool:
    """
    Copy bundled Streamlit config to output directory.

    Args:
        output_dir: Output directory path
        config_name: Config file name (default: config.toml)

    Returns:
        True if successful, False otherwise
    """
    config_path = get_asset_path(config_name)
    if not config_path:
        return False

    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)

    try:
        # Extract just the filename if config_name has a path
        target_name = Path(config_name).name
        shutil.copy2(config_path, output_path / target_name)
        return True
    except Exception:
        return False


def copy_fonts(output_dir: str) -> int:
    """
    Copy bundled fonts and license files to static directory.

    Args:
        output_dir: Output directory path (should be .streamlit directory)

    Returns:
        Number of files copied (fonts + licenses)
    """
    assets_dir = Path(__file__).parent
    fonts_dir = assets_dir / "fonts"

    # Look for font files and license files in the fonts subdirectory
    font_files = []
    license_files = []
    if fonts_dir.exists():
        font_files = (
            list(fonts_dir.glob("*.ttf"))
            + list(fonts_dir.glob("*.otf"))
            + list(fonts_dir.glob("*.woff*"))
        )
        license_files = list(fonts_dir.glob("*.txt"))  # License files

    if not font_files and not license_files:
        return 0

    # Create static directory structure
    output_path = Path(output_dir)
    if output_path.name == ".streamlit":
        # Create static at parent level (alongside .streamlit)
        static_dir = output_path.parent / "static"
    else:
        # Fallback: create static at output directory level
        static_dir = output_path.parent / "static"
    static_dir.mkdir(parents=True, exist_ok=True)

    copied = 0

    # Copy font files to static directory
    for font_file in font_files:
        try:
            shutil.copy2(font_file, static_dir / font_file.name)
            copied += 1
        except Exception:
            continue

    # Copy license files to static directory
    for license_file in license_files:
        try:
            shutil.copy2(license_file, static_dir / license_file.name)
            copied += 1
        except Exception:
            continue

    return copied


def list_assets() -> list:
    """
    List all available bundled assets.

    Returns:
        List of asset file names
    """
    assets_dir = Path(__file__).parent
    return [f.name for f in assets_dir.iterdir() if f.is_file() and f.name != "__init__.py"]
