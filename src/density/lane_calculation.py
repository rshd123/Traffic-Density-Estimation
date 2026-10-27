"""Virtual spatial zones - lane-free strips that follow the road's perspective.

Lane markings on Chennai roads are often missing or ignored, so instead of
lanes the road (everything below the horizon) is split into N wedge-shaped
strips of equal angle that fan out from the vanishing point. Like real lanes
in a photo, each strip is thin far away and wide near the camera.

A vehicle goes into the strip that holds its ground point: the bottom-centre
of its box, where the wheels touch the road.

Zones are numbered 0..N-1 from left to right. Points on or above the horizon
are not on the road and get zone None.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from functools import cached_property
from pathlib import Path

import numpy as np
import yaml

ROOT = Path(__file__).resolve().parents[2]
CONFIG = ROOT / "configs" / "lanes.yaml"

Point = tuple[float, float]


def load_config(path: str | Path = CONFIG) -> dict:
    path = Path(path)
    if not path.is_file():
        return {}
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


@dataclass(frozen=True)
class ZoneLayout:
    width: int
    height: int
    num_zones: int = 5
    horizon_y: float = 0.42   # fraction of image height
    vanishing_x: float = 0.5  # fraction of image width

    def __post_init__(self):
        if self.num_zones < 1:
            raise ValueError("num_zones must be >= 1")
        if not 0.0 <= self.horizon_y < 1.0:
            raise ValueError("horizon_y must be in [0, 1)")

    @classmethod
    def from_config(cls, width: int, height: int, path: str | Path = CONFIG,
                    **overrides) -> "ZoneLayout":
        """Layout from configs/lanes.yaml; non-None overrides win."""
        cfg = load_config(path)
        cfg.update({k: v for k, v in overrides.items() if v is not None})
        return cls(
            width=int(width),
            height=int(height),
            num_zones=int(cfg.get("num_zones", cls.num_zones)),
            horizon_y=float(cfg.get("horizon_y", cls.horizon_y)),
            vanishing_x=float(cfg.get("vanishing_x", cls.vanishing_x)),
        )

    @property
    def vanishing_point(self) -> Point:
        return self.vanishing_x * self.width, self.horizon_y * self.height

    def _index(self, angle):
        # angle 0 = straight left of the vanishing point, pi = straight right
        return np.minimum((angle / math.pi * self.num_zones).astype(int), self.num_zones - 1)

    def zone_of(self, x: float, y: float) -> int | None:
        """Zone index for a ground point in pixels, or None above the horizon."""
        vx, vy = self.vanishing_point
        if y <= vy:
            return None
        return int(self._index(np.float64(math.atan2(y - vy, vx - x))))

    def zone_map(self, step: int = 4) -> np.ndarray:
        """Zone index for every step-th pixel (rows x cols); -1 above the horizon."""
        vx, vy = self.vanishing_point
        ys, xs = np.mgrid[step / 2:self.height:step, step / 2:self.width:step]
        zones = self._index(np.arctan2(ys - vy, vx - xs))
        return np.where(ys > vy, zones, -1)

    @cached_property
    def areas(self) -> list[float]:
        """Share of the image each zone covers (0-1); together = the road's share."""
        m = self.zone_map()
        return [float((m == i).mean()) for i in range(self.num_zones)]

    def _ray_end(self, angle: float) -> Point:
        """Where a ray from the vanishing point at this angle leaves the image."""
        vx, vy = self.vanishing_point
        dx, dy = -math.cos(angle), math.sin(angle)
        hits = [(self.height - vy) / dy if dy > 1e-9 else math.inf]
        if dx < -1e-9:
            hits.append(-vx / dx)
        elif dx > 1e-9:
            hits.append((self.width - vx) / dx)
        t = min(hits)
        return vx + t * dx, vy + t * dy

    def boundaries(self) -> list[tuple[Point, Point]]:
        """Line segments between neighbouring zones (for drawing)."""
        vp = self.vanishing_point
        return [(vp, self._ray_end(k * math.pi / self.num_zones))
                for k in range(1, self.num_zones)]

    def label_points(self, depth: float = 0.8) -> list[Point]:
        """A point inside each zone (along its middle ray) to place its label."""
        vx, vy = self.vanishing_point
        points = []
        for i in range(self.num_zones):
            ex, ey = self._ray_end((i + 0.5) * math.pi / self.num_zones)
            points.append((vx + depth * (ex - vx), vy + depth * (ey - vy)))
        return points

    def to_dict(self) -> dict:
        return {
            "num_zones": self.num_zones,
            "horizon_y": self.horizon_y,
            "vanishing_x": self.vanishing_x,
            "vanishing_point": [round(v, 1) for v in self.vanishing_point],
            "boundaries": [[[round(v, 1) for v in a], [round(v, 1) for v in b]]
                           for a, b in self.boundaries()],
        }
