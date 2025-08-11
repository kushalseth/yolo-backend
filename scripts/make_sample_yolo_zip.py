import os, sys, zipfile, tempfile, shutil
from PIL import Image, ImageDraw

"""
Generate a tiny YOLO dataset ZIP locally:
usage: python scripts/make_sample_yolo_zip.py out/sample_yolo.zip
"""

def main(out_zip):
    root = tempfile.mkdtemp()
    try:
        os.makedirs(os.path.join(root, 'images'), exist_ok=True)
        os.makedirs(os.path.join(root, 'labels'), exist_ok=True)
        with open(os.path.join(root, 'classes.txt'), 'w') as f:
            f.write('person car')
        for i in range(2):
            imgp = os.path.join(root, 'images', f'{i}.jpg')
            img = Image.new('RGB', (640, 480))
            d = ImageDraw.Draw(img)
            d.rectangle([200,150,300,300])
            img.save(imgp)
            with open(os.path.join(root, 'labels', f'{i}.txt'), 'w') as lf:
                lf.write('0 0.5 0.5 0.2 0.3')
        os.makedirs(os.path.dirname(out_zip), exist_ok=True)
        with zipfile.ZipFile(out_zip, 'w', zipfile.ZIP_DEFLATED) as z:
            for dirpath, _, filenames in os.walk(root):
                for fn in filenames:
                    lp = os.path.join(dirpath, fn)
                    rel = os.path.relpath(lp, root)
                    z.write(lp, rel)
        print(f'Wrote {out_zip}')
    finally:
        shutil.rmtree(root)

if __name__ == '__main__':
    out_zip = sys.argv[1] if len(sys.argv) > 1 else 'sample_yolo.zip'
    main(out_zip)