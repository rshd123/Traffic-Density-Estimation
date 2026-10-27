# TODO

Remaining work for the project, based on **docs/CONTEXT.md** (the research goal) and **docs/IMPLEMENTATION.md** (the plan). Tasks are written as outcomes, not file names — the code layout can change freely.

---

## Done so far (quick status)

- Data subset built: 3,000 train / 400 val / 700 test images, config generated (`nc: 28`)
- Split is **video-level**: each drive sits in exactly one split, exact duplicate images removed (no train/test leakage)
- Environment ready: conda env `tde`, torch with CUDA 13.0, ultralytics, GPU verified (RTX 5060)
- PCU weights defined (car 1.0 · motorcycle 0.5 · auto-rickshaw 0.75 · bus 3.0 · truck 3.5) with ID-based lookup
- Training entry point written (CLI ready to run)
- Pretrained base weights downloaded

---

## 1. Train the detector  (done)

- [x] Run training: `python src/main.py train` (yolo26n, batch 16, imgsz 640, GPU) — early-stopped at epoch 45, best epoch 30, ~20 min
- [x] Check quality: test mAP50 — car 0.94 · motorcycle 0.94 · auto-rickshaw 0.77 · bus 0.73 · truck 0.56 (weakest)
- [x] Confirm the best checkpoint is saved for later use → `weights/yolo26n_best.pt`

## 2. PCU-weighted density  (core of the project)

- [x] **Virtual spatial zones** — `src/density/lane_calculation.py`: equal-angle strips fanning out from the vanishing point (3/5/7, configurable), thin far away and wide near the camera; each vehicle goes into a zone by its ground point (bottom-centre of the box)
- [x] **Density estimation** — `src/density/estimator.py`: zone density = PCU in zone ÷ zone area; overall density = all PCU ÷ road area; plain-count density reported alongside. Run: `python src/main.py predict <image>`
- [ ] Density: smooth over time for video
- [ ] Density: convert areas to real road size (m²) with perspective calibration
- [ ] **Occlusion correction** — make up for vehicles hidden behind each other in crowded zones (under-counting)

## 3. Evaluation  (prove it actually works)

- [x] Detection accuracy (mAP) on the test split — all-class mAP50 0.587 (see section 1 for the PCU classes)
- [ ] Density error compared to ground truth
- [ ] **Baseline 1:** plain vehicle counting vs PCU-weighted density — this is the project's main comparison (from CONTEXT.md)
- [ ] **Baseline 2:** fixed lane-based zones vs virtual spatial zones
- [ ] Zone assignment accuracy

## 4. Visualization & demo

- [x] Show detections with their PCU values
- [x] Zone-wise density heatmap drawn over the road image (red tint, stronger = denser)
- [ ] Comparison plots: PCU density vs raw count
- [x] Image inference that outputs an annotated result + density numbers (`predict`)
- [ ] Video inference
- [ ] Simple demo app: upload an image/video → get the density result

## 5. Research validation  (the risk flagged in CONTEXT.md)

- [ ] Justify the PCU weights properly (IRC-based values + references) — CONTEXT.md calls unvalidated/arbitrary PCU weights the main risk to publication
- [ ] Later: final names for all 28 class IDs (cosmetic only — never requires retraining)
- [ ] Later: real-world evaluation on Chennai traffic footage (external validation)

---

**Suggested order:** 1 → 2 → 3 → 4, with 5 running alongside. Item 1 can start immediately.
