import gym
from gym import spaces
import numpy as np
import random

class LakeEnv(gym.Env):
    """Lake Environment modeling a dam control system in a generic lake. For now only the como lake system is available"""
    metadata = {'render.modes': ['human']}

    def __init__(self, inflow, demand, lake, h_flo=1.24, initial_inflow=20, integration_steps=24, flooding_penalty=-1):
        super(LakeEnv, self).__init__()
        self.MAX_RELEASE = 491.61 #to be checked
        self.MIN_RELEASE = 0 #to be checked

        self.actions_values = [0, 
                              79.38777777777779,
                              88.09601136363636,
                              110.38678125,
                              148.3911666666667,
                              200.13165573770488,
                              225.25006557377043, 
                              491.61]
        self.N_DISCRETE_ACTIONS = len(self.actions_values)
        # Define action and observation space
        # They must be gym.spaces objects
        # Example when using discrete actions:
        self.action_space = spaces.Discrete(self.N_DISCRETE_ACTIONS)#spaces.Box(low=self.MIN_RELEASE, high=self.MAX_RELEASE, shape=(1,), dtype=np.float32)
        # Example for using image as input:
        low = np.array([-1, -1, -0.5])#to be checked
        high = np.array([1, 1, 1.3])#to be checked
        self.observation_space = spaces.Box(low=np.float32(low), high=np.float32(high), dtype=np.float32)
        self.inflow = inflow
        self.t = 0
        self.period = len(inflow)
        self.horizon = len(inflow)
        self.demand = demand
        self.h_flo = h_flo
        self.lake = lake
        self.s = np.zeros(self.period+1)
        self.h = np.zeros(self.period+1)
        self.r = np.zeros(self.period)
        self.h[self.t] = lake.initial_cond
        self.s[self.t] = lake.levelToStorage(self.h[self.t])
        self.qIn = None
        self.qIn_1 = initial_inflow
        self.integration_steps = integration_steps
        self.flooding_penalty = flooding_penalty
        self.gamma = 0.9999


    def step(self, action):
        # Execute one time step within the environment
        action = self.actions_values[action]
        self.qIn = self.inflow[self.t]
        self.s[self.t+1], self.r[self.t] = self.lake.integrate(self.integration_steps, self.t, self.s[self.t], action, self.qIn)
        self.h[self.t+1] = self.lake.storageToLevel(self.s[self.t+1])
        self.qIn_1 = self.qIn
        self.t += 1
        done = self.period == self.t

        obs = np.array([np.sin(2 * np.pi * (self.t + 1) / self.period), np.cos(2 * np.pi * (self.t + 1) / self.period),
             self.h[self.t]])

        alpha = 1/3
        beta = 1/(356.434)**2
        reward = alpha*beta*self.deficitBeta() + alpha*(self.flooding_penalty if self.h[self.t] > self.h_flo else 0) - alpha*np.abs(action - self.r[self.t-1])/self.MAX_RELEASE

        return obs, reward, done, {}

    def reset(self, inflow=None, demand=None, lake=None, h_flow=None, initial_inflow=None, integration_steps=24):
        if inflow is not None:
            self.inflow = inflow
            self.period = len(self.inflow)
        if lake is not None:
            self.lake = lake
        if demand is not None:
            self.demand = demand
        if h_flow is not None:
            self.h_flo = h_flow
        if initial_inflow is not None:
            self.qIn_1 = initial_inflow

        self.lake.initial_cond = np.random.uniform(-0.5, 1.23)

        self.qIn = None
        self.t = 0
        self.s = np.zeros(self.period+1)
        self.h = np.zeros(self.period+1)
        self.r = np.zeros(self.period)
        self.h[self.t] = self.lake.initial_cond
        self.s[self.t] = self.lake.levelToStorage(self.h[self.t])
        self.integration_steps = integration_steps

        obs = [np.sin(2*np.pi*(self.t+1)/self.period), np.cos(2*np.pi*(self.t+1)/self.period),
             self.h[self.t]]
        return np.array(obs)

    def render(self, mode='human', close=False):
        # Render the environment to the screen
        pass

    def seed(self, seed=None):
        if seed is not None:
            np.random.seed(seed)
            random.seed(seed)
            return [seed]
        else:
            np.random.seed(7)
            random.seed(7)
            return [7]

    def deficitBeta(self):
        qdiv = self.r[self.t-1] - self.lake.minEnvFlow[self.t-1]
        if qdiv < 0:
            qdiv = 0
        d = self.demand[self.t-1] - qdiv
        if d < 0:
            d = 0
        if self.period == 365:
            if self.t > 120 and self.t <= 243: # from may to august
                d = 2*d
        else:
            if self.t > 121 and self.t <= 244: # from may to august
                d = 2*d

        return -d**2


# UNIT TESTING
if __name__ == '__main__':
    import pandas as pd
    from lakecomo import Lakecomo
    random.seed(7)
    np.random.seed(7)

    como_data = pd.read_csv('data/como_data.csv')
    Demand = np.loadtxt('data/comoDemand.txt')  # se anno bisestile aggiungi il 29 febbraio copiando la domanda del 28
    minEnvFlow = np.loadtxt('data/MEF_como.txt')
    actions = np.loadtxt("data/actions.txt")

    Inflow = np.loadtxt("data/comoInflowSim.txt")#como_data.loc[como_data['year'] == 1946, 'in']
    initial_condition = 0.35#como_data.loc[como_data['year'] == 1946, 'h'].values[0]
    Lake = Lakecomo(None, None, minEnvFlow, None, None, initial_cond=initial_condition)
    env = LakeEnv(Inflow, Demand, Lake)
    env.seed(7)

    obs, done, reward, t = env.reset(), False, 0.0, 0

    while not done:
        action = np.random.randint(0, 19)#actions[t]#np.random.uniform(0, 491.61)  # env.action_space.sample() uses custom samplers, need to set their seeds for deterministic behavior
        obs, rew, done, _ = env.step(action)
        print('t-action-reward:', t, action, rew)
        reward += rew
        t += 1
    print('Final reward:', reward)
    print('Avg reward:', reward / t)
    print('Final length:', t)