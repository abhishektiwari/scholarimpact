"""
Widget configuration and visibility management for the dashboard.
Handles reading config from .streamlit/config.toml to hide/show sections.
"""

import tomllib
from pathlib import Path
from typing import Optional, Set


class WidgetConfig:
    """Manages widget visibility based on configuration."""

    _hidden_widgets_cache: Optional[Set[str]] = None

    @staticmethod
    def get_hidden_widgets() -> Set[str]:
        """Load hidden widgets from .streamlit/config.toml.

        Config format in .streamlit/config.toml:
        [widgets]
        hideWidgets = ["Altmetric Attention", "Top Citing Countries"]

        Returns:
            Set of widget names that should be hidden
        """
        if WidgetConfig._hidden_widgets_cache is not None:
            return WidgetConfig._hidden_widgets_cache

        hidden_widgets = set()

        try:
            # Try to find .streamlit/config.toml in multiple locations
            import os
            import sys

            config_paths = [
                # Current working directory
                Path(".streamlit/config.toml"),
                # User's home streamlit config
                Path("~/.streamlit/config.toml").expanduser(),
                # Walk up directory tree looking for .streamlit/config.toml
                Path(os.getcwd()).parent / ".streamlit" / "config.toml",
                Path(os.getcwd()).parent.parent / ".streamlit" / "config.toml",
            ]

            for config_path in config_paths:
                if config_path.exists():
                    try:
                        with open(config_path, "rb") as f:
                            config = tomllib.load(f)
                            if "widgets" in config and "hideWidgets" in config["widgets"]:
                                hide_list = config["widgets"]["hideWidgets"]
                                if isinstance(hide_list, list):
                                    hidden_widgets = set(hide_list)
                                    print(f"✓ Loaded hidden widgets from {config_path.resolve()}: {hidden_widgets}")
                        break
                    except Exception as file_err:
                        print(f"Error reading {config_path}: {file_err}")
        except Exception as e:
            print(f"Warning: Could not load widget config: {e}")

        if not hidden_widgets:
            print("No hidden widgets configured (all sections will be shown)")

        WidgetConfig._hidden_widgets_cache = hidden_widgets
        return hidden_widgets

    @staticmethod
    def should_render(widget_name: str) -> bool:
        """Check if a widget should be rendered.

        Args:
            widget_name: Name of the widget to check

        Returns:
            True if widget should be rendered, False if hidden
        """
        hidden = WidgetConfig.get_hidden_widgets()
        return widget_name not in hidden

    @staticmethod
    def clear_cache():
        """Clear the cached hidden widgets (useful for testing)."""
        WidgetConfig._hidden_widgets_cache = None


# Available widget names that can be hidden (use snake_case)
AVAILABLE_WIDGETS = {
    "Top_Citing_Countries",
    "Citation_Distribution_by_Country",
    "Citations_Distribution_by_Year",
    "Research_Domain_Analysis",
    "Interdisciplinary_Impact_Metrics",
    "Altmetric_Attention",
    "Notable_Citations",
    "Top_Citing_Institutions",
    "Detailed_Citations_Table",
}
