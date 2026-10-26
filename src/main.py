"""Adaptive Traffic Density Estimation - CLI entry.

Usage (tde conda env):
    python src/main.py train
    python src/main.py train --epochs 50 --batch 16 --device 0
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(Path(__file__).resolve().parent))


def _device(value: str) -> int | str:
    return int(value) if value.lstrip("-").isdigit() else value


def cmd_train(args) -> None:
    from models.detector import train

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

    args = ap.parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
