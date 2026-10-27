"""Web API - upload a road photo, get the PCU density back.

Run (tde conda env):
    python src/main.py serve

Routes are documented in docs/ENDPOINTS.md. The model is loaded once at
startup. When frontend/dist exists (npm run build), the React app is served
at / as well, so one command runs everything.
"""

from __future__ import annotations

import base64
import threading
from contextlib import asynccontextmanager
from pathlib import Path

import cv2
import numpy as np
from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from starlette.concurrency import run_in_threadpool

from density import pcu
from density.lane_calculation import ZoneLayout, load_config
from detection.detector import load
from evaluation.compare import compare, find_labels, ground_truth
from evaluation.visualize import draw
from pipeline import analyze

ROOT = Path(__file__).resolve().parents[2]
FRONTEND_DIST = ROOT / "frontend" / "dist"
WEIGHTS = "yolo26n_best.pt"
DEFAULT_CONF = 0.25
MAX_UPLOAD = 20 * 1024 * 1024  # 20 MB

state: dict = {}
model_lock = threading.Lock()  # one prediction at a time on the shared model


@asynccontextmanager
async def lifespan(_app: FastAPI):
    state["model"] = load(WEIGHTS)
    yield
    state.clear()


app = FastAPI(title="Traffic Density Estimation API", lifespan=lifespan)
app.add_middleware(  # React dev server (npm run dev)
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def _data_url(image: np.ndarray) -> str:
    _, buf = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 90])
    return "data:image/jpeg;base64," + base64.b64encode(buf).decode()


def _check(name: str, value: float | None, low: float, high: float) -> None:
    if value is not None and not low <= value <= high:
        raise HTTPException(422, f"{name} must be between {low} and {high}")


@app.get("/api/health")
def health() -> dict:
    return {"status": "ok", "model_loaded": "model" in state, "weights": WEIGHTS}


@app.get("/api/config")
def config() -> dict:
    lanes = load_config()
    return {
        "conf": DEFAULT_CONF,
        "lanes": {
            "num_zones": lanes.get("num_zones", ZoneLayout.num_zones),
            "horizon_y": lanes.get("horizon_y", ZoneLayout.horizon_y),
            "vanishing_x": lanes.get("vanishing_x", ZoneLayout.vanishing_x),
        },
        "pcu": [{"class_id": c, "label": pcu.label(c), "pcu": pcu.weight(c)}
                for c in pcu.class_ids()],
    }


@app.post("/api/analyze")
async def analyze_image(
    file: UploadFile = File(...),
    labels: UploadFile | None = File(None),
    conf: float = Form(DEFAULT_CONF),
    num_zones: int | None = Form(None),
    horizon_y: float | None = Form(None),
    vanishing_x: float | None = Form(None),
) -> dict:
    _check("conf", conf, 0.01, 1.0)
    _check("num_zones", num_zones, 1, 15)
    _check("horizon_y", horizon_y, 0.0, 0.95)
    _check("vanishing_x", vanishing_x, 0.0, 1.0)

    data = await file.read()
    if len(data) > MAX_UPLOAD:
        raise HTTPException(413, "image is larger than 20 MB")
    image = cv2.imdecode(np.frombuffer(data, np.uint8), cv2.IMREAD_COLOR)
    if image is None:
        raise HTTPException(400, "file is not a readable image (use jpg / png / webp / bmp)")

    lanes = {"num_zones": num_zones, "horizon_y": horizon_y, "vanishing_x": vanishing_x}

    def run():
        with model_lock:
            return analyze(state["model"], image, conf=conf, **lanes)

    result, annotated = await run_in_threadpool(run)
    result["image"] = file.filename
    response = {"result": result, "image": _data_url(annotated), "comparison": None}

    # ground truth: an uploaded label file wins, else look the photo up in data/subset
    truth, source, split = None, None, None
    if labels is not None and labels.filename:
        truth, source = (await labels.read()).decode("utf-8", errors="replace"), "uploaded"
    elif found := find_labels(file.filename or ""):
        split, path = found
        truth, source = path.read_text(encoding="utf-8"), "dataset"

    if truth is not None:
        h, w = image.shape[:2]
        layout = ZoneLayout.from_config(w, h, **lanes)
        actual = ground_truth(truth, layout)
        response["comparison"] = {
            "source": source,
            "split": split,
            **compare(result, actual),
            "actual": actual,
            "actual_image": _data_url(draw(image, actual, layout)),
        }
    return response


if FRONTEND_DIST.is_dir():  # built React app (after the API routes, so /api/* wins)
    app.mount("/", StaticFiles(directory=FRONTEND_DIST, html=True), name="frontend")
