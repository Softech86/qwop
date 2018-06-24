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
import argparse

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

# preprocess raw image to 80*80 gray image
def preprocess(observation, bgArr, dimension=3):  
    img = Image.open(Buffer(observation))

    # 去除背景，灰度，调整至 80 x 80
    imgArr = np.array(img)
    isBg = np.all(imgArr == bgArr, axis=2)
    imgArr[isBg] = np.ones(4) * 255
    imgArr[:30, 80:280] = np.ones((30, 200, 4)) * 255
    imgArr[:50, :5] = np.ones((50, 5, 4)) * 255
    img = Image.fromarray(imgArr)
    img = img.convert(mode='L')
    img = img.resize((80, 80), resample=Image.LANCZOS)

    observation = np.array(img)

    if dimension == 3:
        observation = np.reshape(observation, (80, 80, 1))
    if dimension == 2:
        observation = np.reshape(observation, (80, 80))

    return observation

def play(debug=False):
    keys = ['q', 'w', 'o', 'p']
    counter = 0

    bg = Image.open("images\\bg.png")
    bgArr = np.array(bg)

    # Step 1: init BrainDQN
    actions = 16
    brain = BrainDQN(actions)

    # Step 2: init game
    res = operate({}) # do nothing, just get initial observation
    terminal = res['lose']
    observation = bytearray(res['image']['data'])
    observation = preprocess(observation, bgArr, dimension=2)
    totalReward = res['score']
    prevReward = totalReward
    brain.setInitState(observation)
    if debug:
        with open('screenshots/%d.png' % counter, 'wb') as f:
            counter += 1
            Image.fromarray(observation).save(f)
        print(counter, terminal, totalReward)

	# Step 3: run the game
    while True:
        t0 = time.time()
        
        # get action from brain
        action = brain.getAction()
        actionIdx = np.argmax(action)
        operation = {}
        for i in range(4):
            if actionIdx & (1 << i):
                operation.update({keys[i]: 30})

        # act and observe
        res = operate(operation)

        # if lose, punish, restart and observe again
        terminal = res['lose']
        if terminal:
            nextObservation = bytearray(res['image']['data'])
            nextObservation = preprocess(nextObservation, bgArr)
            brain.setPerception(nextObservation, action, -10, terminal)
            res = operate({'restart': True})
            prevReward = 0
            action = np.zeros(16)
            action[0] = 1
        
        # train the net with action, reward and nextObs
        terminal = res['lose']
        nextObservation = bytearray(res['image']['data'])
        nextObservation = preprocess(nextObservation, bgArr)
        totalReward = res['score']
        stepReward = totalReward - prevReward - 0.001
        brain.setPerception(nextObservation, action, stepReward, terminal)
        
        prevReward = totalReward

        if debug:
            with open('screenshots/%d.png' % counter, 'wb') as f:
                counter += 1
                Image.fromarray(nextObservation.reshape(80, 80)).save(f)
            print(counter, terminal, totalReward, time.time() - t0, operation)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument("-d", "--debug", action="store_true", default=False)
    args = parser.parse_args()
    play(debug=args.debug)