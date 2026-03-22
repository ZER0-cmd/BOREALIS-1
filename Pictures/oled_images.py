from PIL import Image
from numpy import *

def process(path, oleddim):
    oleddim = array(oleddim)
    img = Image.open(path)
    dims = array([img.width, img.height])
    ratio = dims/oleddim
    ar = dims[1] / dims[0]
    ndims = (oleddim[0], int(ar*oleddim[0])) if ratio[0] > ratio[1] else (int(oleddim[1]/ar), oleddim[1])
    img = img.resize(ndims, Image.Resampling.HAMMING).convert('L')

    img.show()

    output = open(path[:-3]+'csv', 'w')
    pixels = img.load()
    for x in range(ndims[0]):
        for y in range(ndims[1]):
            v = 0 if pixels[x,y] > 125 else 1
            output.write(f'{x},{y},{v}\n')

for i in 'magnet', 'pressure', 'humidity', 'co2', 'acceleration':
    process(f'{i}.png', [128, 40])