import keras
import learners.learner_common
import os

class Learner(learners.learner_common.KerasBlackBox):

    def __init__(self, learnerName, learnerMode, validationPattern, traceFilePrefix):
        super().__init__(
            learnerName=learnerName,
            learnerMode=learnerMode,
            validationPattern=validationPattern
                         , inputFieldNames=[
                    "-c",
                    "-s",
                    "-t",
                    "packetLoss",
                    "rttAvg"
            ]
                         , actionFields={
                    "-c": [10],
                    "-s": range(56, 896, 56),
                    "-t": [255]
            }
                         , targetFieldNames=[
                    "packetLoss",
                    "rttAvg"
            ]
                         , epochs=24
                         , normalizationApproach='l2'
                         , normalizationAxis=1
                         , traceFilePrefix=traceFilePrefix)

    def Reward(self, stateData):
        row = stateData.iloc[0]

        reward = 0 - float(row["rttAvg"]) * 1 - float(row["packetLoss"]) * 3
        return reward

    def BaseModelGeneration(self, modelName, inputCount):
        # Check for existing model to load in
        if os.path.exists(self.ModelFolderRoot + modelName):
            model = keras.models.load_model(self.ModelFolderRoot + modelName)

            print('Previous model loaded')
        else:
            model = keras.models.Sequential()

            # Define model

            # Input layer
            model.add(keras.layers.Dense(50, input_shape=(inputCount,), activation='relu'))

            # Hidden layer
            model.add(keras.layers.Dense(50, activation='relu'))
            model.add(keras.layers.Dense(50, activation='relu'))

            # Output layer
            model.add(keras.layers.Dense(1))

            # Finally put model together for training
            model.compile(optimizer='SGD', loss='mean_squared_error', metrics=['acc'])

        return model