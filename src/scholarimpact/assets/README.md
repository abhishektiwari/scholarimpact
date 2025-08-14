# ScholarImpact Assets

This directory contains bundled assets for the ScholarImpact package.

## Files

- `config.toml` - Default Streamlit configuration with optimized settings
- Font files (*.ttf, *.otf, *.woff) - Custom fonts for dashboard theming

## Usage

Assets are automatically copied when using:

```bash
scholarimpact generate-dashboard
```

Or programmatically:

```python
from scholarimpact.assets import copy_streamlit_config, copy_fonts

# Copy config
copy_streamlit_config('.streamlit/')

# Copy fonts  
copy_fonts('.streamlit/')
```

## Adding Custom Assets

To add custom fonts or configurations:

1. Place font files in this directory
2. Update config.toml as needed
3. Reinstall package: `pip install -e .`