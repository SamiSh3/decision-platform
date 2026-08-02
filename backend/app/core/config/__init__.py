"""Configuration package.

Re-exports the application `Settings` model and the memoized `get_settings()` /
`settings` singleton so existing imports (`from app.core.config import settings`)
keep working after the config module was split into its own subpackage.
"""

from app.core.config.settings import Settings, get_settings, settings

__all__ = ["Settings", "get_settings", "settings"]
