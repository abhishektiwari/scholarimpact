"""
Widget configuration and visibility management for the dashboard.
Handles reading config from .streamlit/secrets.toml
"""

from typing import Optional, Set

import streamlit as st


class WidgetConfig:
    """Manages widget visibility based on Streamlit secrets configuration."""

    _hidden_widgets_cache: Optional[Set[str]] = None

    @staticmethod
    def get_hidden_widgets() -> Set[str]:
        """Load hidden widgets from Streamlit secrets.

        Configuration in .streamlit/secrets.toml:
        SCHOLARIMPACT_HIDE_WIDGETS = "Altmetric_Attention,Top_Citing_Countries"

        Returns:
            Set of widget names that should be hidden
        """
        if WidgetConfig._hidden_widgets_cache is not None:
            return WidgetConfig._hidden_widgets_cache

        hidden_widgets = set()

        # Read from Streamlit secrets (stored in .streamlit/secrets.toml)
        env_hidden = st.secrets["SCHOLARIMPACT_HIDE_WIDGETS"]
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
