from typing import List

from fastapi import APIRouter, Depends

from app.core.security import Role, require_role
from app.schemas.plugins import PluginSpecRead
from app.services.plugins import PLUGIN_REGISTRY

router = APIRouter(prefix="/plugins", tags=["plugins"])


@router.get("/", response_model=List[PluginSpecRead])
def list_plugins(current_user=Depends(require_role(Role.viewer))):
    """Return the registry of available protocol plugins and their safety posture."""

    return list(PLUGIN_REGISTRY.values())
