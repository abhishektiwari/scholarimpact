"""
Main Dashboard class for ScholarImpact.

This module provides the Dashboard class with modern component-based architecture.
"""

import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional

import streamlit as st

from ..data.loader import load_data
from .components import ComponentRegistry, LayoutManager, get_layout_template
from .components.config import ConfigManager, DashboardConfig, get_preset_config

logger = logging.getLogger(__name__)


class Dashboard:
    """Main Dashboard class for creating Streamlit citation analysis apps."""

    def __init__(
        self,
        data_dir: str = "./data",
        title: str = "Citation Analysis Dashboard",
        config_file: Optional[str] = None,
        layout_template: str = "default",
        preset: Optional[str] = None,
        host: str = "localhost",
        port: int = 8501,
    ):
        """
        Initialize the Dashboard.

        Args:
            data_dir: Directory containing citation data
            title: Dashboard title
            config_file: Path to configuration file
            layout_template: Layout template name
            preset: Preset configuration name
            host: Host to bind to
            port: Port to run on
        """
        self.data_dir = Path(data_dir)
        self.host = host
        self.port = port

        # Load configuration
        if config_file:
            self.config_manager = ConfigManager(config_file)
            self.config = self.config_manager.load_config()
        elif preset:
            self.config = get_preset_config(preset)
            if not self.config:
                raise ValueError(f"Preset '{preset}' not found")
        else:
            # Create default configuration
            self.config_manager = ConfigManager()
            self.config = self.config_manager.get_default_config()
            self.config.title = title
            self.config.layout_template = layout_template
            self.config.data_dir = data_dir

        # Verify data directory exists
        if not self.data_dir.exists():
            logger.warning(f"Data directory {self.data_dir} does not exist")

    @classmethod
    def from_config(cls, config_path: str, **kwargs):
        """
        Create dashboard from configuration file.

        Args:
            config_path: Path to configuration file
            **kwargs: Additional keyword arguments

        Returns:
            Dashboard instance
        """
        import yaml

        with open(config_path, "r") as f:
            config = yaml.safe_load(f)

        return cls(config=config, **kwargs)

    def run(self, port: Optional[int] = None, debug: bool = False):
        """
        Run the Streamlit dashboard.

        Args:
            port: Port to run dashboard on (optional, uses instance port)
            debug: Enable debug mode
        """
        # Check if we're already running in Streamlit context
        try:
            import streamlit as st
            # If we can access Streamlit's runtime, we're already in a Streamlit app
            if hasattr(st, 'runtime') and st.runtime.exists():
                # Just render directly, no subprocess needed
                self.render_app()
                return
        except:
            # Not in Streamlit context or error checking, proceed with subprocess
            pass

        if port is None:
            port = self.port

        # Create dashboard app code
        dashboard_code = self._generate_component_dashboard_code()

        # Write to temporary file
        temp_file = Path("_temp_component_dashboard.py")
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(dashboard_code)

        try:
            # Run streamlit
            logger.info(f"Launching dashboard on http://{self.host}:{port}")
            cmd = [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                str(temp_file),
                "--server.port",
                str(port),
                "--server.address",
                self.host,
            ]

            if not debug:
                cmd.extend(["--server.headless", "true"])

            subprocess.run(cmd)
        except KeyboardInterrupt:
            logger.info("Dashboard stopped by user")
        finally:
            # Clean up temporary file
            if temp_file.exists():
                temp_file.unlink()

    def render_app(self):
        """
        Render the dashboard app directly (for use in existing Streamlit context).
        """
        # Set page config exactly as in original streamlit_app.py
        st.set_page_config(
            page_title="Citation Analysis Dashboard",
            page_icon=None,
            layout="wide",
            initial_sidebar_state="expanded",
        )

        # Load data
        try:
            data = load_data(str(self.data_dir))
            if not data:
                st.error("No citation data found. Please run citation crawler first.")
                st.info("Run: `scholarimpact extract-author YOUR_SCHOLAR_ID`")
                return

        except Exception as e:
            st.error(f"Error loading data: {e}")
            return

        # Title and description exactly as in original
        st.title("Citation Analysis Dashboard")

        # Create layout manager with the data
        layout_manager = LayoutManager(data)

        # Create the streamlit app component
        app_component = layout_manager.create_component("streamlit_app")
        if app_component:
            app_component.render(data, data_dir=str(self.data_dir))
        else:
            st.error("Could not create streamlit app component")

    def _generate_component_dashboard_code(self) -> str:
        """
        Generate the component-based dashboard code.

        Returns:
            Python code string for the dashboard
        """
        import json

        # Convert config to JSON, then fix boolean syntax for Python
        config_json = json.dumps(self.config.to_dict(), indent=2)
        # Replace JSON booleans with Python booleans
        config_json = (
            config_json.replace("true", "True").replace("false", "False").replace("null", "None")
        )

        return f"""
# Component-based ScholarImpact Dashboard
# Auto-generated by Dashboard.run()

import sys
from pathlib import Path

# Add scholarimpact package to path
package_path = Path(__file__).parent
while package_path.name != "scholarimpact" and package_path.parent != package_path:
    package_path = package_path.parent
    
if package_path.name == "scholarimpact":
    sys.path.insert(0, str(package_path.parent))

try:
    from scholarimpact.dashboard.app import Dashboard
    from scholarimpact.dashboard.components.config import DashboardConfig
    
    # Embedded configuration
    config_data = {config_json}
    
    # Create dashboard config
    config = DashboardConfig.from_dict(config_data)
    
    # Create dashboard instance
    dashboard = Dashboard.__new__(Dashboard)
    dashboard.config = config
    dashboard.data_dir = Path("{self.data_dir}")
    dashboard.host = "{self.host}"
    dashboard.port = {self.port}
    
    # Render the app
    dashboard.render_app()
    
except Exception as e:
    import streamlit as st
    st.error(f"Error loading dashboard: {{e}}")
    st.info("This may be due to missing dependencies or incorrect package installation.")
    st.code(str(e))
"""

    def export_config(self, path: str):
        """
        Export current dashboard configuration.

        Args:
            path: Path to save configuration file
        """
        if hasattr(self, "config_manager") and self.config_manager:
            self.config_manager.save_config(self.config, path)
        else:
            config_manager = ConfigManager()
            config_manager.save_config(self.config, path)

    def get_component_config(self, component_name: str) -> Dict[str, Any]:
        """
        Get configuration for a specific component.

        Args:
            component_name: Name of component

        Returns:
            Component configuration dictionary
        """
        for comp in self.config.components:
            if comp.name == component_name and comp.enabled:
                return comp.config
        return {}

    def update_component_config(self, component_name: str, config: Dict[str, Any]):
        """
        Update configuration for a specific component.

        Args:
            component_name: Name of component
            config: New configuration options
        """
        for comp in self.config.components:
            if comp.name == component_name:
                comp.config.update(config)
                return

        # Add new component if not found
        from .components.config import ComponentConfig

        self.config.components.append(ComponentConfig(name=component_name, config=config))

    @classmethod
    def create_preset(cls, preset_name: str, **kwargs):
        """
        Create dashboard from preset configuration.

        Args:
            preset_name: Name of preset ('minimal', 'research', 'overview')
            **kwargs: Additional arguments

        Returns:
            Dashboard instance
        """
        return cls(preset=preset_name, **kwargs)

    def list_components(self) -> List[str]:
        """
        List enabled components in this dashboard.

        Returns:
            List of enabled component names
        """
        return [comp.name for comp in self.config.components if comp.enabled]
