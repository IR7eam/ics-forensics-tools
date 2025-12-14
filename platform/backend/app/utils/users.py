"""Simple demo user registry parsing from settings."""

from typing import Dict, Tuple

from app.core.config import get_settings
from app.core.security import Role


def load_demo_users() -> Dict[str, Tuple[str, Role]]:
    settings = get_settings()
    registry: Dict[str, Tuple[str, Role]] = {}
    for entry in settings.demo_users:
        try:
            username, password, role = entry.split(":")
            registry[username] = (password, Role(role))
        except ValueError:
            continue
        except Exception:  # pragma: no cover - defensive parse guard
            continue
    return registry
