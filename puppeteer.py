import requests
import json
import random
import time
from PIL import Image

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

    with open('screenshots/%d.png' % counter, 'wb') as f:
        counter += 1
        f.write(data)
    
    # Image.open(Buffer(data)).show()
