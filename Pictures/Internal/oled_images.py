import glob
from PIL import Image
from numpy import *

OUTPUT = 'Pico-code/pictures/'

def process(path: str, oleddim, invert=False):
    oleddim = array(oleddim)
    img = Image.open(path)
    dims = array([img.width, img.height])
    ratio = dims/oleddim
    ar = dims[1] / dims[0]
    ndims = (oleddim[0], int(ar*oleddim[0])) if ratio[0] > ratio[1] else (int(oleddim[1]/ar), oleddim[1])
    img = img.resize(ndims, Image.Resampling.HAMMING).convert('L')

    # img.show()
    ver = 0
    print(OUTPUT + path.split('/')[-1][:-3].replace(" ", "") + 'py')
    output = open(OUTPUT + path.split("/")[-1][:-3].replace(" ", "") + 'py', 'w')
    output.write(f'DIM = ({ndims[0]},{ndims[1]})\nPIXELS = bytes(')
    pixels = img.load()
    for x in range(ndims[0]):
        for y in range(ndims[1]):
            v = (0 if pixels[x,y] > 125 else 1) if invert else (1 if pixels[x,y] > 125 else 0)
            if v == 0:
                continue
            output.write(f'{x},{y},')
            ver += 1
    output.write(')')
    print(f"Converted {path} ({ver} pixels)")

for path in glob.glob(f"Pictures/Internal/*.png"):
    process(path, [128, 40])