from collections.abc import Mapping
from typing import Any

from sqlalchemy.orm import Session

from app.core.exceptions import (
    DeviceTypeUndeterminedException,
    GNS3RequestException,
)
from app.models.user import User
from app.services.Gns3.Nodes import get_node as get_gns3_node
from app.services.Gns3.Templates import get_template as get_gns3_template
from app.services.projectService import get_project_by_id


DEVICE_TYPES = frozenset({"router", "switch", "host"})

# Template IDs are stable only within one GNS3 environment. Add an explicit
# override here when an environment has stable IDs that should take priority.
TEMPLATE_ID_DEVICE_TYPES: dict[str, str] = {}

# GNS3 template categories are the primary portable classification signal.
CATEGORY_DEVICE_TYPES = {
    "router": "router",
    "routers": "router",
    "switch": "switch",
    "switches": "switch",
    "host": "host",
    "hosts": "host",
    "end device": "host",
    "end devices": "host",
    "guest": "host",
    "guests": "host",
}

# These are deliberate exact template-name fallbacks for common GNS3
# templates, not endpoint-level heuristics.
TEMPLATE_NAME_DEVICE_TYPES = {
    "cisco iosv": "router",
    "cisco iosvl2": "switch",
    "iosvl2": "switch",
    "vpcs": "host",
}

TEMPLATE_TYPE_DEVICE_TYPES = {
    "vpcs": "host",
    "ethernet switch": "switch",
}


def _normalise(value: object) -> str:
    return " ".join(str(value).strip().lower().replace("_", " ").replace("-", " ").split())


def get_device_type(template: Mapping[str, Any] | None) -> str | None:
    """Return a logical device type from a GNS3 template, or ``None`` safely."""
    if not template:
        return None

    explicit_type = template.get("device_type")
    if explicit_type in DEVICE_TYPES:
        return explicit_type

    template_id = template.get("template_id")
    if template_id and template_id in TEMPLATE_ID_DEVICE_TYPES:
        return TEMPLATE_ID_DEVICE_TYPES[template_id]

    category_type = CATEGORY_DEVICE_TYPES.get(_normalise(template.get("category", "")))
    if category_type:
        return category_type

    template_type = TEMPLATE_TYPE_DEVICE_TYPES.get(_normalise(template.get("template_type", "")))
    if template_type:
        return template_type

    return TEMPLATE_NAME_DEVICE_TYPES.get(_normalise(template.get("name", "")))


async def get_node_device_type(
    db: Session,
    project_id: int,
    node_id: str,
    current_user: User,
) -> str:
    """Resolve and classify a node through its GNS3 template relationship."""
    project = get_project_by_id(
        db=db,
        project_id=project_id,
        current_user=current_user,
    )
    node = await get_gns3_node(str(project.project_id), node_id)
    template_id = node.get("template_id")

    if not template_id:
        raise DeviceTypeUndeterminedException(
            "The device type could not be determined for this node."
        )

    try:
        template = await get_gns3_template(template_id)
    except GNS3RequestException as exc:
        # The GNS3 server responded, but this node's template is no longer a
        # resolvable classification dependency. GNS3UnreachableException is
        # deliberately not caught so infrastructure failures remain distinct.
        raise DeviceTypeUndeterminedException(
            "The device type could not be determined for this node."
        ) from exc

    device_type = get_device_type(template)

    if not device_type:
        raise DeviceTypeUndeterminedException(
            "The device type could not be determined for this node."
        )

    return device_type
