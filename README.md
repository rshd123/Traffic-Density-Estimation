<div align="center">

# 🚦 Adaptive Traffic Density Estimation

**PCU-weighted, lane-independent traffic density for Chennai roads**

![Python](https://img.shields.io/badge/Python-3.10-3776AB?logo=python&logoColor=white)
![PyTorch](https://img.shields.io/badge/PyTorch-2.14-EE4C2C?logo=pytorch&logoColor=white)
![CUDA](https://img.shields.io/badge/CUDA-13.0-76B900?logo=nvidia&logoColor=white)
![YOLO26](https://img.shields.io/badge/Ultralytics-YOLO26n-111F68?logo=ultralytics&logoColor=white)
![OpenCV](https://img.shields.io/badge/OpenCV-5.0-5C3EE8?logo=opencv&logoColor=white)
![NumPy](https://img.shields.io/badge/NumPy-2.2-013243?logo=numpy&logoColor=white)
![Conda](https://img.shields.io/badge/Conda-env-44A833?logo=anaconda&logoColor=white)
![Dataset](https://img.shields.io/badge/Dataset-DriveIndia-FF9933)

</div>

---

## 🎯 Objective

**Measure how loaded a road really is — and where — in mixed Indian traffic.**

Normal systems ask:

> *"How many vehicles are there?"*

This project asks:

> *"How much road space do they take up, and which part of the road is jammed?"*

On Chennai roads, cars, bikes, autos, buses and trucks all share the same space, often without clear lanes. Simple counting breaks down here in two ways:

| Problem | Why it fails | Our fix |
|---|---|---|
| **Every vehicle counts as 1** | A bus counts the same as a bike, but blocks far more road | **PCU weighting** |
| **Depends on lane markings** | Lanes are faded or ignored, so "cars per lane" doesn't work | **Virtual zones** |

---

## ⚖️ PCU — giving each vehicle a "size score"

**PCU (Passenger Car Unit)** compares every vehicle to one car. Think of a toll booth that charges by size: a bike pays half, a bus pays three times.

| Vehicle | PCU |
|---|:---:|
| 🚗 Car | 1.0 |
| 🏍️ Motorcycle | 0.5 |
| 🛺 Auto-rickshaw | 0.75 |
| 🚌 Bus | 3.0 |
| 🚚 Truck | 3.5 |

**Example:**

| Scene | Plain count | PCU |
|---|:---:|:---:|
| 10 bikes + 1 bus | 11 vehicles | 10 × 0.5 + 1 × 3.0 = **8 PCU** |
| 2 buses + 2 trucks | 4 vehicles *(looks quieter)* | 2 × 3.0 + 2 × 3.5 = **13 PCU** *(actually more crowded)* |

PCU catches what counting misses.

---

## 🛣️ Virtual zones — splitting the road without lanes

Instead of trusting painted lanes, the system **draws its own invisible strips** across the road. They are narrower at the top of the picture, because far-away road looks smaller:

```text
        \  Z1 | Z2 | Z3  /      ← far away (narrow)
         \    |    |    /
          \   |    |   /
           \  |    |  /         ← near the camera (wide)
```

1. YOLO finds each vehicle and draws a box around it.
2. The **centre point** of each box decides which strip it belongs to.
3. PCU scores are **added up per strip**.

**Example result:**

| Zone | Vehicles | PCU |
|---|---|:---:|
| Z1 (left) | 4 bikes | 2.0 |
| Z2 (middle) | 1 bus + 2 cars | **5.0** ← jammed here |
| Z3 (right) | 1 auto | 0.75 |
| **Whole road** | | **7.75** |

This gives both **how much** traffic there is (7.75 PCU) and **where** it is concentrated (the middle zone).

---

## 🔄 How it works

```text
Traffic image / video
        ↓
YOLO26n — detect & classify vehicles
        ↓
PCU weighting — size score per vehicle
        ↓
Virtual zones — place each vehicle in a strip
        ↓
Zone-wise PCU density  →  where the road is crowded
Overall PCU density    →  how crowded the road is
```
