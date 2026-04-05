"""Timeline operations — zoom, speed, trim, crop, and annotation regions.

Each region type maps directly to Openscreen's data model:
- ZoomRegion: startMs, endMs, depth (1-6), focus (cx, cy), focusMode
- SpeedRegion: startMs, endMs, speed (0.25-2.0)
- TrimRegion: startMs, endMs
- AnnotationRegion: startMs, endMs, type, content, position, size, style
- CropRegion: x, y, width, height (all normalized 0-1)
"""

import uuid
from typing import Optional

from .session import Session


# ── Constants ────────────────────────────────────────────────────────────

ZOOM_DEPTHS = {1: 1.25, 2: 1.5, 3: 1.8, 4: 2.2, 5: 3.5, 6: 5.0}
VALID_SPEEDS = [0.25, 0.5, 0.75, 1.25, 1.5, 1.75, 2.0]
ANNOTATION_TYPES = ["text", "image", "figure"]
ARROW_DIRECTIONS = [
    "up", "down", "left", "right",
    "up-right", "up-left", "down-right", "down-left",
]


def _gen_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"


# ── Zoom regions ─────────────────────────────────────────────────────────

def list_zoom_regions(session: Session) -> list[dict]:
    """List all zoom regions."""
    if not session.is_open:
        raise RuntimeError("No project is open")
    return session.editor.get("zoomRegions", [])


def add_zoom_region(
    session: Session,
    start_ms: int,
    end_ms: int,
    depth: int = 3,
    focus_x: float = 0.5,
    focus_y: float = 0.5,
    focus_mode: str = "manual",
) -> dict:
    """Add a zoom region to the timeline."""
    if not session.is_open:
        raise RuntimeError("No project is open")
    if depth not in ZOOM_DEPTHS:
        raise ValueError(f"Invalid depth {depth}. Valid: {list(ZOOM_DEPTHS.keys())}")
    if not 0 <= focus_x <= 1 or not 0 <= focus_y <= 1:
        raise ValueError("Focus coordinates must be 0.0-1.0")
    if end_ms <= start_ms:
        raise ValueError("end_ms must be > start_ms")

    session.checkpoint()
    region = {
        "id": _gen_id("zoom"),
        "startMs": start_ms,
        "endMs": end_ms,
        "depth": depth,
        "focus": {"cx": focus_x, "cy": focus_y},
        "focusMode": focus_mode,
    }
    session.editor.setdefault("zoomRegions", []).append(region)
    return region


def remove_zoom_region(session: Session, region_id: str) -> dict:
    """Remove a zoom region by ID."""
    if not session.is_open:
        raise RuntimeError("No project is open")
    session.checkpoint()
    regions = session.editor.get("zoomRegions", [])
    before = len(regions)
    session.editor["zoomRegions"] = [r for r in regions if r["id"] != region_id]
    removed = before - len(session.editor["zoomRegions"])
    if removed == 0:
        raise ValueError(f"Zoom region not found: {region_id}")
    return {"status": "removed", "id": region_id}


# ── Speed regions ────────────────────────────────────────────────────────

def list_speed_regions(session: Session) -> list[dict]:
    """List all speed regions."""
    if not session.is_open:
        raise RuntimeError("No project is open")
    return session.editor.get("speedRegions", [])


def add_speed_region(
    session: Session,
    start_ms: int,
    end_ms: int,
    speed: float = 1.5,
) -> dict:
    """Add a speed region to the timeline."""
    if not session.is_open:
        raise RuntimeError("No project is open")
    if speed not in VALID_SPEEDS:
        raise ValueError(f"Invalid speed {speed}. Valid: {VALID_SPEEDS}")
    if end_ms <= start_ms:
        raise ValueError("end_ms must be > start_ms")

    session.checkpoint()
    region = {
        "id": _gen_id("speed"),
        "startMs": start_ms,
        "endMs": end_ms,
        "speed": speed,
    }
    session.editor.setdefault("speedRegions", []).append(region)
    return region


def remove_speed_region(session: Session, region_id: str) -> dict:
    """Remove a speed region by ID."""
    if not session.is_open:
        raise RuntimeError("No project is open")
    session.checkpoint()
    regions = session.editor.get("speedRegions", [])
    before = len(regions)
    session.editor["speedRegions"] = [r for r in regions if r["id"] != region_id]
    if before - len(session.editor["speedRegions"]) == 0:
        raise ValueError(f"Speed region not found: {region_id}")
    return {"status": "removed", "id": region_id}


# ── Trim regions ─────────────────────────────────────────────────────────

def list_trim_regions(session: Session) -> list[dict]:
    """List all trim regions."""
    if not session.is_open:
        raise RuntimeError("No project is open")
    return session.editor.get("trimRegions", [])


def add_trim_region(session: Session, start_ms: int, end_ms: int) -> dict:
    """Add a trim (cut) region to the timeline."""
    if not session.is_open:
        raise RuntimeError("No project is open")
    if end_ms <= start_ms:
        raise ValueError("end_ms must be > start_ms")

    session.checkpoint()
    region = {
        "id": _gen_id("trim"),
        "startMs": start_ms,
        "endMs": end_ms,
    }
    session.editor.setdefault("trimRegions", []).append(region)
    return region


def remove_trim_region(session: Session, region_id: str) -> dict:
    """Remove a trim region by ID."""
    if not session.is_open:
        raise RuntimeError("No project is open")
    session.checkpoint()
    regions = session.editor.get("trimRegions", [])
    before = len(regions)
    session.editor["trimRegions"] = [r for r in regions if r["id"] != region_id]
    if before - len(session.editor["trimRegions"]) == 0:
        raise ValueError(f"Trim region not found: {region_id}")
    return {"status": "removed", "id": region_id}


# ── Crop ─────────────────────────────────────────────────────────────────

def get_crop(session: Session) -> dict:
    """Get current crop region."""
    if not session.is_open:
        raise RuntimeError("No project is open")
    return session.editor.get("cropRegion", {"x": 0, "y": 0, "width": 1, "height": 1})


def set_crop(session: Session, x: float, y: float, w: float, h: float) -> dict:
    """Set crop region (all values normalized 0-1)."""
    if not session.is_open:
        raise RuntimeError("No project is open")
    for val, name in [(x, "x"), (y, "y"), (w, "width"), (h, "height")]:
        if not 0 <= val <= 1:
            raise ValueError(f"{name} must be 0.0-1.0, got {val}")
    if x + w > 1.001 or y + h > 1.001:
        raise ValueError("Crop region extends beyond frame boundaries")

    session.checkpoint()
    session.editor["cropRegion"] = {"x": x, "y": y, "width": w, "height": h}
    return session.editor["cropRegion"]


# ── Annotations ──────────────────────────────────────────────────────────

def list_annotations(session: Session) -> list[dict]:
    """List all annotation regions."""
    if not session.is_open:
        raise RuntimeError("No project is open")
    return session.editor.get("annotationRegions", [])


def add_text_annotation(
    session: Session,
    start_ms: int,
    end_ms: int,
    text: str,
    x: float = 0.5,
    y: float = 0.5,
    font_size: int = 32,
    color: str = "#ffffff",
    bg_color: str = "#000000",
) -> dict:
    """Add a text annotation to the timeline."""
    if not session.is_open:
        raise RuntimeError("No project is open")
    if end_ms <= start_ms:
        raise ValueError("end_ms must be > start_ms")

    session.checkpoint()
    region = {
        "id": _gen_id("ann"),
        "startMs": start_ms,
        "endMs": end_ms,
        "type": "text",
        "textContent": text,
        "content": text,
        "position": {"x": x, "y": y},
        "size": {"width": 0.3, "height": 0.1},
        "style": {
            "color": color,
            "backgroundColor": bg_color,
            "fontSize": font_size,
            "fontFamily": "Inter",
            "fontWeight": "normal",
            "fontStyle": "normal",
            "textDecoration": "none",
            "textAlign": "center",
        },
        "zIndex": 1,
    }
    session.editor.setdefault("annotationRegions", []).append(region)
    return region


def remove_annotation(session: Session, region_id: str) -> dict:
    """Remove an annotation by ID."""
    if not session.is_open:
        raise RuntimeError("No project is open")
    session.checkpoint()
    regions = session.editor.get("annotationRegions", [])
    before = len(regions)
    session.editor["annotationRegions"] = [r for r in regions if r["id"] != region_id]
    if before - len(session.editor["annotationRegions"]) == 0:
        raise ValueError(f"Annotation not found: {region_id}")
    return {"status": "removed", "id": region_id}
