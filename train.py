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

# while True:
#     operation = {}
#     keys = ['q', 'w', 'o', 'p']
#     random.shuffle(keys)

#     for key in keys[0:random.randint(1, 4)]: # 0:1/2/3/4, 前1个/2个/3个/4个键
#         operation.update({key: random.randint(2, 5) * 100})
#     if lose:
#         operation.update({'restart': True})
    
#     t0 = time.time()
#     res = operate(operation)
#     print(res['lose'], res['score'], time.time() - t0)
#     lose = res['lose']
#     data = bytearray(res['image']['data'])


# preprocess raw image to 80*80 gray image
def preprocess(observation, bgArr, tool, dimension=3):  
    img = Image.open(Buffer(observation))
    img = img.crop((30, 0, 210, 180))
    imgOcr = img.crop((40, 0, 140, 15))

    # 去除背景，灰度，调整至 80 x 80
    imgArr = np.array(img)
    isBg = np.all(imgArr == bgArr, axis=2)
    imgArr[isBg] = np.ones(4) * 255
    imgArr[:15, :] = np.ones((15, 180, 4)) * 255
    imgArr[:25, :10] = np.ones((25, 10, 4)) * 255
    img = Image.fromarray(imgArr)
    img = img.convert(mode='L')
    img = img.resize((80, 80), resample=Image.LANCZOS)
    # with open('screenshots/%d.png' % counter, 'wb') as f:
    #     counter += 1
    #     f.write(observation)
    # img.show()
    observation = np.array(img)

    # OCR
    scoreStr = tool.image_to_string(imgOcr)
    scoreStr = scoreStr.split(' ')[0].split('m')[0].replace('o', '0').replace('n', '0').replace('s', '6').replace('L', '1.').replace('l', '1')
    score = None
    try:
        score = float(scoreStr)
    except ValueError as e:
        print(e)

    if dimension == 3:
        observation = np.reshape(observation, (80, 80, 1))
    if dimension == 2:
        observation = np.reshape(observation, (80, 80))

    return (observation, score)

def play():
    keys = ['q', 'w', 'o', 'p']

    bg = Image.open("images\\bg.png")
    bgArr = np.array(bg)

    tool = pyocr.get_available_tools()[0]
    print("ocr tool =", tool)

    # Step 1: init BrainDQN
    actions = 16
    brain = BrainDQN(actions)

    # Step 2: init game
    res0 = operate({}) # do nothing, just get initial observation
    prevAction = np.zeros(16)
    prevAction[0] = 1
    prevTerminal0 = res0['lose']
    observation0 = bytearray(res0['image']['data'])
    (observation0, reward0) = preprocess(observation0, bgArr, tool, dimension=2)
    prevPrevTotalReward = reward0
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
                operation.update({keys[i]: 300})

        # act and observe
        res = operate(operation)

        # if lose, restart and observe again
        prevTerminal = res['lose']
        if prevTerminal:
            operation.clear()
            operation.update({'restart': True})
            res = operate(operation)
        
        observation = bytearray(res['image']['data'])
        (observation, prevTotalReward) = preprocess(observation, bgArr, tool)
    
        if prevTotalReward:
            prevReward = prevTotalReward - prevPrevTotalReward - 0.002
            prevPrevTotalReward = prevTotalReward
        else:
            prevReward = -0.002
        brain.setPerception(observation, prevAction, prevReward, prevTerminal)
        print(prevTerminal, prevTotalReward, time.time() - t0)

        perv_action = action
        
def main():
    play()

if __name__ == '__main__':
    main()