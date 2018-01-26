from gym.envs.registration import register

register(
    id='trading-v0',
    entry_point='reinforcement.env:MyEnv',
    timestep_limit=1000,
)
