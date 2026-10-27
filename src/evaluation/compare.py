"""Actual vs predicted - compare the model's result with ground-truth labels.

Ground truth = a YOLO label file (one line per vehicle: class cx cy w h,
all normalized 0-1). It goes through the same PCU + lane calculation as the
model's detections, so the two results can be compared number for number.

Vehicles are also matched one to one by box overlap (IoU >= 0.5):
    correct     - matched, same vehicle type
    wrong_type  - matched, different type (e.g. truck called bus)
    missed      - real vehicle the model did not find
    extra       - model box with no real vehicle behind it (false alarm)
"""

from __future__ import annotations

from pathlib import Path

from density.estimator import estimate
from density.lane_calculation import ZoneLayout

ROOT = Path(__file__).resolve().parents[2]
SUBSET = ROOT / "data" / "subset"
SPLITS = ("test", "val", "train")


def find_labels(filename: str) -> tuple[str, Path] | None:
    """(split, label path) for a dataset image name, or None if not in the subset."""
    stem = Path(filename).stem
    for split in SPLITS:
        p = SUBSET / split / "labels" / f"{stem}.txt"
        if p.is_file():
            return split, p
    return None


def parse_labels(text: str, width: int, height: int) -> list[dict]:
    """YOLO label lines -> detections in pixels (conf 1.0)."""
    boxes = []
    for line in text.splitlines():
        p = line.split()
        if len(p) < 5:
            continue
        try:
            cid = int(float(p[0]))
            cx, cy, w, h = map(float, p[1:5])
        except ValueError:
            continue
        boxes.append({
            "class_id": cid,
            "conf": 1.0,
            "box": [round((cx - w / 2) * width, 1), round((cy - h / 2) * height, 1),
                    round((cx + w / 2) * width, 1), round((cy + h / 2) * height, 1)],
        })
    return boxes


def iou(a: list[float], b: list[float]) -> float:
    ix = max(0.0, min(a[2], b[2]) - max(a[0], b[0]))
    iy = max(0.0, min(a[3], b[3]) - max(a[1], b[1]))
    inter = ix * iy
    union = (a[2] - a[0]) * (a[3] - a[1]) + (b[2] - b[0]) * (b[3] - b[1]) - inter
    return inter / union if union > 0 else 0.0


def match(predicted: list[dict], actual: list[dict], threshold: float = 0.5) -> dict:
    """Greedy one-to-one box matching, highest overlap first."""
    pairs = sorted(
        ((iou(p["box"], a["box"]), i, j)
         for i, p in enumerate(predicted) for j, a in enumerate(actual)),
        reverse=True,
    )
    used_p, used_a, correct, wrong = set(), set(), 0, []
    for score, i, j in pairs:
        if score < threshold:
            break
        if i in used_p or j in used_a:
            continue
        used_p.add(i)
        used_a.add(j)
        if predicted[i]["class_id"] == actual[j]["class_id"]:
            correct += 1
        else:
            wrong.append({"actual": actual[j]["label"], "predicted": predicted[i]["label"]})
    return {
        "correct": correct,
        "wrong_type": len(wrong),
        "missed": len(actual) - len(used_a),
        "extra": len(predicted) - len(used_p),
        "wrong_type_details": wrong,
    }


def _on_road(result: dict) -> list[dict]:
    return [v for v in result["vehicles"] if v["zone"] is not None]


def _diff(pred: float, actual: float) -> dict:
    return {"predicted": pred, "actual": actual, "difference": round(pred - actual, 3)}


def compare(predicted: dict, actual: dict) -> dict:
    """Side-by-side numbers for two estimator results (model vs ground truth)."""
    po, ao = predicted["overall"], actual["overall"]
    lanes = [
        {"zone": p["zone"], "vehicles": _diff(p["vehicles"], a["vehicles"]),
         "pcu": _diff(p["pcu"], a["pcu"]), "density": _diff(p["density"], a["density"])}
        for p, a in zip(predicted["zones"], actual["zones"])
    ]
    by_class = [
        {"class_id": p["class_id"], "label": p["label"],
         "count": _diff(p["count"], a["count"]), "pcu": _diff(p["pcu"], a["pcu"])}
        for p, a in zip(predicted["by_class"], actual["by_class"])
    ]
    pcu_error_pct = (round(100 * abs(po["pcu"] - ao["pcu"]) / ao["pcu"], 1)
                     if ao["pcu"] else None)
    return {
        "overall": {
            "vehicles": _diff(po["vehicles"], ao["vehicles"]),
            "pcu": _diff(po["pcu"], ao["pcu"]),
            "density": _diff(po["density"], ao["density"]),
            "pcu_error_pct": pcu_error_pct,
            "lane_pcu_mae": round(sum(abs(l["pcu"]["difference"]) for l in lanes) / len(lanes), 3),
        },
        "by_class": by_class,
        "lanes": lanes,
        "matching": match(_on_road(predicted), _on_road(actual)),
    }


def ground_truth(text: str, layout: ZoneLayout) -> dict:
    """Estimator result built from a label file instead of the model."""
    return estimate(parse_labels(text, layout.width, layout.height), layout)

