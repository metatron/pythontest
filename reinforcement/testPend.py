# https://qiita.com/namakemono/items/9b75d1c0c98916b396ba
# https://keon.io/deep-q-learning/
# http://punkbite.blogspot.jp/2016/10/create-simple-ai-playing-game-with.html
# https://qiita.com/trtd56/items/3a09d37788d8d13ff131#パラメータ設定
# http://www.kumilog.net/entry/openai-gym-rl

# import gym
# env = gym.make('Pendulum-v0')
# for i_episode in range(20):
#     observation = env.reset()
#     for t in range(100):
#         env.render()
#         print(observation)
#         action = env.action_space.sample()
#         observation, reward, done, info = env.step(action)
#         if done:
#             print("Episode finished after {} timesteps".format(t+1))
#             break


# -*- coding: utf-8 -*-
import random
import gym
import numpy as np
from collections import deque
from keras.models import Sequential
from keras.layers import Dense
from keras.optimizers import Adam

# a number of games we want the agent to play.
EPISODES = 1000


class DQNAgent:
    def __init__(self, state_size, action_size):
        self.state_size = state_size
        self.action_size = action_size
        self.memory = deque(maxlen=2000)
        self.gamma = 0.95    # discount rate, to calculate the future discounted reward
        self.epsilon = 1.0  # exploration rate, this is the rate in which an agent randomly decides its action rather than prediction
        self.epsilon_min = 0.01 # we want the agent to explore at least this amount.
        self.epsilon_decay = 0.995 #we want to decrease the number of explorations as it gets good at playing games.
        self.learning_rate = 0.001
        self.model = self._build_model()

    def _build_model(self):
        # Neural Net for Deep-Q learning Model
        model = Sequential()
        model.add(Dense(24, input_dim=self.state_size, activation='relu'))
        model.add(Dense(24, activation='relu'))
        model.add(Dense(self.action_size, activation='linear'))
        model.compile(loss='mse',
                      optimizer=Adam(lr=self.learning_rate))
        return model

    def remember(self, state, action, reward, next_state, done):
        self.memory.append((state, action, reward, next_state, done))

    def act(self, state):
        if np.random.rand() <= self.epsilon:
            return random.randrange(self.action_size)

        # Predict the reward value based on the given state
        act_values = self.model.predict(state)
        return np.argmax(act_values[0])  # returns action

    def replay(self, batch_size):
        # Sample minibatch from the memory
        minibatch = random.sample(self.memory, batch_size)

        # Extract informations from each memory
        for state, action, reward, next_state, done in minibatch:
            # if done, make our target reward
            target = reward

            if not done:
                # predict the future discounted reward
                target = (reward + self.gamma *
                          np.amax(self.model.predict(next_state)[0]))

            # make the agent to approximately map
            # the current state to future discounted reward
            # We'll call that target_f
            target_f = self.model.predict(state)
            target_f[0][action] = target

            # Train the Neural Net with the state and target_f
            self.model.fit(state, target_f, epochs=1, verbose=0)
        if self.epsilon > self.epsilon_min:
            self.epsilon *= self.epsilon_decay

    def load(self, name):
        self.model.load_weights(name)

    def save(self, name):
        self.model.save_weights(name)


if __name__ == "__main__":
    env = gym.make('Pendulum-v0')
    state_size = env.observation_space.shape[0]

    action_list = [np.array([a]) for a in [-2.0, 2.0]]
    action_size =  len(action_list)
    agent = DQNAgent(state_size, action_size)
    # agent.load("./save/cartpole-dqn.h5")
    done = False
    batch_size = 32

    for e in range(EPISODES):
        state = env.reset()
        state = np.reshape(state, [1, state_size])
        for time in range(500):
            # env.render()
            action = agent.act(state)
            next_state, reward, done, _ = env.step(np.asarray(action))
            reward = reward if not done else -10
            next_state = np.reshape(next_state, [1, state_size])
            agent.remember(state, action, reward, next_state, done)
            state = next_state
            if done:
                print("episode: {}/{}, score: {}, e: {:.2}"
                      .format(e, EPISODES, time, agent.epsilon))
                break
        if len(agent.memory) > batch_size:
            agent.replay(batch_size)
        # if e % 10 == 0:
        #     agent.save("./save/cartpole-dqn.h5")
