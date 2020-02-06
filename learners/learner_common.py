import os
import json
import pandas as pd
import numpy as np
import datetime
import keras
import random

class ReinforcementLearningCore(object):

    def __init__(self, modelname, numberofactions, training=True, verbose=False, epochcount=16,epsilon=65,
                 learningrate=0.001,lossfunction='mean_squared_error',modellayers=[]):
        """
        modelname:
        numberofactions:
        training:
        verbose:
        epochcount:
        epsilon:
        learningrate:
        lossfunction:
        modellayers:
        activation:
        """

        # Model I/O and Functional Descriptions
        self.Description = ''
        self.InputFieldDescriptions = []
        self.OutputFieldDescriptions = []

        # Configurations ----------------------------------------------------------------------------------------------
        self.Verbose = verbose
        self.DateFormat = "%d-%m-%Y-%H-%M-%S"

        # File Locations
        self.ModelName = modelname
        self.CoreFolder = './tmp/{}/'.format(self.ModelName)

        # Ensure folder creation
        os.makedirs(self.CoreFolder, exist_ok=True)

        self.ModelTraceHeader = 'Timestamp,Reward,'

        # Training flag
        self.Training = training

        self.ModelLogFilePath = self.CoreFolder + '{}-report.json'.format(self.ModelName)

        # datetime of starting
        self.DateTimeOfSessionStart = datetime.datetime.now()

        if self.Training:
            self.ModelTraceFilePath = self.CoreFolder + '{}-training-runlogs.csv'.format(self.DateTimeOfSessionStart.strftime(self.DateFormat))
        else:
            self.ModelTraceFilePath = self.CoreFolder + '{}-testing-runlogs.csv'.format(self.DateTimeOfSessionStart.strftime(self.DateFormat))

        # make trace file
        traceFileFD = open(self.ModelTraceFilePath, 'w')
        traceFileFD.flush()
        traceFileFD.close()

        self.ModelFilePath = self.CoreFolder + '{}'.format(self.ModelName)

        # number of epochs to train over (present the data obtained n times to the trainer)
        self.EpochCount = epochcount

        # threshold to explore/exploit
        self.Epsilon = epsilon

        # Total number of actions the system can take
        self.NumberOfActions = numberofactions

        # Duration Tracking, the number of training steps that occur (Note: this is presentations of the environment not the epochs)
        self.RunDuration = 0

        # Keras Model creation
        self.LearningRate = learningrate
        self.Model = keras.models.Sequential()

        self.LossFunction = lossfunction

        # Add the layers
        self.LayerCount = len(modellayers)

        # for each layer add it

        # also note the traits of the layers for the output report
        layerDescriptors = []

        for layer in modellayers:
            self.Model.add(layer)
            layerDescriptors.append({'density': layer.units})

        # Output Layer
        outputLayer = keras.layers.Dense(1)
        self.Model.add(outputLayer)

        # add output layer info to report
        layerDescriptors.append({'density': outputLayer.units})

        # Fixed/Variables ----------------------------------------------------------------------------------------------
        self.CurrentStep = 1
        self.FirstLogWrite = True

        # Last action is a explore or exploit
        self.LastActionType = 0

        if os.path.exists(self.ModelFilePath):
            # load in an existing model
            self.Model.load_weights(self.ModelFilePath)
            print('Loading existing model, {}'.format(self.ModelFilePath))
        else:
            print('No existing model present, creating new model')

            # Setup the Configurations File
            jsonBody = {'model-configurations': {
                'Epochs': self.EpochCount,
                'ExploreOrExploitChance': self.Epsilon,
                'LearningRate': self.LearningRate,
                'LossFunction': self.LossFunction,
                'Layers': layerDescriptors
            },
                'training-sessions': []
                ,
                'testing-sessions': []

            }

            mlconfigFileDS = open(self.ModelLogFilePath, 'w')

            mlconfigFileDS.write(json.dumps(jsonBody, indent=5))

            mlconfigFileDS.flush()
            mlconfigFileDS.close()

        # set the learning rate
        optimizer = keras.optimizers.Adam(lr=self.LearningRate)

        # ???
        metrics = ['accuracy']

        # Finally put model together for training
        self.Model.compile(optimizer, loss=self.LossFunction, metrics=metrics)

    # Return a Dict describing the learner, and inputs/outputs
    def Describe(self):

        descriptionDict = {'Description': self.Description,
                           'InputFieldDescriptions': self.InputFieldDescriptions,
                           'OutputFieldDescriptions': self.OutputFieldDescriptions}

        return descriptionDict

    # Take in stateData (as a Python Dict), return a command structure (as a Python Dict)
    def Operate(self, stateData):

        # Calculate Reward Value
        reward = self.Reward(stateData)

        # Write out the trace line
        traceFileDS = open(self.ModelTraceFilePath, 'a')

        # check if first time writing out
        if self.FirstLogWrite:
            self.FirstLogWrite = False

            headerLine = self.ModelTraceHeader

            # write out the state
            for key in stateData.keys():
                headerLine += ',{}'.format(key)

            traceFileDS.write(headerLine + '\n')

        # write out all the state info collected by the RL
        logLine = '{},{}'.format(datetime.datetime.now().strftime(self.DateFormat), reward)

        # write out each of the state values
        for value in stateData.values():
            logLine += ',{}'.format(value)

        traceFileDS.write('{}\n'.format(logLine))

        traceFileDS.flush()
        traceFileDS.close()

        # Get actions/commands
        actionID = -1

        # Train from state data
        if self.Training:
            # Train then return an action
            actionID = self.Train(stateData, reward)
        else:
            # Take action
            actionID = self.Act(stateData)

        # Increment Common Metrics
        self.CurrentStep += 1
        self.RunDuration += 1

        return {'ActionID': actionID}

    # Observe environment, based on epsilon either explore or exploit (seek highest reward)
    def Train(self, state, reward):

        expandedState = list(state.values())

        properlyDimensionedState = np.array(expandedState, ndmin=len(expandedState)-1)

        # Fit action to reward, so that given an action we can see the potential impact
        trainingResult = self.Model.fit(properlyDimensionedState, [reward], epochs=self.EpochCount, verbose=self.Verbose)

        if self.Verbose:
            print(str(trainingResult))

        print('Training-Reward {} State {} Action Type {}'.format(reward, state, self.LastActionType))

        # Save model out
        self.Model.save(self.ModelFilePath)

        # determine if agent will take random action, or if it will select the highest rewarding action

        # Explore or Exploit
        if random.randint(1,100) <= self.Epsilon:
            # Explore
            self.LastActionType = 0
            # Pick a random action
            selectedAction = random.randint(0,self.NumberOfActions-1)

        else:
            # Exploit
            self.LastActionType = 1
            selectedAction = self.Act(state)

        return selectedAction

    # Make actionable decision and then return
    def Act(self, state):

        # pick an action based on highest reward
        # Of all possible actions, predict reward for each, take highest
        highestReward = -1
        highestRewardActionIndex = -1

        for actionIndex in range(0, self.NumberOfActions):

            expandedState = list(state.values())

            expandedState.append(actionIndex)

            properlyDimensionedState = np.array(expandedState, ndmin=len(expandedState)-1)

            predictedReward = self.Model.predict(properlyDimensionedState)

            if self.Verbose:
                print('Predicted Reward {} for State {}'.format(predictedReward, expandedState))

            if predictedReward > highestReward:
                highestReward = predictedReward
                highestRewardActionIndex = actionIndex

        return highestRewardActionIndex

    # write out the trace file, ml report
    def Conclude(self):

        # conclusion time
        self.DateTimeOfSessionEnd = datetime.datetime.now()

        # Update the run config, read first, close, then reopen to write it back out with new info
        mlconfigFileDS = open(self.ModelLogFilePath, 'r')

        configData = json.load(mlconfigFileDS)

        mlconfigFileDS.close()

        # load in the run logs for this current run and then get the values of a reward
        runLogDF = pd.read_csv(self.ModelTraceFilePath)

        actions = runLogDF['Action'].unique()

        actionInfoList = dict()

        for action in actions:
            # get specific action stats
            actionDF = runLogDF[runLogDF['Action'] == action]

            rewardDF = actionDF['Reward']

            std = rewardDF.std()
            avg = rewardDF.mean()
            count = rewardDF.count()

            actionInfoList[int(action)] = {'mean': avg, 'std': std, 'count': int(count)}

        newFields = {'environmental-config': '--',
                     'time-training-started': self.DateTimeOfSessionStart.strftime(self.DateFormat),
                     'time-training-ended': self.DateTimeOfSessionEnd.strftime(self.DateFormat),
                     'runLengthInSteps': self.RunDuration,
                     'action-breakdown': actionInfoList}

        if self.Training:

            listOfTrainingEntries = configData['training-sessions']

            listOfTrainingEntries.append(newFields)

            configData['training-sessions'] = listOfTrainingEntries
        else:
            # Testing
            listOfTestingEntries = configData['testing-sessions']

            listOfTestingEntries.append(newFields)

            configData['testing-sessions'] = listOfTestingEntries


        mlconfigFileDS = open(self.ModelLogFilePath, 'w')

        mlconfigFileDS.write(json.dumps(configData, indent=5))

        mlconfigFileDS.flush()
        mlconfigFileDS.close()

    # Return a numeric reward value based on metrics
    def Reward(self, stateData):
        return NotImplementedError