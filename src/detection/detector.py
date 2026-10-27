"""YOLO detector - training and inference for the DriveIndia subset.

torch / ultralytics are imported inside the functions so the rest of the
project (preprocessor, pcu) keeps working without the training deps.

Usage (tde conda env):
    python src/main.py train
    python src/main.py train --epochs 50 --batch 16 --device 0
"""

from __future__ import annotations

from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA_YAML = ROOT / "configs" / "data.yaml"
WEIGHTS_DIR = ROOT / "weights"
RUNS_DIR = ROOT / "runs" / "detect"


def resolve_model(model: str = "yolo26n.pt") -> str:
    """Prefer a non-empty local copy in weights/, else let ultralytics fetch."""
    local = WEIGHTS_DIR / Path(model).name
    if local.is_file() and local.stat().st_size > 0:
        return str(local)
    p = Path(model)
    if p.is_file() and p.stat().st_size > 0:
        return str(p)
    return model


def load(weights: str = "yolo26n_best.pt"):
    """Load detector weights (looked up in weights/ first)."""
    from ultralytics import YOLO

    return YOLO(resolve_model(weights))


def detect(model, image, conf: float = 0.25, imgsz: int = 640,
           device: int | str | None = None) -> list[dict]:
    """Run the detector on one image (path or BGR array).

    Returns one dict per box: class_id, conf, box [x1, y1, x2, y2] in pixels.
    """
    r = model.predict(image, conf=conf, imgsz=imgsz, device=device, verbose=False)[0]
    b = r.boxes
    return [
        {"class_id": int(c), "conf": round(float(s), 3), "box": [round(float(v), 1) for v in xyxy]}
        for c, s, xyxy in zip(b.cls.tolist(), b.conf.tolist(), b.xyxy.tolist())
    ]


def train(
    data: str | Path = DATA_YAML,
    model: str = "yolo26n.pt",
    epochs: int = 50,
    imgsz: int = 640,
    batch: int = 16,
    device: int | str = 0,
    patience: int = 15,
    cache: str = "ram",
    workers: int = 8,
    project: str | Path = RUNS_DIR,
    name: str = "train",
) -> Path:
    """Transfer-learn the detector on the DriveIndia subset.

    Returns the path of the copied best checkpoint (weights/*_best.pt).
    """
    from ultralytics import YOLO

    data = Path(data)
    if not data.is_file():
        raise SystemExit(
            f"missing dataset config: {data}\n"
            "run: python src/data/preprocessor.py build && python src/data/preprocessor.py config"
        )

    src = resolve_model(model)
    yolo = YOLO(src)

    results = yolo.train(
        data=str(data),
        epochs=epochs,
        imgsz=imgsz,
        batch=batch,
        device=device,
        patience=patience,
        cache=False if cache == "none" else cache,
        workers=workers,
        project=str(project),
        name=name,
        exist_ok=True,
    )

    best = Path(results.save_dir) / "weights" / "best.pt"
    if not best.is_file():
        raise SystemExit(f"training finished without best.pt in {results.save_dir}")
    WEIGHTS_DIR.mkdir(parents=True, exist_ok=True)
    dest = WEIGHTS_DIR / f"{Path(src).stem}_best.pt"
    dest.write_bytes(best.read_bytes())
    print(f"best checkpoint -> {dest}")
    return dest
