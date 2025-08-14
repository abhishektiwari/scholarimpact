"""Dashboard module for ScholarImpact."""

from .app import Dashboard
from .components import ComponentRegistry, LayoutManager, StreamlitAppComponent

__all__ = ["Dashboard", "ComponentRegistry", "LayoutManager", "StreamlitAppComponent"]
