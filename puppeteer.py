import requests
import json
import random
import time
from PIL import Image
import numpy as np 
from pyocr import pyocr

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

tool = pyocr.get_available_tools()[0]
print("ocr tool =", tool)

lose = False

counter = 0

bg = Image.open("images\\bg.png")
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
    lose = res['lose']
    data = bytearray(res['image']['data'])
    img = Image.open(Buffer(data))
    img = img.crop((30, 0, 210, 180)) # 180 * 180
    imgOcr = img.crop((40, 0, 140, 15))

    # 去除背景，灰度，调整至 84 x 84
    imgArr = np.array(img)
    isBg = np.all(imgArr == bgArr, axis=2)
    imgArr[isBg] = np.ones(4) * 255
    imgArr[:15, :] = np.ones((15, 180, 4)) * 255
    imgArr[:25, :10] = np.ones((25, 10, 4)) * 255
    img = Image.fromarray(imgArr)
    img = img.convert(mode='L')
    img = img.resize((84, 84), resample=Image.LANCZOS)

    # ocr
    scoreStr = tool.image_to_string(imgOcr)
    scoreStr = scoreStr.split(' ')[0].split('m')[0].replace('o', '0').replace('n', '0').replace('s', '6').replace('L', '1.').replace('l', '1')
    score = None
    try:
        score = float(scoreStr)
    except ValueError as e:
        print(e)

    with open('screenshots/%d.png' % counter, 'wb') as f:
        counter += 1
        img.save(f)
    with open('screenshots/%d_ocr.png' % counter, 'wb') as f:
        imgOcr.save(f)

    print(counter, res['lose'], score, time.time() - t0)
    
