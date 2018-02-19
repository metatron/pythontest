# https://towardsdatascience.com/reinforcement-learning-w-keras-openai-dqns-1eed3a5338c

import gym
import numpy as np
import random
from keras.models import Sequential
from keras.layers import Dense, Dropout, Flatten
from keras.optimizers import Adam

from collections import deque

#__init__.pyを呼ぶのに必要
import reinforcement.envstock.myEnv as myEnv


class DQN:
    def __init__(self, env, state_size, action_size):
        self.env = env
        self.state_size = state_size
        self.action_size = action_size

        self.memory = deque(maxlen=2000)

        self.gamma = 0.85
        self.epsilon = 1.0
        self.epsilon_min = 0.01
        self.epsilon_decay = 0.995
        self.learning_rate = 0.005
        self.tau = .125

        self.model = self.create_model()
        self.target_model = self.create_model()

    def create_model(self):
        model = Sequential()
        model.add(Dense(24, input_shape=self.state_size, activation="relu"))
        model.add(Dense(48, activation="relu"))
        model.add(Dense(24, activation="relu"))
        model.add(Dense(self.action_size, activation='linear'))
        model.compile(loss="mean_squared_error",
                      optimizer=Adam(lr=self.learning_rate))
        # model.summary()
        return model

    def act(self, state):
        self.epsilon *= self.epsilon_decay
        self.epsilon = max(self.epsilon_min, self.epsilon)
        if np.random.random() < self.epsilon:
            return random.randrange(self.action_size)
        return np.argmax(self.model.predict(state)[0])

    def remember(self, state, action, reward, new_state, done):
        self.memory.append([state, action, reward, new_state, done])

    def replay(self):
        batch_size = 32
        if len(self.memory) < batch_size:
            return

        samples = random.sample(self.memory, batch_size)
        for sample in samples:
            state, action, reward, new_state, done = sample
            target = self.target_model.predict(state)
            if done:
                target[0][action] = reward
            else:
                Q_future = max(self.target_model.predict(new_state)[0])
                target[0][action] = reward + Q_future * self.gamma
            self.model.fit(state, target, epochs=1, verbose=0)

    def target_train(self):
        weights = self.model.get_weights()
        target_weights = self.target_model.get_weights()
        for i in range(len(target_weights)):
            target_weights[i] = weights[i] * self.tau + target_weights[i] * (1 - self.tau)
        self.target_model.set_weights(target_weights)

    def save_model(self, fn):
        self.model.save_weights(fn)

    def load_model(self, fn):
        self.model.load_weights(fn)

    def predictStage(self, state):
        print(self.model.predict(state))
        actionList = self.model.predict(state)[0]
        index = 0
        if(actionList[1] > actionList[0]):
            index = 1
        return index



def main():
    env = gym.make("trading-v0")
    gamma = 0.9
    epsilon = .95

    EPISODES = 3
    trial_len = 500

    # updateTargetNetwork = 1000
    state_size = env.observation_space.shape
    action_size = env.action_space.n
    dqn_agent = DQN(env=env, state_size=state_size, action_size=action_size)
    # dqn_agent.load_model("success_2.h5")
    steps = []
    for trial in range(EPISODES):
        cur_state = env.reset()
        cur_state = np.reshape(cur_state, [1, state_size[0]])
        for step in range(trial_len):

            action = dqn_agent.act(cur_state)
            new_state, reward, done, _ = env.step(action)
            print(new_state, reward)
            # reward = reward if not done else -20
            new_state = np.reshape(new_state, [1, state_size[0]])
            dqn_agent.remember(cur_state, action, reward, new_state, done)

            dqn_agent.replay()  # internally iterates default (prediction) model
            dqn_agent.target_train()  # iterates target model

            cur_state = new_state

            if step%100 == 0:
                print("completed trial:{}, step:{}".format(trial, step));

            if done:
                break
        print("Completed in {} trials".format(trial))
        dqn_agent.save_model("success_"+str(trial)+".h5")


def prediction():
    env = gym.make("trading-v0")
    state_size = env.observation_space.shape
    action_size = env.action_space.n
    dqn_agent = DQN(env=env, state_size=state_size, action_size=action_size)
    dqn_agent.load_model("success_2.h5")

    cast(myEnv.MyEnv, env)
    for i in range(5):
        state = env.env.getState(i)
        state = np.reshape(state, [1, 4])
        predict = dqn_agent.predictStage(state)
        print("prediction:{}".format(predict))
        print()

def cast(ParentalClass, child_object):
    child_object.__class__ = ParentalClass

if __name__ == "__main__":
    # main()
    prediction()