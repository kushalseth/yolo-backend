import os, tempfile, shutil
from app.yolo import parse_yolo_dir
from PIL import Image

def test_parse_yolo_dir_minimal():
    root = tempfile.mkdtemp()
    try:
        os.makedirs(os.path.join(root, 'images'), exist_ok=True)
        os.makedirs(os.path.join(root, 'labels'), exist_ok=True)
        with open(os.path.join(root, 'classes.txt'), 'w') as f:
            f.write('person car')
        imgp = os.path.join(root, 'images', 'a.jpg')
        Image.new('RGB', (64, 64)).save(imgp)
        with open(os.path.join(root, 'labels', 'a.txt'), 'w') as f:
            f.write('0 0.5 0.5 0.2 0.2')
        parsed = parse_yolo_dir(root)
        assert parsed['classes'] == ['person car']
        assert len(parsed['images']) == 1
        assert parsed['images'][0]['labels'][0]['class_id'] == 0
    finally:
        shutil.rmtree(root)