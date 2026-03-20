from PIL import Image
from numpy import *

path = 'Pictures/logo.png'
oleddim = array([128,64])

img = Image.open(path)
dims = array([img.width, img.height])
ratio = dims/oleddim
ar = dims[1] / dims[0]
ndims = (oleddim[0], int(ar*oleddim[0])) if ratio[0] > ratio[1] else (int(oleddim[1]/ar), oleddim[1])
img = img.resize(ndims, Image.Resampling.NEAREST).convert('L')

img.show()

output = open(path[:-3]+'csv', 'w')
pixels = img.load()
for x in range(ndims[0]):
    for y in range(ndims[1]):
        v = pixels[x,y]/255
        output.write(f'{x},{y},{v}\n')