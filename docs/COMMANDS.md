# Commands

Run from the project folder after `conda activate tde`.

## Setup

```powershell
python -m pip install torch torchvision --index-url https://download.pytorch.org/whl/cu130   # install GPU torch (do this first)
python -m pip install -r requirements.txt                                                    # install the other packages
python -m pip install --force-reinstall --no-deps torch torchvision --index-url https://download.pytorch.org/whl/cu130   # fix torch if it became the CPU version
python -c "import torch; print(torch.cuda.is_available(), torch.cuda.get_device_name(0))"   # check the GPU is visible
```

## Data

```powershell
python src/data/preprocessor.py stats                  # count images/objects per class
python src/data/preprocessor.py verify                 # draw boxes on sample images -> data/verify/index.html
python src/data/preprocessor.py build                  # build the 3000/400/700 subset (video-level split, 640 px)
python src/data/preprocessor.py config                 # write configs/data.yaml (run after build)
python src/data/preprocessor.py build --imgsz 0        # build with full-resolution images
python src/data/preprocessor.py build --group route    # build with a stricter split (whole routes)
```

## Training

```powershell
python src/main.py train                    # train YOLO26n -> weights/yolo26n_best.pt
python src/main.py train --epochs 1         # quick 1-epoch test
python src/main.py train --batch -1         # train with auto batch size (usually faster)
```

## Density (image -> PCU density)

```powershell
python src/main.py predict photo.jpg                       # annotated image + density JSON -> outputs/predict/
python src/main.py predict data/subset/test/images         # every image in a folder
python src/main.py predict photo.jpg --zones 3             # 3 zones instead of 5
python src/main.py predict photo.jpg --horizon 0.5         # horizon at half height (photos from another camera)
python src/main.py predict photo.jpg --conf 0.4            # only keep detections the model is >= 40% sure of
```

## Class-check helpers

```powershell
python scripts/pcu_atlas.py      # photo sheet of the 5 PCU classes -> data/verify/pcul_*.jpg
python scripts/class_atlas.py    # photo sheet of every class -> data/verify/atlas_*.jpg
python scripts/ambig_atlas.py    # photo sheet of unclear classes -> data/verify/ambig_*.jpg
```
