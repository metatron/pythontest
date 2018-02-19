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

import scraping.kabucom
import scraping.SignalFinder

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
        self._kabucom = scraping.kabucom.KabuComMainController()

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
        self.observation_space= spaces.Box(low=np.zeros(5), high=np.array([2000.0,2000.0,2000.0,2000.0,1.0]), shape=np.array(['open', 'high', 'low', 'close', 'macd']).shape)

        self.actHistory = []

        self.reward = 0


    def _reset(self):
        self.state = self.np_random.uniform(low=-0.05, high=0.05, size=(4,))
        self.index = 0
        self.reward = 0
        return np.array(self.state)


    def _seed(self, seed=None):
        self.np_random, seed = seeding.np_random(seed)
        return [seed]


    def _step(self, action):
        assert self.action_space.contains(action), "%r (%s) invalid" % (action, type(action))

        crntTick = self._tickDataList[self.index]
        tmpTick = crntTick[1:]
        tmpTick[0] = int(tmpTick[0])
        #上記で実際のtickデータと同じにコンバート
        #下記でコントローラにストックしている状態にする
        self._kabucom._stockTicks.append(tmpTick)
        self._kabucom._statusUpdate()
        stockstatClass = self._kabucom.convertToStockStats(['macd'])
        self._alldata = stockstatClass.as_matrix(columns=['open', 'high', 'low', 'close', 'volume', 'macd'])

        self.state = self._alldata[-1]

        #株価が上がった
        if(todayObs[0] - yesterDayObj[3] > 0):
            #予測が[上がった]の場合rewardを与える
            if(action == 1):
                self.reward += 1.0
            #[下がった]の場合はrewardなし
            else:
                self.reward -= 1.0
        #株価が下がった
        else:
            #予測が[上がった]の場合rewardなし
            if(action == 1):
                self.reward -= 1.0
            #[下がった]の場合はrewardあり
            else:
                self.reward += 1.0

        self.index += 1
        done = self.index >= self.totalStep

        return np.array(self.state), self.reward, done, {}


    def _render(self, mode='human', close=False):
        # no rendering for stock prediction

        pass


    def getState(self, index=0):
        print(self.allData[index])
        return self.allDataNormalized[index]

