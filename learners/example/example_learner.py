from sklearn import preprocessing
import keras
import learners.learner_common

CCs = ['cubic','bbr','reno','vegas']

class ReinforcementLearner(learners.learner_common.ReinforcementLearningCore):

    def __init__(self, training=True):
        super().__init__('cc-rl', 4, modellayers=[keras.layers.Dense(20, input_dim=3, activation='relu'),
                     keras.layers.Dense(20, activation='relu'),
                     keras.layers.Dense(20, activation='relu'),
                     keras.layers.Dense(20, activation='relu')], training=training)

    # EDITABLE - Observe environment and return the relevant environmental states/info
    def ObserveEnvironment(self, clientLogJson, serverLogJson, networkLogJson):

        # extract state
        # REWARD LOGIC
        # For a CC ML, should take into account high bandwidths, low RTTs,
        try:

            bandwidth = serverLogJson['logs']['end']['sum_sent']['bits_per_second']
            retrans = serverLogJson['logs']['end']['sum_sent']['retransmits']
            state = {'bandwidth':bandwidth, 'retransmits':retrans}

            # bandwidth - retransmits
            reward = (bandwidth - retrans)

        except Exception as ex:
            print(str(ex))
            print('skipping sample')
            reward = None
            state = None

        return state, reward

    # EDITABLE - Resolve the picked action to actual environment impact
    def TakeAction(self, actionIndex):

        # based on selected actionIndex, take an action
        if actionIndex != -1:
            # Cubic
            self.Network.CC = CCs[actionIndex]

        print('{}|{}'.format(actionIndex, self.Network.CC))