import keras
import learners.learner_common

class ExampleLearner(learners.learner_common.KerasDelta):

    def __init__(self, training):
        super(ExampleLearner, self).__init__(startVectorFieldNames=['bps-0', 'retransmits-0']
                                        , endVectorFieldNames=['bps-1', 'retransmits-1', 'actionID']
                                        , learnerName='example-alt'
                                        , training=training
                                        , numberOfActions=4
                                        , epsilon=65
                                        , epochs=24)

        self.Description = 'Example Learner, will take in numeric only data, sum them, and will reward based on that sum.'
        self.InputFieldDescriptions = 'Any number of numeric fields, and the action index.'
        self.OutputFieldDescriptions = 'The recommended action ID, 0-1, 0 is low reward sum, 1 is high reward sum'

    def Reward(self, stateData):
        reward = int(stateData["state1"]) * 1 + int(stateData["state2"]) * 1
        return reward