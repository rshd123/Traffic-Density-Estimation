"""Drawing helpers - zones, zone density tint, detections with PCU values."""

from __future__ import annotations

import cv2
import numpy as np

from density.lane_calculation import ZoneLayout

# BGR colour per PCU class id
COLORS = {
    2: (255, 160, 0),    # car - blue
    3: (0, 200, 255),    # motorcycle - yellow
    10: (0, 220, 0),     # auto-rickshaw - green
    5: (200, 0, 200),    # bus - purple
    7: (0, 100, 255),    # truck - orange
}
OFF_ROAD = (160, 160, 160)


def _text(img, text, org, scale, color, thickness):
    x, y = int(org[0]), int(org[1])
    (tw, th), base = cv2.getTextSize(text, cv2.FONT_HERSHEY_SIMPLEX, scale, thickness)
    cv2.rectangle(img, (x, y - th - base), (x + tw, y + base), (0, 0, 0), -1)
    cv2.putText(img, text, (x, y), cv2.FONT_HERSHEY_SIMPLEX, scale, color, thickness, cv2.LINE_AA)


def draw(image: np.ndarray, result: dict, layout: ZoneLayout) -> np.ndarray:
    """Annotated copy of a BGR image: red tint = denser zone, boxes labelled with PCU."""
    out = image.copy()
    h, w = out.shape[:2]
    scale = max(h / 720, 0.7)
    thick = max(int(round(scale * 1.5)), 1)

    # zone tint, stronger red for higher PCU density
    densities = [z["density"] for z in result["zones"]]
    top = max(densities) or 1.0
    zmap = cv2.resize(layout.zone_map(), (w, h), interpolation=cv2.INTER_NEAREST)
    alpha = np.zeros((h, w), np.float32)
    for i, d in enumerate(densities):
        alpha[zmap == i] = 0.45 * d / top
    red = np.zeros_like(out)
    red[:] = (0, 0, 255)
    a = alpha[..., None]
    out = (out * (1 - a) + red * a).astype(np.uint8)

    # horizon + zone boundaries
    vy = int(layout.vanishing_point[1])
    cv2.line(out, (0, vy), (w, vy), (255, 255, 255), thick, cv2.LINE_AA)
    for (x1, y1), (x2, y2) in layout.boundaries():
        cv2.line(out, (int(x1), int(y1)), (int(x2), int(y2)), (255, 255, 255), thick, cv2.LINE_AA)

    # vehicles
    for v in result["vehicles"]:
        x1, y1, x2, y2 = map(int, v["box"])
        color = COLORS.get(v["class_id"], OFF_ROAD) if v["zone"] is not None else OFF_ROAD
        cv2.rectangle(out, (x1, y1), (x2, y2), color, thick)
        _text(out, f"{v['label']} {v['pcu']:g}", (x1, max(y1 - 3, 12)), scale * 0.5, color, max(thick - 1, 1))

    # zone labels
    for z, (lx, ly) in zip(result["zones"], layout.label_points()):
        _text(out, f"L{z['zone'] + 1}: {z['pcu']:g} PCU", (lx - 40 * scale, ly), scale * 0.6,
              (255, 255, 255), max(thick - 1, 1))

    o = result["overall"]
    _text(out, f"{o['vehicles']} vehicles | {o['pcu']:g} PCU | density {o['density']:g}",
          (10, int(30 * scale) + 5), scale * 0.8, (255, 255, 255), thick)
    return out
