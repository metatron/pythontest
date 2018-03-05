# https://qiita.com/ohtaman/items/edcb3b0a2ff9d48a7def

import logging
import math
import gym
from gym import spaces
from gym.utils import seeding
import numpy as np
import tensorflow as tf
import stockstats as stss
import pandas as pd
from sklearn.preprocessing import MinMaxScaler

logger = logging.getLogger(__name__)

from ico.bitflyer_trade import BitFlyerController
from ico.bit_buysell_logic import BitSignalFinder

ACTION_BUY = 0
ACTION_STAY = 1
ACTION_SELL = 2

class MyEnv(gym.Env):
    metadata = {
        'render.modes': ['human', 'rgb_array'],
        'video.frames_per_second' : 50
    }

    def __init__(self):
        RAND_SEED = 778  # 日産 2018/01/15更新

        np.random.seed(RAND_SEED)
        tf.set_random_seed(RAND_SEED)

        # 保存されたCSVを読み込んでstockstatsフォーマットにする
        self._bitTrade = BitFlyerController()

        #でーたファイル読み込み
        path = "stockTick_20180216_7201.csv"
        df = pd.read_csv(path)
        self._tickDataList = df.values.tolist()

        self.totalStep = len(self._tickDataList)

        self.index = 0

        self.state = None

        self._alldata = []

        self._seed()
        self.viewer = None

        # 売買で生じる値動き
        self.min_values = 2000.0
        self.max_values = 0.0

        #0: 買う、1:ステイ、2:売る
        self.action_space = spaces.Discrete(3)
        #actionに伴う所持金の変化
        self.observation_space= spaces.Box(
            low=np.zeros(5),
            high=np.array([2000.0,2000.0,2000.0,2000.0,1.0]),
            shape=np.array(['open', 'high', 'low', 'close', 'macd']).shape
        )

        self.actHistory = []

        self.reward = 0

        #買いの回数
        self._boughtNum = 0

        self._bitflyer = BitFlyerController()
        # bitflyer.initGraph()

        self._bitsignal = BitSignalFinder(self._bitflyer._tickList, self._bitflyer._candleStats)

        tickFilePath = "./csv/tick_201803051658_BTC_JPY.csv"
        df = pd.read_csv(tickFilePath)
        self._tickDataList = df.values.tolist()

        self.totalStep = len(self._tickDataList)

    def _reset(self):
        self.state = self.np_random.uniform(low=-0.05, high=0.05, size=(4,))
        self.index = 0
        self.reward = 0
        self._boughtNum = 0
        return np.array(self.state)


    def _seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        return [seed]


    def _step(self, action):
        assert self.action_space.contains(action), "%r (%s) invalid" % (action, type(action))

        tmpTick = self._tickDataList[self.index]
        self._bitflyer._tickList.append(tmpTick)
        self._bitflyer._convertTickDataToCandle(self._bitflyer._tickList)
        stockstatsClass = self._bitflyer.convertToStockStats()
        self._bitsignal.update(self._bitflyer._tickList, stockstatsClass)

        #買う事ができる場合リワードは少なくする
        if(self._boughtNum == 0):
            self._boughtNum += 1
            self.reward += 1

        #売る場合





        self.index += 1
        done = self.index >= self.totalStep

        return np.array(self.state), self.reward, done, {}


    def _render(self, mode='human', close=False):
        # no rendering for stock prediction

        pass



