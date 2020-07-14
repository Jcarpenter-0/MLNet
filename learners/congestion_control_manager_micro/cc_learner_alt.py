import keras
import learners.learner_common
import os
from sklearn import preprocessing
# Learner that will rotate congestion control algs based on metrics
# Useful Notes:
# sysctl net.ipv4.tcp_available_congestion_control - displays cc's available on host

class CCLearner(learners.learner_common.KerasDelta):

    def __init__(self, training):
        super(CCLearner, self).__init__(startVectorFieldNames=['bps-0', 'retransmits-0', 'actionID']
                                        , endVectorFieldNames=['bps-1', 'retransmits-1']
                                        , learnerName='cclearner'
                                        , training=training
                                        , numberOfActions=4
                                        , epsilon=65
                                        , epochs=24
                                        , normalizationApproach='l2'
                                        , normalizationAxis=1)

    def Reward(self, stateData):
        row = stateData.iloc[0]

        reward = float(row["bps-1"]) * 1 - float(row["retransmits-1"]) * 1
        return reward

    def BaseModelGeneration(self, modelName, inputCount):

        model = keras.models.Sequential()

        # Define model

        # Input layer
        model.add(keras.layers.Dense(10, input_shape=(inputCount,), activation='relu'))

        # Hidden layer
        model.add(keras.layers.Dense(20, activation='relu'))

        # Output layer
        model.add(keras.layers.Dense(1))

        # Check for existing model to load in
        if os.path.exists(self.ModelFolderRoot + modelName):
            model.load_weights(self.ModelFolderRoot + modelName)

        # set the learning rate
        optimizer = keras.optimizers.Adam()

        # Finally put model together for training
        model.compile(optimizer, loss='mse', metrics=['mse'])

        return model