"""
Layout management system matching original streamlit_app.py structure.
"""

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional, Union

import streamlit as st

from .base import BaseComponent, ComponentRegistry


class LayoutType(Enum):
    """Available layout types."""

    COLUMNS = "columns"
    TABS = "tabs"
    SIDEBAR = "sidebar"
    CONTAINER = "container"
    EXPANDER = "expander"
    MAIN = "main"


@dataclass
class LayoutConfig:
    """Configuration for layout sections."""

    layout_type: LayoutType
    components: List[str] = field(default_factory=list)
    config: Dict[str, Any] = field(default_factory=dict)
    title: Optional[str] = None


@dataclass
class DashboardLayout:
    """Complete dashboard layout configuration."""

    title: str
    sections: List[LayoutConfig] = field(default_factory=list)
    sidebar_sections: List[LayoutConfig] = field(default_factory=list)


class LayoutManager:
    """Manager for dashboard layout and component composition."""

    def __init__(self, data: Dict[str, Any]):
        """Initialize layout manager."""
        self.data = data
        self.components = {}
        self._current_containers = {}

    def create_component(
        self, component_name: str, config: Optional[Dict[str, Any]] = None
    ) -> Optional[BaseComponent]:
        """Create and cache component instance."""
        if component_name not in self.components:
            component = ComponentRegistry.create(component_name, config)
            if component:
                self.components[component_name] = component
            return component
        return self.components[component_name]

    def render_layout(self, layout: DashboardLayout):
        """Render complete dashboard layout."""
        # Set page title
        if layout.title:
            st.title(layout.title)

        # Render sidebar sections
        if layout.sidebar_sections:
            with st.sidebar:
                for section in layout.sidebar_sections:
                    self._render_section(section)

        # Render main sections
        for section in layout.sections:
            self._render_section(section)

    def _render_section(self, section: LayoutConfig):
        """Render a layout section with its components."""
        container = self._create_container(section)

        if section.layout_type == LayoutType.COLUMNS:
            # Handle columns layout
            col_configs = section.config.get("columns", [1] * len(section.components))
            cols = st.columns(col_configs) if container is None else container.columns(col_configs)

            for i, component_name in enumerate(section.components):
                if i < len(cols):
                    component = self.create_component(component_name)
                    if component:
                        component.set_layout(cols[i])
                        self._render_component(component, component_name, section.config)

        elif section.layout_type == LayoutType.TABS:
            # Handle tabs layout
            tab_titles = section.config.get("tab_titles", section.components)
            tabs = st.tabs(tab_titles) if container is None else container.tabs(tab_titles)

            for i, component_name in enumerate(section.components):
                if i < len(tabs):
                    component = self.create_component(component_name)
                    if component:
                        component.set_layout(tabs[i])
                        self._render_component(component, component_name, section.config)

        else:
            # Handle single container layouts
            for component_name in section.components:
                component = self.create_component(component_name)
                if component:
                    component.set_layout(container)
                    self._render_component(component, component_name, section.config)

    def _create_container(self, section: LayoutConfig):
        """Create Streamlit container based on layout type."""
        container = None

        if section.layout_type == LayoutType.CONTAINER:
            container = st.container()

        elif section.layout_type == LayoutType.EXPANDER:
            expanded = section.config.get("expanded", False)
            container = st.expander(section.title or "Section", expanded=expanded)

        elif section.layout_type == LayoutType.SIDEBAR:
            container = st.sidebar

        # Add section title if specified and not handled by container
        if section.title and section.layout_type not in [LayoutType.EXPANDER]:
            if container:
                container.subheader(section.title)
            else:
                st.subheader(section.title)

        return container

    def _render_component(
        self, component: BaseComponent, component_name: str, section_config: Dict[str, Any]
    ):
        """Render individual component with section configuration."""
        try:
            # Get component-specific config from section
            component_config = section_config.get(component_name, {})

            # Pass data_dir if not already in config
            if "data_dir" not in component_config:
                component_config["data_dir"] = "data"

            # Render component
            component.render(self.data, **component_config)

        except Exception as e:
            st.error(f"Error rendering {component_name}: {e}")

    def create_original_layout(self) -> DashboardLayout:
        """Create layout matching original streamlit_app.py exactly."""
        return DashboardLayout(
            title="Citation Analysis Dashboard",
            sidebar_sections=[
                LayoutConfig(
                    layout_type=LayoutType.SIDEBAR, components=["streamlit_app"], config={}
                )
            ],
            sections=[
                LayoutConfig(layout_type=LayoutType.MAIN, components=["streamlit_app"], config={})
            ],
        )


# Predefined layout templates
LAYOUT_TEMPLATES = {"original": lambda lm: lm.create_original_layout()}


def get_layout_template(name: str) -> Optional[Callable]:
    """Get layout template by name."""
    return LAYOUT_TEMPLATES.get(name)
