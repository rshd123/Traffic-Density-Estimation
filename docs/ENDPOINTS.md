# API Endpoints

The backend is a small **FastAPI** server (`src/api/server.py`). The React app (`frontend/`) talks to it; you can also call it directly with `curl` or Postman.

**Start it** (from the project folder, `conda activate tde`):

```powershell
python src/main.py serve              # http://127.0.0.1:8000
python src/main.py serve --reload     # restarts automatically when code changes
```

- Base URL: `http://127.0.0.1:8000`
- Interactive docs (try every route in the browser): `http://127.0.0.1:8000/docs`
- The model (`weights/yolo26n_best.pt`) is loaded **once** when the server starts.

| Method | Route | What it does |
|---|---|---|
| GET | `/api/health` | Is the server up and the model loaded? |
| GET | `/api/config` | Default settings + PCU weights (the frontend reads these on load) |
| POST | `/api/analyze` | **Main route:** upload a photo → PCU density (+ actual vs predicted when correct answers exist) |
| GET | `/` | The built React app (only after `npm run build` in `frontend/`) |

---

## GET `/api/health`

Quick check that the server is running.

```json
{ "status": "ok", "model_loaded": true, "weights": "yolo26n_best.pt" }
```

---

## GET `/api/config`

Default settings from `configs/lanes.yaml` and the PCU weights from `configs/pcu_weights.yaml`.

```json
{
  "conf": 0.25,
  "lanes": { "num_zones": 5, "horizon_y": 0.42, "vanishing_x": 0.5 },
  "pcu": [
    { "class_id": 2, "label": "car", "pcu": 1.0 },
    { "class_id": 3, "label": "motorcycle", "pcu": 0.5 },
    { "class_id": 5, "label": "bus", "pcu": 3.0 },
    { "class_id": 7, "label": "truck", "pcu": 3.5 },
    { "class_id": 10, "label": "auto-rickshaw", "pcu": 0.75 }
  ]
}
```

---

## POST `/api/analyze`

Upload one road photo, get the density result back. Sent as **form data** (`multipart/form-data`), like a normal file upload.

### Request fields

| Field | Type | Required | Default | Meaning |
|---|---|---|---|---|
| `file` | image file | **yes** | – | Road photo (jpg / png / webp / bmp, max 20 MB) |
| `labels` | .txt file | no | – | Correct answers in YOLO format (`class cx cy w h` per line, values 0–1). Enables actual vs predicted |
| `conf` | number | no | `0.25` | Minimum model confidence, 0.01–1 |
| `num_zones` | integer | no | `5` | Number of virtual lanes, 1–15 |
| `horizon_y` | number | no | `0.42` | Horizon height as a fraction of image height (0 = top), 0–0.95 |
| `vanishing_x` | number | no | `0.5` | Where the road disappears, as a fraction of image width, 0–1 |

**Correct answers are found automatically** when the photo's file name matches an image in `data/subset/{test,val,train}` (e.g. `F_3_4_4531.jpg`). An uploaded `labels` file takes priority.

### Example

```powershell
curl -F "file=@data/subset/test/images/R_11_4_257.jpg" -F num_zones=5 http://127.0.0.1:8000/api/analyze
```

### Response

```jsonc
{
  "result": {
    "image": "R_11_4_257.jpg",
    "width": 640, "height": 432,
    "overall": {
      "vehicles": 10,          // vehicles on the road (5 PCU classes only)
      "pcu": 9.25,             // total PCU
      "area": 0.5833,          // road area as a share of the photo
      "density": 15.857,       // PCU ÷ road area
      "count_density": 17.143, // plain vehicle count ÷ road area (baseline)
      "busiest_zone": 1        // lane index (0 = far left), null if empty
    },
    "by_class": [ { "class_id": 2, "label": "car", "count": 3, "pcu": 3.0 } /* ...one per PCU class */ ],
    "zones": [
      { "zone": 0, "vehicles": 1, "pcu": 1.0, "area": 0.1363, "density": 7.337, "count_density": 7.337 }
      /* ...one per lane, left to right */
    ],
    "vehicles": [
      { "class_id": 2, "label": "car", "conf": 0.91, "box": [x1, y1, x2, y2], "pcu": 1.0, "zone": 0 }
      /* zone null = above the horizon, left out of density */
    ],
    "zones_layout": { "num_zones": 5, "horizon_y": 0.42, "vanishing_x": 0.5,
                      "vanishing_point": [320.0, 181.4], "boundaries": [[[x, y], [x, y]] /* ... */] },
    "off_road": 0,             // PCU vehicles above the horizon
    "ignored_detections": 3    // non-PCU detections (pedestrians, signs, ...)
  },

  "image": "data:image/jpeg;base64,...",   // annotated photo: lanes, boxes, PCU labels, red density tint

  "comparison": null   // or the object below when correct answers exist
}
```

### `comparison` (actual vs predicted)

The correct answers go through the **same** PCU + lane calculation as the model, so every number can be compared directly.

```jsonc
{
  "source": "dataset",          // "dataset" (found automatically) or "uploaded"
  "split": "test",              // test / val / train, null when uploaded
                                // "train" = the model studied this photo, not a fair test
  "overall": {
    "vehicles": { "predicted": 10, "actual": 9, "difference": 1 },
    "pcu":      { "predicted": 9.25, "actual": 8.75, "difference": 0.5 },
    "density":  { "predicted": 15.857, "actual": 15.0, "difference": 0.857 },
    "pcu_error_pct": 5.7,       // |predicted - actual| ÷ actual × 100, null if actual is 0
    "lane_pcu_mae": 0.1         // average PCU error per lane
  },
  "by_class": [ { "class_id": 2, "label": "car",
                  "count": { "predicted": 3, "actual": 3, "difference": 0 },
                  "pcu":   { "predicted": 3.0, "actual": 3.0, "difference": 0.0 } } ],
  "lanes":    [ { "zone": 0, "vehicles": {...}, "pcu": {...}, "density": {...} } ],
  "matching": {                 // boxes paired one to one when they overlap >= 50% (IoU)
    "correct": 9,               // found, right type
    "wrong_type": 0,            // found, wrong type
    "missed": 0,                // real vehicle not found
    "extra": 1,                 // model box with no real vehicle (false alarm)
    "wrong_type_details": [ { "actual": "truck", "predicted": "bus" } ]
  },
  "actual": { /* full result built from the correct answers, same shape as "result" */ },
  "actual_image": "data:image/jpeg;base64,..."   // photo drawn with the correct boxes
}
```

### Errors

| Status | When |
|---|---|
| 400 | `file` is not a readable image |
| 413 | Image larger than 20 MB |
| 422 | A setting is out of range (e.g. `num_zones=99`) or `file` is missing |

Error body: `{ "detail": "num_zones must be between 1 and 15" }`
