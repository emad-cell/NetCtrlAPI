from io import BytesIO
from typing import Any

from PIL import Image, ImageDraw

NODE_SIZE = 60
PADDING = 80
BACKGROUND_COLOR = "white"
NODE_FILL_COLOR = "#f0f0f0"
NODE_OUTLINE_COLOR = "black"
LINK_COLOR = "black"
TEXT_COLOR = "black"


def render_topology_image(
    nodes: list[dict[str, Any]],
    links: list[dict[str, Any]],
) -> bytes:

    if not nodes:
        return _render_empty_image()

    min_x = min(node["x"] for node in nodes)
    max_x = max(node["x"] for node in nodes)
    min_y = min(node["y"] for node in nodes)
    max_y = max(node["y"] for node in nodes)

    width = (max_x - min_x) + NODE_SIZE + (PADDING * 2)
    height = (max_y - min_y) + NODE_SIZE + (PADDING * 2) + 20

    image = Image.new("RGB", (int(width), int(height)), BACKGROUND_COLOR)
    draw = ImageDraw.Draw(image)

    positions: dict[str, tuple[int, int]] = {}

    for node in nodes:
        center_x = (node["x"] - min_x) + PADDING + (NODE_SIZE // 2)
        center_y = (node["y"] - min_y) + PADDING + (NODE_SIZE // 2)
        positions[node["node_id"]] = (center_x, center_y)

    for link in links:
        link_nodes = link.get("nodes", [])

        if len(link_nodes) != 2:
            continue

        node_id_a = link_nodes[0].get("node_id")
        node_id_b = link_nodes[1].get("node_id")

        if node_id_a not in positions or node_id_b not in positions:
            continue

        draw.line(
            [positions[node_id_a], positions[node_id_b]],
            fill=LINK_COLOR,
            width=2,
        )

    for node in nodes:
        center_x, center_y = positions[node["node_id"]]

        left = center_x - (NODE_SIZE // 2)
        top = center_y - (NODE_SIZE // 2)
        right = center_x + (NODE_SIZE // 2)
        bottom = center_y + (NODE_SIZE // 2)

        draw.rectangle(
            [left, top, right, bottom],
            outline=NODE_OUTLINE_COLOR,
            fill=NODE_FILL_COLOR,
            width=2,
        )

        name = node.get("name", "")

        text_bbox = draw.textbbox((0, 0), name)
        text_width = text_bbox[2] - text_bbox[0]

        draw.text(
            (center_x - (text_width // 2), bottom + 6),
            name,
            fill=TEXT_COLOR,
        )

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


def _render_empty_image() -> bytes:
    image = Image.new("RGB", (400, 150), BACKGROUND_COLOR)
    draw = ImageDraw.Draw(image)
    draw.text((20, 65), "No nodes in this project", fill=TEXT_COLOR)

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()