"""PCU-weighted traffic density - per zone and for the whole road.

    zone density    = PCU in the zone / zone area
    overall density = PCU on the road / road area

Areas are shares of the image (whole image = 1), so the numbers do not depend
on the photo's resolution. Plain vehicle counts are reported next to PCU
(count_density) so both can be compared - the project's main baseline.

Only the 5 PCU classes count; every other detection (pedestrian, sign, ...)
is ignored. Vehicles above the horizon are listed but left out of density.
"""

from __future__ import annotations

from density import pcu
from density.lane_calculation import ZoneLayout


def _density(value: float, area: float) -> float:
    return round(value / area, 3) if area > 0 else 0.0


def estimate(detections: list[dict], layout: ZoneLayout) -> dict:
    """Density result for one image.

    detections: dicts with class_id, conf, box [x1, y1, x2, y2] in pixels.
    """
    vehicles, ignored = [], 0
    for d in detections:
        w = pcu.weight(d["class_id"])
        if w is None:
            ignored += 1
            continue
        x1, _, x2, y2 = d["box"]
        vehicles.append({
            **d,
            "label": pcu.label(d["class_id"]),
            "pcu": w,
            "zone": layout.zone_of((x1 + x2) / 2, y2),  # ground point
        })

    zones = []
    for i, area in enumerate(layout.areas):
        inside = [v for v in vehicles if v["zone"] == i]
        total = sum(v["pcu"] for v in inside)
        zones.append({
            "zone": i,
            "vehicles": len(inside),
            "pcu": round(total, 2),
            "area": round(area, 4),
            "density": _density(total, area),
            "count_density": _density(len(inside), area),
        })

    on_road = [v for v in vehicles if v["zone"] is not None]
    road_area = sum(layout.areas)
    total = sum(v["pcu"] for v in on_road)
    by_class = [
        {"class_id": cid, "label": pcu.label(cid),
         "count": sum(v["class_id"] == cid for v in on_road),
         "pcu": round(sum(v["pcu"] for v in on_road if v["class_id"] == cid), 2)}
        for cid in pcu.class_ids()
    ]

    return {
        "width": layout.width,
        "height": layout.height,
        "zones_layout": layout.to_dict(),
        "overall": {
            "vehicles": len(on_road),
            "pcu": round(total, 2),
            "area": round(road_area, 4),
            "density": _density(total, road_area),
            "count_density": _density(len(on_road), road_area),
            "busiest_zone": max(zones, key=lambda z: z["density"])["zone"] if total else None,
        },
        "by_class": by_class,
        "zones": zones,
        "vehicles": vehicles,
        "off_road": len(vehicles) - len(on_road),
        "ignored_detections": ignored,
    }
