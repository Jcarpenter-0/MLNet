"""
Included Learners (Note: these are just for proof of concept and some experimentation)
"""

import random
import json
import os
import learners.common
import keras as kf
import pandas as pd
from sklearn import preprocessing


class KerasEnsemblePredictive(learners.common.MLModule):

    def __init__(self, learnerDir
                 , targetFields
                 , observationFields
                 , training=True
                 , exploreChance=65
                 , epochs=30
                 , optimizer='SGD'
                 , activation='relu'
                 , layerDensity=50
                 , hiddenLayerCount=2
                 , lossfunction='mean_squared_error'
                 , metrics=['acc']
                 , normalizationApproach='l2'
                 , normalizationAxis=1
                 , fieldsExemptFromNormalization=[]):
        """A simple prediction learner. Use multiple models to predict multiple new values using the potential actions
         that make up a new 'state'."""
        super().__init__()

        # Logging and trace info
        self.CoreDir = learnerDir
        self.ModelsDir = self.CoreDir + 'models/'
        self.DecisionFields = []
        self.ConfigDescFilePath = self.CoreDir + 'learner-config.json'

        # ML info
        self.TargetFields = targetFields
        self.ObservationFields = observationFields
        self.Training = training
        self.ExploreChance = exploreChance
        self.Epochs = epochs
        self.Optimizer = optimizer
        self.Activation = activation
        self.LayerDensity = layerDensity
        self.HiddenLayerCount = hiddenLayerCount
        self.LossFunction = lossfunction
        self.Metrics = metrics

        self.ModelCount = len(targetFields)
        self.InputCount = len(observationFields) - len(self.TargetFields)
        self.ModelNamingPattern = 'model-for-{}'
        self.Models = dict()

        # Data control options
        self.NormalizationApproach = normalizationApproach
        self.NormalizationAxis = normalizationAxis
        self.FieldsExcemptFromNormalization = fieldsExemptFromNormalization

        # Ensure the path exists
        os.makedirs(self.ModelsDir, exist_ok=True)

        # Load existing Model(s), if they exist
        # Each target needs one model to predict it
        for targetField in self.TargetFields:

            modelName = self.ModelNamingPattern.format(targetField)

            modelPath = self.ModelsDir + modelName

            if os.path.exists(modelPath):
                self.Models[modelName] = kf.models.load_model(modelPath)
                print('Existing {} loaded'.format(modelName))
            else:
                model = kf.models.Sequential()

                # Input layer
                model.add(kf.layers.Dense(self.LayerDensity, input_shape=(self.InputCount,), activation=self.Activation))

                # Hidden layers
                for index in range(0, self.HiddenLayerCount):
                    model.add(kf.layers.Dense(self.LayerDensity, activation=self.Activation))

                # Output layer
                model.add(kf.layers.Dense(1))

                # Finally put model together for training
                model.compile(optimizer=optimizer, loss=self.LossFunction, metrics=self.Metrics)

                self.Models[modelName] = model

                print('New {} created'.format(modelName))

    def Operate(self, observation, reward, actionSpace, info, domainDefinition):

        # Run each model
        explore = False

        if self.Training:

            obvCopy = observation.copy()

            # Normalize the data
            if self.NormalizationApproach is not None:

                rawVals = []

                for val in observation.values():
                    rawVals.append(val)

                normedValues = preprocessing.normalize(X=[rawVals], norm=self.NormalizationApproach, axis=self.NormalizationAxis)

                for index, key in enumerate(obvCopy.keys()):
                    if key not in self.FieldsExcemptFromNormalization:
                        obvCopy[key] = normedValues[0][index]

            # Train each model
            for targetField in self.TargetFields:

                modelName = self.ModelNamingPattern.format(targetField)

                model = self.Models[modelName]

                modelPath = self.ModelsDir + modelName

                # Get target field
                train_y = obvCopy[targetField]

                train_x = obvCopy.copy()

                # Drop off the target fields (these are used as the "answers" and thus are not present in operation)
                for removeTargetField in self.TargetFields:
                    del train_x[removeTargetField]

                # Fit action to reward, so that given an action we can see the potential impact

                training_x_array = list(train_x.values())

                trainingResult = model.fit([training_x_array], [train_y], epochs=self.Epochs, verbose=False)

                # Save model out, update weights, etc
                model.save(modelPath)

            explore = random.randint(1, 100) <= self.ExploreChance

        if explore:
            # Select random action
            action = actionSpace[random.randint(0, len(actionSpace)-1)]
        else:
            # Do a "considered" action
            # Look at all the possible actions
            highestRewardValue = -1
            highestRewardIndex = -1

            for inputIndex, inputPattern in enumerate(actionSpace):

                potentialObv = dict()

                for targetField in self.TargetFields:

                    modelName = self.ModelNamingPattern.format(targetField)

                    model = self.Models[modelName]

                    # Copy the unnormalized version of the data, it will require different normalization approach here
                    test_x = observation.copy()

                    # Drop off the target fields (if they are present, shouldn't be)
                    for removeTargetField in self.TargetFields:
                        del test_x[removeTargetField]

                    # replace the input pattern based on the projected next action
                    for actionField in inputPattern.keys():
                        test_x[actionField] = inputPattern[actionField]

                    # if normalizing, append the columns, then drop exempt ones, normalize, re-add exempts
                    if self.NormalizationApproach is not None:

                        rawVals = []

                        for val in test_x.values():
                            rawVals.append(val)

                        normedValues = preprocessing.normalize([rawVals], norm=self.NormalizationApproach, axis=self.NormalizationAxis)

                        for index, key in enumerate(test_x.keys()):
                            if key not in self.FieldsExcemptFromNormalization:
                                test_x[key] = normedValues[0][index]

                    testing_x_array = list(test_x.values())

                    predictedValue = model.predict([testing_x_array])[0][0]

                    # box the predicted value so that it fits into pandas dataframe
                    potentialObv[targetField] = predictedValue

                # calculate the reward
                rewardCalculatedFromPrediction = domainDefinition.DefineReward(potentialObv)

                if rewardCalculatedFromPrediction > highestRewardValue:
                    highestRewardIndex = inputIndex
                    highestRewardValue = rewardCalculatedFromPrediction

            action = actionSpace[highestRewardIndex]

        print('Action Space {}'.format(len(actionSpace)))

        print('ML Action: {}'.format(str(action)))

        return action

    def Conclude(self):
        """Write out some kind of file that provides the configs for the learner and its experiences"""
        del self.Models
        configFP = open(self.ConfigDescFilePath, 'w')
        json.dump(self.__dict__, configFP, indent=5, skipkeys=True)
        configFP.flush()
        configFP.close()


if __name__ == '__main__':
    import learners.example_ping_manager.ping_manager

    # For testing the models

    # Setup domain definition
    domainDF = learners.example_ping_manager.ping_manager.PingExperimentExampleDomainDefinition('./tmp/')

    # Setup the ML module
    obvFields = domainDF.ObservationFields

    testModel = KerasEnsemblePredictive('./tmp/'
                                        ,['packetLoss', 'rttAvg']
                                        ,['-c', '-s', '-t', 'packetLoss', 'rttAvg'])

    testModel.Operate({'-c': 10, '-s': 56, '-t': 255, 'packetLoss': 0.0, 'rttAvg': 20.594}
                      , 10
                      , domainDF.DefineActionSpace()
                      , None
                      , domainDF)


    print()