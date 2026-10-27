"""Image in -> density out. One call shared by the CLI and (later) the web API.

    detect vehicles -> PCU weight -> virtual zones -> zone + overall density
"""

from __future__ import annotations

import numpy as np

from density.estimator import estimate
from density.lane_calculation import ZoneLayout
from evaluation.visualize import draw
from detection.detector import detect


def analyze(model, image: np.ndarray, conf: float = 0.25, imgsz: int = 640,
            device: int | str | None = None, num_zones: int | None = None,
            horizon_y: float | None = None, vanishing_x: float | None = None,
            ) -> tuple[dict, np.ndarray]:
    """Density result + annotated image for one BGR image.

    num_zones / horizon_y / vanishing_x override configs/lanes.yaml when given.
    """
    h, w = image.shape[:2]
    layout = ZoneLayout.from_config(w, h, num_zones=num_zones, horizon_y=horizon_y,
                                    vanishing_x=vanishing_x)
    result = estimate(detect(model, image, conf=conf, imgsz=imgsz, device=device), layout)
    return result, draw(image, result, layout)
