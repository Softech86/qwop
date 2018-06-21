import requests
import json
import random
import time
from PIL import Image
import numpy as np 

config = {}
with open('config.json', 'r') as f:
    config = json.load(f)

def operate(operation):
    r = requests.get("http://localhost:%d" % config['port'], params=operation)
    return r.json()

class Buffer:
    def __init__(self, data):
        self.data = data
    def read(self):
        return self.data

lose = False

counter = 0

bg = Image.open("screenshots\\bg.png")
bgArr = np.array(bg)

while True:
    operation = {}
    keys = ['q', 'w', 'o', 'p']
    random.shuffle(keys)
    for key in keys[0:random.randint(1, 4)]:
        operation.update({key: random.randint(2, 5) * 100})
    if lose:
        operation.update({'restart': True})
    
    t0 = time.time()
    res = operate(operation)
    print(res['lose'], res['score'], time.time() - t0)
    lose = res['lose']
    data = bytearray(res['image']['data'])
    img = Image.open(Buffer(data))
    imgCrop = img.crop((110, 65, 445, 400))
    imgCropArr = np.array(imgCrop)

    isBg = np.all(imgCropArr == bgArr, axis=2)
    imgCropArr[isBg] = [0, 0, 0, 0]
    imgCropArr[318:, :] = np.zeros((17, 335, 4))
    imgCropArr[:10, :20] = np.zeros((10, 20, 4))
    imgClear = Image.fromarray(imgCropArr)
    imgClear = imgClear.convert(mode='L')
    imgClear = imgClear.resize((84, 84), resample=Image.LANCZOS)

    with open('screenshots/%d.png' % counter, 'wb') as f:
        counter += 1
        # f.write(data)
        imgClear.save(f)
    
    # Image.open(Buffer(data)).show()
