import keras
import learners.learner_common
import os
from sklearn import preprocessing
# Learner that will rotate congestion control algs based on metrics
# Useful Notes:
# sysctl net.ipv4.tcp_available_congestion_control - displays cc's available on host

class HttpCacheLearner(learners.learner_common.KerasDelta):

    def __init__(self, learnerName, learnerMode, validationPattern):
        super(HttpCacheLearner, self).__init__(startVectorFieldNames=['bps-0', 'retransmits-0'
            , 'actionID-0'
            , 'actionID-1'
            , 'actionID-2'
            , 'actionID-3']
                                        , endVectorFieldNames=['bps-1', 'retransmits-1']
                                        , learnerName=learnerName
                                        , learnerMode=learnerMode
                                        , validationPattern=validationPattern
                                        , numberOfActions=4
                                        , epsilon=65
                                        , epochs=30
                                        , normalizationApproach='l2'
                                        , normalizationAxis=1
                                        , fieldsExemptFromNormalization=['actionID-0'
                                                                        , 'actionID-1'
                                                                        , 'actionID-2'
                                                                        , 'actionID-3'
                                                                         ]
                                        )

        self.Description = 'Rotate Congestion Control Algorithm based on metrics'
        self.InputFieldDescriptions = '{\'bps\':<float>, \'retransmits\':<int>, \'actionID\':<int>} Bits per second (bps) of the iperf run, retransmission count, and the action id corresponding to the CC used.'
        self.OutputFieldDescriptions = 'Returned CC to use: 0=cubic, 1=bbr, 2=vegas, 3=reno'

    def Reward(self, stateData):
        row = stateData.iloc[0]

        reward = float(row["bps-1"]) * 2 - float(row["retransmits-1"]) * 1
        return reward

    def BaseModelGeneration(self, modelName, inputCount):

        model = keras.models.Sequential()

        # Define model

        # Input layer
        model.add(keras.layers.Dense(50, input_shape=(inputCount,), activation='relu'))

        # Hidden layer
        model.add(keras.layers.Dense(50, activation='relu'))
        model.add(keras.layers.Dense(50, activation='relu'))

        # Output layer
        model.add(keras.layers.Dense(1))

        # Check for existing model to load in
        if os.path.exists(self.ModelFolderRoot + modelName):
            model.load_weights(self.ModelFolderRoot + modelName)

        # set the learning rate
        optimizer = keras.optimizers.Adam()

        # Finally put model together for training
        model.compile(optimizer='SGD', loss='mean_squared_error', metrics=['acc'])

        return model