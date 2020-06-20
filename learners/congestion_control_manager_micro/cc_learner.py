import keras
import learners.learner_common
from sklearn import preprocessing
# Learner that will rotate congestion control algs based on metrics
# Useful Notes:
# sysctl net.ipv4.tcp_available_congestion_control - displays cc's available on host
#

class ReinforcementLearner(learners.learner_common.ReinforcementLearningCore):

    def __init__(self, training):
        super().__init__('congestion-control-manager', 4,
                         modellayers=[keras.layers.Dense(8, input_dim=3, activation='relu')
                             , keras.layers.Dense(8, activation='relu')]
                         ,epochcount=4, training=training, verbose=True)

        self.Description = 'Rotate Congestion Control Algorithm based on metrics'
        self.InputFieldDescriptions = '{\'bps\':<float>, \'retransmits\':<int>, \'actionID\':<int>} Bits per second (bps) of the iperf run, retransmission count, and the action id corresponding to the CC used.'
        self.OutputFieldDescriptions = 'Returned CC to use: 0=cubic, 1=bbr, 2=vegas, 3=reno'

    def ModifyState(self, stateData):

        

        return preprocessing.normalize(stateData)

    def Reward(self, stateData):
        reward = int(stateData["bps"]/1000000) * 1 - int(stateData["retransmits"]) * 1
        return reward