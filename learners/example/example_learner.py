import keras
import learners.learner_common

class ReinforcementLearner(learners.learner_common.ReinforcementLearningCore):

    def __init__(self, training):
        super().__init__('example', 2, modellayers=[keras.layers.Dense(20, input_dim=3, activation='relu')],epochcount=2, training=training)

        self.Description = 'Example Learner, will take in numeric only data, sum them, and will reward based on that sum.'
        self.InputFieldDescriptions = 'Any number of numeric fields, and the action index.'
        self.OutputFieldDescriptions = 'The recommended action ID, 0-1, 0 is low reward sum, 1 is high reward sum'

    def Reward(self, stateData):
        reward = int(stateData["state1"]) * 1 + int(stateData["state2"]) * 1
        return reward