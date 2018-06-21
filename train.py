# -------------------------
# Project: Deep Q-Learning on Flappy Bird
# Author: Flood Sung
# Date: 2016.3.21
# -------------------------

from PIL import Image
import requests
import json
import random
import time
from BrainDQN import BrainDQN
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




while True:
    operation = {}
    keys = ['q', 'w', 'o', 'p']
    random.shuffle(keys)

    for key in keys[0:random.randint(1, 4)]: # 0:1/2/3/4, 前1个/2个/3个/4个键
        operation.update({key: random.randint(2, 5) * 100})
    if lose:
        operation.update({'restart': True})
    
    t0 = time.time()
    res = operate(operation)
    print(res['lose'], res['score'], time.time() - t0)
    lose = res['lose']
    data = bytearray(res['image']['data'])


# preprocess raw image to 84*84 gray image
def preprocess(observation, bgArr, dimension=3):  
	img = Image.open(Buffer(observation))
    imgCrop = img.crop((110, 65, 445, 400))
    imgCropArr = np.array(imgCrop)

    isBg = np.all(imgCropArr == bgArr, axis=2)
    imgCropArr[isBg] = [0, 0, 0, 0]
    imgCropArr[318:, :] = np.zeros((17, 335, 4))
    imgCropArr[:10, :20] = np.zeros((10, 20, 4))
    imgClear = Image.fromarray(imgCropArr)

    imgClear = imgClear.convert(mode='L')
    imgClear = imgClear.resize((84, 84), resample=Image.LANCZOS)

    observation = np.array(imgClear)

    if dimension == 2:
        return observation
    elif dimension == 3:
	    return np.reshape(observation,(84, 84, 1))

def play():
    keys = ['q', 'w', 'o', 'p']
    bg = Image.open("screenshots\\bg.png")
    bgArr = np.array(bg)
    counter = 0

	# Step 1: init BrainDQN
	actions = 16
	brain = BrainDQN(actions)

	# Step 2: init game
    res0 = operate({}) # do nothing, just get initial observation
    prevAction = 0
    reward0 = res0['score']
    prevTerminal0 = res0['lose']
    observation0 = bytearray(res0['image']['data'])
    observation0 = preprocess(observation0, bgArr, dimension=2)
    brain.setInitState(observation0)

	# Step 3: run the game
	while True:
        t0 = time.time()
        
        # get action from brain
		action = brain.getAction()
        actionIdx = np.argmax(action)
        operation = {}
        for i in range(4):
            if actionIdx & (1 << i):
                operation.update({keys[i]: 500})

        # act and observe
        res = operate(operation)
        prevReward = res['score']
        prevTerminal = res['lose']
        observation = bytearray(res['image']['data'])
        observation = preprocess(observation, bgArr)
        with open('screenshots/%d.png' % counter, 'wb') as f:
            counter += 1
            f.write(observation)
    
		brain.setPerception(observation, prevAction, prevReward, prevTerminal)
        print(prevTerminal, prevReward, time.time() - t0)

        perv_action = action

def main():
	play()

if __name__ == '__main__':
	main()