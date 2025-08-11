import os
from PIL import Image

def parse_yolo_dir(root: str):
    """Parse a YOLO dataset folder, extracting classes, images, labels.
    Supported layouts: either /images + /labels or mixed folders. Returns:
      {
        "classes": ["person", ...],
        "images": [
          {"local_path": "/tmp/.../img.jpg", "w": 640, "h": 480,
           "labels": [{"class_id": 0, "class_name": "person", "bbox_xywhn": [x,y,w,h]}]
          }, ...
        ]
      }
    """
    classes = []
    classes_path = None
    for dirpath, _, filenames in os.walk(root):
        if "classes.txt" in filenames:
            classes_path = os.path.join(dirpath, "classes.txt")
            break
    if classes_path and os.path.exists(classes_path):
        with open(classes_path, "r", encoding="utf-8") as f:
            classes = [ln.strip() for ln in f if ln.strip()]

    images = []
    exts = (".jpg", ".jpeg", ".png")
    for dirpath, _, filenames in os.walk(root):
        for fn in filenames:
            if fn.lower().endswith(exts):
                img_path = os.path.join(dirpath, fn)
                base = os.path.splitext(fn)[0]
                # label in same dir or under a sibling labels/ directory
                candidate_dirs = [dirpath, dirpath.replace("images", "labels")]
                label_path = None
                for d in candidate_dirs:
                    lp = os.path.join(d, base + ".txt")
                    if os.path.exists(lp):
                        label_path = lp
                        break
                labels = []
                if label_path:
                    with open(label_path, "r", encoding="utf-8") as lf:
                        for line in lf:
                            line = line.strip()
                            if not line:
                                continue
                            parts = line.split()
                            if len(parts) != 5:
                                continue
                            cid = int(float(parts[0]))
                            x, y, w, h = map(float, parts[1:])
                            cname = classes[cid] if cid < len(classes) else str(cid)
                            labels.append({
                                "class_id": cid,
                                "class_name": cname,
                                "bbox_xywhn": [x, y, w, h],
                            })
                try:
                    with Image.open(img_path) as im:
                        w_img, h_img = im.size
                except Exception:
                    w_img = h_img = None
                images.append({"local_path": img_path, "w": w_img, "h": h_img, "labels": labels})

    return {"classes": classes, "images": images}