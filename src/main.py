"""Traffic Density Estimation - CLI entry.

Usage (tde conda env):
    python src/main.py train
    python src/main.py train --epochs 50 --batch 16 --device 0
    python src/main.py predict photo.jpg
    python src/main.py predict data/subset/test/images --zones 3
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))


IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def _device(value: str | None) -> int | str | None:
    if value is None:
        return None
    return int(value) if value.lstrip("-").isdigit() else value


def _images(paths: list[str]) -> list[Path]:
    files = []
    for p in map(Path, paths):
        if p.is_dir():
            files += sorted(f for f in p.iterdir() if f.suffix.lower() in IMAGE_EXTS)
        elif p.is_file():
            files.append(p)
        else:
            raise SystemExit(f"not found: {p}")
    return files


def cmd_train(args) -> None:
    from detection.detector import train

    train(
        data=args.data,
        model=args.model,
        epochs=args.epochs,
        imgsz=args.imgsz,
        batch=args.batch,
        device=_device(args.device),
        patience=args.patience,
        cache=args.cache,
        workers=args.workers,
    )


def cmd_predict(args) -> None:
    import json

    import cv2

    from detection.detector import load
    from pipeline import analyze

    files = _images(args.images)
    out_dir = Path(args.out)
    out_dir.mkdir(parents=True, exist_ok=True)
    model = load(args.weights)

    for f in files:
        image = cv2.imread(str(f))
        if image is None:
            print(f"skip (not an image): {f}")
            continue
        result, annotated = analyze(
            model, image, conf=args.conf, imgsz=args.imgsz, device=_device(args.device),
            num_zones=args.zones, horizon_y=args.horizon, vanishing_x=args.vanish_x,
        )
        result["image"] = f.name
        cv2.imwrite(str(out_dir / f"{f.stem}_density.jpg"), annotated)
        (out_dir / f"{f.stem}_density.json").write_text(json.dumps(result, indent=2), encoding="utf-8")

        o = result["overall"]
        zones = "  ".join(f"Z{z['zone'] + 1}={z['pcu']:g}" for z in result["zones"])
        print(f"{f.name}: {o['vehicles']} vehicles, {o['pcu']:g} PCU, density {o['density']:g}"
              f" | zone PCU {zones}")
    print(f"results -> {out_dir}")


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    sub = ap.add_subparsers(dest="cmd", required=True)

    t = sub.add_parser("train", help="train yolo26n on the DriveIndia subset")
    t.add_argument("--data", default=ROOT / "configs" / "data.yaml",
                   help="dataset yaml (default configs/data.yaml)")
    t.add_argument("--model", default="yolo26n.pt",
                   help="base weights, looked up in weights/ first (default yolo26n.pt)")
    t.add_argument("--epochs", type=int, default=50)
    t.add_argument("--imgsz", type=int, default=640)
    t.add_argument("--batch", type=int, default=16, help="images per step; -1 = largest that fits the GPU")
    t.add_argument("--device", default="0", help="cuda device id / 'cpu' (default 0)")
    t.add_argument("--patience", type=int, default=15, help="early-stop patience (default 15)")
    t.add_argument("--cache", choices=["ram", "disk", "none"], default="ram",
                   help="keep decoded images in RAM (default, ~2-3 GB) / on disk / off")
    t.add_argument("--workers", type=int, default=8, help="dataloader worker processes (default 8)")
    t.set_defaults(func=cmd_train)

    p = sub.add_parser("predict", help="image(s) -> annotated image + PCU density JSON")
    p.add_argument("images", nargs="+", help="image files and/or folders")
    p.add_argument("--weights", default="yolo26n_best.pt",
                   help="trained weights, looked up in weights/ first (default yolo26n_best.pt)")
    p.add_argument("--conf", type=float, default=0.25, help="min detection confidence (default 0.25)")
    p.add_argument("--imgsz", type=int, default=640)
    p.add_argument("--device", default=None, help="cuda device id / 'cpu' (default: auto)")
    p.add_argument("--zones", type=int, default=None, help="number of zones (default configs/lanes.yaml)")
    p.add_argument("--horizon", type=float, default=None,
                   help="horizon height as a fraction of image height (default configs/lanes.yaml)")
    p.add_argument("--vanish-x", type=float, default=None,
                   help="vanishing point x as a fraction of image width (default configs/lanes.yaml)")
    p.add_argument("--out", default=ROOT / "outputs" / "predict", help="output folder (default outputs/predict)")
    p.set_defaults(func=cmd_predict)

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
