"""
Base component classes and utilities for dashboard components.
"""

from abc import ABC, abstractmethod
from typing import Any, Callable, Dict, List, Optional

import streamlit as st


class ThemeColors:
    """Color utilities matching original streamlit_app.py exactly."""

    @staticmethod
    def get_color_palette() -> Dict[str, Any]:
        """Get theme colors dynamically matching original."""
        theme_colors = st.get_option("theme.chartCategoricalColors") or [
            "#0ea5e9",
            "#059669",
            "#fbbf24",
        ]

        return {
            "primary": st.get_option("theme.primaryColor") or "#cb785c",
            "chart_colors": theme_colors,
            "bar_color": theme_colors[0],
            "line_color": theme_colors[2],
            "fill_color": theme_colors[2],
            "gradient": [
                "#e6fef5",
                "#b8f5e0",
                "#8aeccc",
                "#5ce3b7",
                "#2dd4a3",
                "#0dc58e",
                "#059669",
            ],
            "qualitative": theme_colors + ["#cb785c", "#8b5cf6", "#ec4899", "#6366f1", "#78716c"],
            "sequential": "Greens",
            "diverging": "RdBu",
        }

    @staticmethod
    def get_single_color(color_type: str = "bar") -> str:
        """Get single color for charts."""
        palette = ThemeColors.get_color_palette()
        return palette.get(f"{color_type}_color", palette["chart_colors"][0])

    @staticmethod
    def get_colorscale(scale_type: str = "sequential") -> str:
        """Get colorscale for plotly."""
        palette = ThemeColors.get_color_palette()
        return palette.get(scale_type, "Greens")

    @staticmethod
    def apply_theme_to_plotly(fig, color_palette: Dict[str, Any]):
        """Apply theme styling to plotly figures."""
        fig.update_layout(
            paper_bgcolor=st.get_option("theme.backgroundColor") or "#fdfdf8",
            plot_bgcolor=st.get_option("theme.backgroundColor") or "#fdfdf8",
        )


class BaseComponent(ABC):
    """Base class for all dashboard components."""

    def __init__(self, name: str, config: Optional[Dict[str, Any]] = None):
        """Initialize component."""
        self.name = name
        self.config = config or {}
        self.container = None

    def set_layout(self, container):
        """Set the Streamlit container for this component."""
        self.container = container

    def _render_in_container(self, render_func: Callable):
        """Render component in its assigned container."""
        if self.container:
            with self.container:
                render_func()
        else:
            render_func()

    @abstractmethod
    def get_required_data_keys(self) -> List[str]:
        """Return list of required data keys."""
        pass

    @abstractmethod
    def validate_data(self, data: Dict[str, Any]) -> bool:
        """Validate that required data is available."""
        pass

    @abstractmethod
    def render(self, data: Dict[str, Any], **kwargs) -> None:
        """Render the component."""
        pass


class ComponentRegistry:
    """Registry for dashboard components."""

    _components: Dict[str, type] = {}

    @classmethod
    def register(cls, name: str, component_class: type):
        """Register a component class."""
        cls._components[name] = component_class

    @classmethod
    def create(cls, name: str, config: Optional[Dict[str, Any]] = None) -> Optional[BaseComponent]:
        """Create a component instance."""
        if name in cls._components:
            return cls._components[name](name, config)
        return None

    @classmethod
    def list_components(cls) -> List[str]:
        """List all registered components."""
        return list(cls._components.keys())
