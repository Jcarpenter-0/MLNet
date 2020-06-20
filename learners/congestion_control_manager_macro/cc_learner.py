import keras
import learners.learner_common

# Learner that will rotate congestion control algs based on metrics
# Useful Notes:
# sysctl net.ipv4.tcp_available_congestion_control - displays cc's available on host
#

class ReinforcementLearner(learners.learner_common.ReinforcementLearningCore):

    def __init__(self, training):
        super().__init__('congestion-control-manager', 4, modellayers=[keras.layers.Dense(8, input_dim=3, activation='relu')],epochcount=2, training=training, verbose=True)

        self.Description = 'Rotate Congestion Control Algorithm based on metrics'
        self.InputFieldDescriptions = ''
        self.OutputFieldDescriptions = 'Returned CC to use: 0=cubic, 1=reno, 2=bbr, 3=vegas'

    def Reward(self, stateData):
        reward = int(stateData["state1"]) * 1 + int(stateData["state2"]) * 1
        return reward