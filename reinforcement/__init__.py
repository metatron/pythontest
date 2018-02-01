from gym.envs.registration import register

register(
    id='trading-v0',
    entry_point='reinforcement.env:MyEnv',
    timestep_limit=1000,
)


register(
    id='maze-v0',
    entry_point='reinforcement.originalenv:MazeEnv',
    timestep_limit=1000,
)
