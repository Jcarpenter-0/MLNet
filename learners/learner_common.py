import os
import json
import pandas as pd
import numpy as np
import datetime
import random
import copy
from sklearn import preprocessing

'''Base Class'''
class Learner(object):

    """"""
    def __init__(self
                 , learnerName
                 , training
                 , numberOfActions
                 , epsilon
                 , inputFieldNames
                 , normalizationApproach
                 , normalizationAxis
                 ):

        self.LearnerName = learnerName

        # Fields to describe the Learner's high level details
        self.Description = ''
        self.InputFieldDescriptions = ''
        self.OutputFieldDescriptions = ''
        self.InputFieldNames = inputFieldNames

        # Some Learner Metadata
        self.RunDuration = 0
        self.Training = training
        self.Verbose = False
        self.NumberOfActions = numberOfActions
        self.LastActionType = 0

        self.Epsilon = epsilon
        self.NormalizationApproach = normalizationApproach
        self.NormalizationAxis = normalizationAxis

        # Start time of the learner's session
        self.LearnerStartSession = datetime.datetime.now()

        # Some field Constants
        self.ActionFieldText = 'actionID'
        self.DateFormat = "%d-%m-%Y-%H-%M-%S"
        self.CoreFolderRoot = './tmp/' + learnerName + '/'
        self.ModelFolderRoot = self.CoreFolderRoot + 'models/'
        self.TracesFolderRoot = self.CoreFolderRoot + 'traces/'
        self.ReportFileName = self.CoreFolderRoot + learnerName + '-report.json'

        self.CurrentTraceFileHeaders = 'Timestamp,Reward'

        if self.Training:
            self.CurrentTraceFileName = self.TracesFolderRoot + '{}-training-runlogs.csv'.format(self.LearnerStartSession.strftime(self.DateFormat))
            self.CurrentTraceFileHeaders += ',Exploit'
        else:
            self.CurrentTraceFileName = self.TracesFolderRoot + '{}-testing-runlogs.csv'.format(self.LearnerStartSession.strftime(self.DateFormat))

        # Add extra state headers
        for inputField in self.InputFieldNames:
            self.CurrentTraceFileHeaders += ',' + inputField

        self.CurrentTraceFileHeaders += '\n'

        # Ensure folder creation
        os.makedirs(self.CoreFolderRoot, exist_ok=True)
        os.makedirs(self.ModelFolderRoot, exist_ok=True)
        os.makedirs(self.TracesFolderRoot, exist_ok=True)

        # Setup trace file
        self.CurrentTraceFileDS = open(self.CurrentTraceFileName, 'w')

        self.CurrentTraceFileDS.write(self.CurrentTraceFileHeaders)

        self.CurrentTraceFileDS.flush()

        # Setup the Configurations File
        if os.path.exists(self.ReportFileName) is False:
            jsonBody = {'learner-configurations': {

            },
                'training-sessions': []
                ,
                'testing-sessions': []
            }

            mlconfigFileDS = open(self.ReportFileName, 'w')

            mlconfigFileDS.write(json.dumps(jsonBody, indent=5))

            mlconfigFileDS.flush()
            mlconfigFileDS.close()

    # Return a Dict describing the learner, and inputs/outputs
    def Describe(self):

        descriptionDict = {'Description': self.Description,
                           'InputFieldDescriptions': self.InputFieldDescriptions,
                           'OutputFieldDescriptions': self.OutputFieldDescriptions}

        return descriptionDict

    '''Take in stateData (as a Python Dict), return a command structure (as a Python Dict)'''
    def Operate(self, stateData):
        # do potential state conversion

        # convert stateData (python dict) to pandas dataframe

        # prep for conversion
        for key in stateData.keys():
            # box into lists each entry
            stateData[key] = [stateData[key]]

        state = pd.DataFrame.from_dict(stateData)

        print('State DF {}'.format(state.shape))
        print(state.head())

        state = self.ModifyState(state)

        # Do potential normalization
        if self.NormalizationApproach is not None:
            state = pd.DataFrame(columns=state.columns
                                , data=preprocessing.normalize(state.values
                                , norm=self.NormalizationApproach
                                , axis=self.NormalizationAxis))

        print('State-Normalized')
        print(state.head())

        # calculate reward
        reward = self.Reward(state)

        # write out trace file
        if self.Training:
            logLine = '{},{},{}'.format(datetime.datetime.now().strftime(self.DateFormat), reward, self.LastActionType)
        else:
            logLine = '{},{},'.format(datetime.datetime.now().strftime(self.DateFormat), reward)

        # write out each of the state values
        for key in self.InputFieldNames:
            logLine += ',{}'.format(stateData[key][0])

        self.CurrentTraceFileDS.write('{}\n'.format(logLine))

        self.CurrentTraceFileDS.flush()

        # do potential training
        explore = False

        if self.Training:
            explore = self.Train(state)

        # Explore or Exploit for next action (will always exploit when not training)
        if explore:
            # pick a random action
            nextAction = random.randint(0, self.NumberOfActions-1)
            self.LastActionType = 0
        else:
            nextAction = self.Act(state)
            self.LastActionType = 1

        self.RunDuration += 1

        return {self.ActionFieldText: nextAction}

    """Fit model with data from the state (as a pandas dataframe)"""
    def Train(self, state):
        return NotImplementedError

    """Apply the model to data from state (as a pandas dataframe) to make the next action"""
    def Act(self, state):
        return NotImplementedError

    '''Write out logs for training sessions and the model's criterias'''
    def Conclude(self):

        # conclusion time
        self.LearnerStopSession = datetime.datetime.now()

        # close trace file
        self.CurrentTraceFileDS.flush()
        self.CurrentTraceFileDS.close()

        # Update the run config, read first, close, then reopen to write it back out with new info
        mlconfigFileDS = open(self.ReportFileName, 'r')

        configData = json.load(mlconfigFileDS)

        mlconfigFileDS.close()

        # load in the run logs for this current run and then get the values of a reward
        runLogDF = pd.read_csv(self.CurrentTraceFileName)

        actions = runLogDF[self.ActionFieldText].unique()

        actionInfoList = dict()

        for action in actions:
            # get specific action stats
            actionDF = runLogDF[runLogDF[self.ActionFieldText] == action]

            rewardDF = actionDF['Reward']

            std = rewardDF.std()
            avg = rewardDF.mean()
            count = rewardDF.count()

            actionInfoList[int(action)] = {'mean': avg, 'std': std, 'count': int(count)}

        newFields = {'time-training-started': self.LearnerStartSession.strftime(self.DateFormat),
                     'time-training-ended': self.LearnerStopSession.strftime(self.DateFormat),
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

        mlconfigFileDS = open(self.ReportFileName, 'w')

        mlconfigFileDS.write(json.dumps(configData, indent=5))

        mlconfigFileDS.flush()
        mlconfigFileDS.close()
        print('Model Output Report Written')

    # Return a numeric reward value based on metrics
    def Reward(self, stateData):
        return NotImplementedError

    # Possibly trim the state here or modify if you wish
    def ModifyState(self, stateData):
        return stateData

'''Keras implementation of a multi-model future state predictive algorithm'''
'''Takes in a starter vector plus finish vector with action transition'''

'''Useful links'''
'''https://towardsdatascience.com/building-a-deep-learning-model-using-keras-1548ca149d37'''
'''https://stats.stackexchange.com/questions/284189/simple-linear-regression-in-keras'''
''''''
class KerasDelta(Learner):

    """Start Vector is the initial values or a first run state
    End Vector is the values of a second run to contrast with first run, plus the action that got there
    """
    def __init__(self
                 , startVectorFieldNames
                 , endVectorFieldNames
                 , learnerName
                 , training
                 , numberOfActions
                 , epsilon
                 , epochs
                 , normalizationApproach
                 , normalizationAxis
                 ):
        inputFieldNames = copy.deepcopy(startVectorFieldNames)
        inputFieldNames.extend(endVectorFieldNames)
        super().__init__(
                        learnerName=learnerName
                         , training=training
                         , numberOfActions=numberOfActions
                         , epsilon=epsilon
                         , inputFieldNames=inputFieldNames
                        , normalizationAxis=normalizationAxis
                        , normalizationApproach=normalizationApproach
        )

        self.Epochs = epochs
        self.StartVectorFieldNames = startVectorFieldNames
        self.EndVectorFieldNames = endVectorFieldNames

        # Models
        self.ModelReferences = dict()

        # Feed in list of strings, the names of all the fields expected
        # The model names will be the patterns of fields and actions
        inputCount = len(startVectorFieldNames)

        # Generate modelnames
        # Model naming scheme, 'predictedvariable'
        # Example: 'retransmits'
        for endVector in endVectorFieldNames:

            # Take a field, and then create a sequence of the other fields
            self.ModelReferences[endVector] = self.BaseModelGeneration(endVector, inputCount)

    '''Return new instance of a keras model, fully compiled'''
    def BaseModelGeneration(self, modelName, inputCount):
        return NotImplementedError

    '''Hand the state off to each of the models'''
    def Train(self, state):

        for modelname in self.ModelReferences.keys():

            model = self.ModelReferences[modelname]

            # Get target values
            train_y = state[modelname]

            # Make dataframe of state, without the targeted field
            train_x = state.copy()
            train_x = train_x.drop(columns=self.EndVectorFieldNames)

            # Fit action to reward, so that given an action we can see the potential impact
            trainingResult = model.fit(train_x, train_y
                                       , epochs=self.Epochs
                                       , verbose=self.Verbose)

            # Save model out
            model.save(self.ModelFolderRoot + modelname)

        # Return explore/exploit
        return random.randint(1, 100) <= self.Epsilon

    def Reward(self, stateData):
        return NotImplementedError

    '''Predict the next state based on potential actions and then pick highest rewarding entry'''
    def Act(self, state):

        highestRewardingAction = -1
        highestReward = -1

        # For each action, try to predict it's impact on the new state
        for actionID in range(0, self.NumberOfActions):

            newState = pd.DataFrame()

            for modelname in self.ModelReferences.keys():

                model = self.ModelReferences[modelname]

                # Make dataframe of state, without the targeted field
                test_x = state.copy()
                test_x = test_x.drop(columns=self.EndVectorFieldNames)
                # Set action id
                test_x[self.ActionFieldText] = [actionID]

                predictedValue = model.predict(test_x)[0][0]

                print('Predicted {} {}'.format(modelname, predictedValue))

                newState[modelname] = [predictedValue]
                print(newState)


            # Analyze the predicted new state, do reward calculation
            newStateString = ''

            for key in newState.columns:
                newStateString += '{}:{}'.format(key, newState.iloc[0][key])

            print('Predicted new Action {} State {}'.format(actionID, newStateString))

            calcReward = self.Reward(newState)

            print('Predicted new Action {} State {} Reward:{}'.format(actionID, newStateString, calcReward))

            if calcReward > highestReward:
                highestReward = calcReward
                highestRewardingAction = actionID

        # End action For
        return highestRewardingAction
