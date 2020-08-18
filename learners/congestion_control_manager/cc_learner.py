import keras
import learners.learner_common
import os

class CCLearner(learners.learner_common.KerasBlackBox):

    def __init__(self, learnerName, learnerMode, validationPattern, traceFilePrefix):
        super(CCLearner, self).__init__(inputFieldNames=[
            'bps-0'
            , 'retransmits-0'
            , 'cubic'
            , 'bbr'
            , 'vegas'
            , 'reno'
            , 'bps-1'
            , 'retransmits-1']
            , actionFields={
                'cubic': range(0, 1),
                'bbr': range(0, 1),
                'vegas': range(0, 1),
                'reno': range(0, 1)
            }
            , targetFieldNames=[
                'bps-1'
                ,'retransmits-1'
            ]
                                        , learnerName=learnerName
                                        , learnerMode=learnerMode
                                        , validationPattern=validationPattern
                                        , explorePercentage=65
                                        , epochs=30
                                        , normalizationApproach='l2'
                                        , normalizationAxis=1
                                        , traceFilePrefix=traceFilePrefix
                                        , fieldsExemptFromNormalization=['cubic'
                                                                        , 'bbr'
                                                                        , 'vegas'
                                                                        , 'reno'
                                                                         ]
                                        )

        self.Description = 'Rotate Congestion Control Algorithm based on metrics'
        self.InputFieldDescriptions = '{\'bps\':<float>, \'retransmits\':<int>, \'actionID\':<int>}'
        self.OutputFieldDescriptions = 'Returned CC to use'

    def Reward(self, stateData):
        row = stateData.iloc[0]

        reward = float(row["bps-1"]) * 2 - float(row["retransmits-1"]) * 1
        return reward

    def DefineActionSpace(self):

        possibleActions = []

        # the actions are binary, only exclusive or allowed
        exclusiveBinaryORGroup = ['cubic', 'bbr', 'reno', 'vegas']

        for activeIndex, activeBinaryChoice in enumerate(exclusiveBinaryORGroup):
            actionPattern = dict()

            actionPattern[activeBinaryChoice] = 1

            for otherIndex, otherBinaryChoice in enumerate(exclusiveBinaryORGroup):
                if activeIndex != otherIndex:
                    actionPattern[otherBinaryChoice] = 0

            possibleActions.append(actionPattern)

        return possibleActions

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