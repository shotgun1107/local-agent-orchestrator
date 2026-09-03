"""Legacy configuration migration."""

from .legacy import migrate_config, migrate_v1_to_v2

__all__ = ["migrate_config", "migrate_v1_to_v2"]
