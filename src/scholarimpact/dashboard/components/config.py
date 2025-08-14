"""
Minimal configuration system for dashboard components.
"""

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional


@dataclass
class ComponentConfig:
    """Configuration for individual components."""

    name: str
    enabled: bool = True
    config: Dict[str, Any] = field(default_factory=dict)
    position: Optional[int] = None


@dataclass
class DashboardConfig:
    """Complete dashboard configuration."""

    title: str = "Citation Analysis Dashboard"
    layout_template: str = "original"
    theme: str = "auto"
    components: List[ComponentConfig] = field(default_factory=list)
    data_dir: str = "./data"
    custom_settings: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "DashboardConfig":
        """Create from dictionary."""
        components = []
        for comp_data in data.get("components", []):
            components.append(ComponentConfig(**comp_data))

        return cls(
            title=data.get("title", "Citation Analysis Dashboard"),
            layout_template=data.get("layout_template", "original"),
            theme=data.get("theme", "auto"),
            components=components,
            data_dir=data.get("data_dir", "./data"),
            custom_settings=data.get("custom_settings", {}),
        )


class ConfigManager:
    """Manager for dashboard and component configurations."""

    def __init__(self, config_file: Optional[str] = None):
        """Initialize config manager."""
        self.config_file = config_file
        self._config = None

    def load_config(self, config_file: Optional[str] = None) -> DashboardConfig:
        """Load configuration from file."""
        # Return default configuration
        self._config = self.get_default_config()
        return self._config

    def save_config(self, config: DashboardConfig, config_file: Optional[str] = None):
        """Save configuration to file."""
        pass  # Minimal implementation

    def get_default_config(self) -> DashboardConfig:
        """Get default dashboard configuration."""
        return DashboardConfig(
            title="Citation Analysis Dashboard",
            layout_template="original",
            theme="auto",
            components=[ComponentConfig(name="streamlit_app", enabled=True, config={})],
            data_dir="./data",
        )


# Preset configurations
PRESET_CONFIGS = {
    "original": DashboardConfig(
        title="Citation Analysis Dashboard",
        layout_template="original",
        components=[ComponentConfig("streamlit_app", enabled=True, config={})],
    )
}


# Configuration validation
class ConfigValidator:
    """Validator for dashboard configurations."""

    @staticmethod
    def validate_config(config: DashboardConfig) -> List[str]:
        """
        Validate dashboard configuration.

        Args:
            config: Configuration to validate

        Returns:
            List of validation errors (empty if valid)
        """
        errors = []

        # Validate required fields
        if not config.title:
            errors.append("Dashboard title is required")

        if not config.layout_template:
            errors.append("Layout template is required")

        # Validate layout template
        valid_templates = ["original"]
        if config.layout_template not in valid_templates:
            errors.append(
                f"Invalid layout template: {config.layout_template}. Must be one of {valid_templates}"
            )

        return errors

    @staticmethod
    def validate_component_config(component_name: str, config: Dict[str, Any]) -> List[str]:
        """
        Validate component-specific configuration.

        Args:
            component_name: Name of component
            config: Component configuration

        Returns:
            List of validation errors
        """
        errors = []
        # Minimal validation for streamlit_app component
        return errors


def get_preset_config(name: str) -> Optional[DashboardConfig]:
    """Get preset configuration by name."""
    return PRESET_CONFIGS.get(name)
