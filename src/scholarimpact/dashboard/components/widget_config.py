"""
Widget configuration and visibility management for the dashboard.
Handles reading config from .env file and environment variables.
"""

import os
from pathlib import Path
from typing import Optional, Set

# Load .env file from app directory (same location as app.py)
try:
    from dotenv import load_dotenv
    env_paths = [
        Path(".env"),
        Path(".") / ".env",
        Path(__file__).parent.parent.parent / ".env",
    ]
    for env_path in env_paths:
        if env_path.exists():
            load_dotenv(env_path)
            break
except ImportError:
    # python-dotenv not available, will use os.environ directly
    pass


class WidgetConfig:
    """Manages widget visibility based on configuration."""

    _hidden_widgets_cache: Optional[Set[str]] = None

    @staticmethod
    def get_hidden_widgets() -> Set[str]:
        """Load hidden widgets from environment variables (.env file).

        Configuration in .env file (same directory as app.py):
        SCHOLARIMPACT_HIDE_WIDGETS=Altmetric_Attention,Top_Citing_Countries

        Returns:
            Set of widget names that should be hidden
        """
        if WidgetConfig._hidden_widgets_cache is not None:
            return WidgetConfig._hidden_widgets_cache

        hidden_widgets = set()

        # Read from SCHOLARIMPACT_HIDE_WIDGETS environment variable
        # This can be set in .env file or as system environment variable
        env_hidden = os.environ.get("SCHOLARIMPACT_HIDE_WIDGETS", "").strip()
        if env_hidden:
            # Parse comma-separated widget names
            hidden_widgets = set(w.strip() for w in env_hidden.split(",") if w.strip())

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
