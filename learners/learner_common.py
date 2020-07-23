import os
import json
import pandas as pd
import datetime
import random
import copy
from sklearn import preprocessing

'''Base Class'''
class ReinforcementLearner(object):

    """Learner Definition
    learnerMode = Mode to set the learner in, 0=testing, 1=training, 2=validating"""
    def __init__(self
                 , learnerName
                 , learnerMode
                 , validationPattern
                 , numberOfActions
                 , epsilon
                 , inputFieldNames
                 , normalizationApproach
                 , normalizationAxis
                 , traceFilePrefix
                 , fieldsExemptFromNormalization=[]
                 ):

        self.LearnerName = learnerName

        # Fields to describe the Learner's high level details
        self.Description = ''
        self.InputFieldDescriptions = ''
        self.OutputFieldDescriptions = ''
        self.InputFieldNames = inputFieldNames

        # Some Learner Metadata
        self.RunDuration = 0
        self.Training = learnerMode == 1
        self.ValidationPattern = validationPattern
        self.LearnerMode = learnerMode
        self.Verbose = False
        self.NumberOfActions = numberOfActions

        self.Epsilon = epsilon
        self.NormalizationApproach = normalizationApproach
        self.NormalizationAxis = normalizationAxis
        self.FieldsExemptFromNormalization = fieldsExemptFromNormalization

        # Start time of the learner's session
        self.LearnerStartSession = datetime.datetime.now()

        # Some field Constants
        self.ActionFieldText = 'actionID-{}'
        self.ReturnBodyText = 'actionID'
        self.DateFormat = "%d-%m-%Y-%H-%M-%S"
        self.CoreFolderRoot = './tmp/' + learnerName + '/'
        self.ModelFolderRoot = self.CoreFolderRoot + 'models/'
        self.TracesFolderRoot = self.CoreFolderRoot + 'traces/'
        self.ReportFileName = self.CoreFolderRoot + learnerName + '-report.json'

        self.CurrentTraceFileHeaders = ['Timestamp', 'Reward']
        self.CurrentDecisionTraceFileHeaders = ['Timestamp', 'Step', 'ActionID', 'Predicted-State', 'Reward', 'Input-State']

        # Add the state fields
        self.CurrentTraceFileHeaders.extend(inputFieldNames)

        # Set to Nones at first, then populate via mode
        self.CurrentDecisionTraceFileName = None

        # Setup for the modes
        if self.LearnerMode == 0:
            # Testing
            self.CurrentTraceFileName = self.TracesFolderRoot + '{}-{}-testing-runlogs.csv'.format(
                self.LearnerStartSession.strftime(self.DateFormat), traceFilePrefix)
            self.CurrentDecisionTraceFileName = self.TracesFolderRoot + '{}-{}-testing-declog.csv'.format(
                self.LearnerStartSession.strftime(self.DateFormat), traceFilePrefix)

        elif self.LearnerMode == 1:
            # Training
            self.CurrentTraceFileName = self.TracesFolderRoot + '{}-{}-training-runlogs.csv'.format(self.LearnerStartSession.strftime(self.DateFormat), traceFilePrefix)
            self.CurrentDecisionTraceFileName = self.TracesFolderRoot + '{}-{}-training-declog.csv'.format(self.LearnerStartSession.strftime(self.DateFormat), traceFilePrefix)

        elif self.LearnerMode == 2:
            # Validating
            self.CurrentTraceFileName = self.TracesFolderRoot + '{}-{}-validation-runlogs.csv'.format(
                self.LearnerStartSession.strftime(self.DateFormat), traceFilePrefix)

        # Ensure folder creation
        os.makedirs(self.CoreFolderRoot, exist_ok=True)
        os.makedirs(self.ModelFolderRoot, exist_ok=True)
        os.makedirs(self.TracesFolderRoot, exist_ok=True)

        # Setup trace files
        self.CurrentTraceFileDS = open(self.CurrentTraceFileName, 'w')

        self.CurrentTraceFileHeaderString = ''

        for index, header in enumerate(self.CurrentTraceFileHeaders):
            self.CurrentTraceFileHeaderString += header

            if index < len(self.CurrentTraceFileHeaders):
                self.CurrentTraceFileHeaderString += ','

        self.CurrentTraceFileHeaderString += '\n'

        self.CurrentTraceFileDS.write(self.CurrentTraceFileHeaderString)
        self.CurrentTraceFileDS.flush()

        if self.CurrentDecisionTraceFileName is not None:
            self.CurrentDecisionTraceFileDS = open(self.CurrentDecisionTraceFileName, 'w')

            self.CurrentDecisionTraceFileHeadersString = ''

            for index, header in enumerate(self.CurrentDecisionTraceFileHeaders):
                self.CurrentDecisionTraceFileHeadersString += header

                if index < len(self.CurrentDecisionTraceFileHeaders):
                    self.CurrentDecisionTraceFileHeadersString += ','

            self.CurrentDecisionTraceFileHeadersString += '\n'

            self.CurrentDecisionTraceFileDS.write(self.CurrentDecisionTraceFileHeadersString)
            self.CurrentDecisionTraceFileDS.flush()

        # Setup the Configurations File
        if os.path.exists(self.ReportFileName) is False:
            jsonBody = {'learner-configurations': {

            },
                'training-sessions': []
                ,
                'testing-sessions': []
                ,
                'validation-sessions': []
            }

            mlconfigFileDS = open(self.ReportFileName, 'w')

            mlconfigFileDS.write(json.dumps(jsonBody, indent=5))

            mlconfigFileDS.flush()
            mlconfigFileDS.close()

    # Return a Dict describing the learner, and inputs/outputs
    def Describe(self):

        descriptionDict = {'Description': self.Description,
                           'Mode': self.LearnerMode,
                           'InputFieldDescriptions': self.InputFieldDescriptions,
                           'OutputFieldDescriptions': self.OutputFieldDescriptions}

        return descriptionDict

    def ModifyState(self, state):
        """Modify the state, if at all before normalization and training/acting. State is panda dataframe and expects to return one."""
        return state

    '''Take in stateData (as a Python Dict), return a command structure (as a Python Dict)'''
    def Operate(self, stateData):

        # Dictionary for logging
        logDict = stateData.copy()

        # prep for conversion
        for key in stateData.keys():
            # box into lists each entry
            stateData[key] = [stateData[key]]

        # Convert to data frame for training
        state = pd.DataFrame.from_dict(stateData)

        # only keep the fields defined for the learner for training/testing
        state = state[self.InputFieldNames]

        state = self.ModifyState(state)

        if self.Verbose:
            print('State DF {}'.format(state.shape))
            print(state.head())

        # Do potential normalization, for training
        if self.NormalizationApproach is not None:
            # extract fields needed for normalization
            normalizeDF = state.copy()
            normalizeDF = normalizeDF.drop(columns=self.FieldsExemptFromNormalization)

            normalizeDF = pd.DataFrame(columns=normalizeDF.columns
                                , data=preprocessing.normalize(normalizeDF.values
                                , norm=self.NormalizationApproach
                                , axis=self.NormalizationAxis))

            # return normalized fields to regular state
            for column in normalizeDF.columns:
                state[column] = normalizeDF[column]

            if self.Verbose:
                print('State-Normalized')
                print(state.head())

        # calculate reward
        logDict['Reward'] = self.Reward(state)
        logDict['Timestamp'] = datetime.datetime.now().strftime(self.DateFormat)
        logDict['Step'] = self.RunDuration

        logLine = ''

        # write out each of the state values
        for key in self.CurrentTraceFileHeaders:
            logLine += '{},'.format(logDict[key])

        self.CurrentTraceFileDS.write('{}\n'.format(logLine))

        self.CurrentTraceFileDS.flush()

        # do potential training
        explore = False

        if self.Training:
            explore = self.Train(state)

        if self.LearnerMode == 2:
            nextAction = self.ValidationPattern[self.RunDuration % len(self.ValidationPattern)]

        # If not validating, testing or training
        if self.LearnerMode != 2:

            # Explore or Exploit for next action
            if explore:
                # pick a random action
                nextAction = random.randint(0, self.NumberOfActions-1)
            else:
                nextAction = self.Act(state)

        self.RunDuration += 1

        return {self.ReturnBodyText: nextAction}

    """Fit model with data from the state (as a pandas dataframe)"""
    def Train(self, state):
        return NotImplementedError

    """Apply the model to data from state (as a pandas dataframe) to make the next action"""
    def Act(self, state):
        return NotImplementedError

    '''Write out logs for training sessions and the model's criteria'''
    def Conclude(self):

        # conclusion time
        self.LearnerStopSession = datetime.datetime.now()

        # close trace file
        self.CurrentTraceFileDS.flush()
        self.CurrentTraceFileDS.close()

        if self.CurrentDecisionTraceFileName is not None:
            self.CurrentDecisionTraceFileDS.flush()
            self.CurrentDecisionTraceFileDS.close()

        # Update the run config, read first, close, then reopen to write it back out with new info
        mlconfigFileDS = open(self.ReportFileName, 'r')

        configData = json.load(mlconfigFileDS)

        mlconfigFileDS.close()

        # load in the run logs for this current run and then get the values of a reward
        runLogDF = pd.read_csv(self.CurrentTraceFileName)

        # Get the reward performance of each action
        actionInfoList = dict()

        for index in range(0, self.NumberOfActions):
            actionField = self.ActionFieldText.format(index)
            actionDF = runLogDF[runLogDF[actionField] == 1]
            rewardDF = actionDF['Reward']

            std = rewardDF.std()
            avg = rewardDF.mean()
            count = rewardDF.count()

            actionInfoList[int(index)] = {'mean': avg, 'std': std, 'count': int(count)}


        newFields = {'time-started': self.LearnerStartSession.strftime(self.DateFormat),
                     'time-ended': self.LearnerStopSession.strftime(self.DateFormat),
                     'trace-file': self.CurrentTraceFileName,
                     'runLengthInSteps': self.RunDuration,
                     'action-breakdown': actionInfoList}

        if self.LearnerMode == 0:
            # Testing
            listOfTestingEntries = configData['testing-sessions']

            listOfTestingEntries.append(newFields)

            configData['testing-sessions'] = listOfTestingEntries

        elif self.LearnerMode == 1:
            # Training
            listOfTrainingEntries = configData['training-sessions']

            listOfTrainingEntries.append(newFields)

            configData['training-sessions'] = listOfTrainingEntries

        elif self.LearnerMode == 2:
            # Validating
            listOfValidationEntries = configData['validation-sessions']

            listOfValidationEntries.append(newFields)

            configData['validation-sessions'] = listOfValidationEntries


        mlconfigFileDS = open(self.ReportFileName, 'w')

        mlconfigFileDS.write(json.dumps(configData, indent=5))

        mlconfigFileDS.flush()
        mlconfigFileDS.close()
        print('Model Output Report Written')

    # Return a numeric reward value based on metrics
    def Reward(self, stateData):
        return NotImplementedError

'''Keras implementation of a multi-model future state predictive algorithm'''
'''Takes in a starter vector plus finish vector with action transition'''

'''Useful links'''
'''https://towardsdatascience.com/building-a-deep-learning-model-using-keras-1548ca149d37'''
'''https://stats.stackexchange.com/questions/284189/simple-linear-regression-in-keras'''
''''''
class KerasDelta(ReinforcementLearner):

    """Start Vector is the initial values or a first run state
    End Vector is the values of a second run to contrast with first run, plus the action that got there
    """
    def __init__(self
                 , startVectorFieldNames
                 , endVectorFieldNames
                 , learnerName
                 , learnerMode
                 , numberOfActions
                 , epsilon
                 , epochs
                 , normalizationApproach
                 , normalizationAxis
                 , traceFilePrefix
                 , fieldsExemptFromNormalization=[]
                 , validationPattern = None
                 ):
        inputFieldNames = copy.deepcopy(startVectorFieldNames)
        inputFieldNames.extend(endVectorFieldNames)
        super().__init__(
                        learnerName=learnerName
                         , learnerMode=learnerMode
                         , validationPattern=validationPattern
                         , numberOfActions=numberOfActions
                         , epsilon=epsilon
                         , inputFieldNames=inputFieldNames
                        , normalizationAxis=normalizationAxis
                        , normalizationApproach=normalizationApproach
                        , traceFilePrefix=traceFilePrefix
                        , fieldsExemptFromNormalization=fieldsExemptFromNormalization
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
                # blank the other actions

                for subActID in range(0, self.NumberOfActions):
                    test_x[self.ActionFieldText.format(subActID)] = [0]

                test_x[self.ActionFieldText.format(actionID)] = [1]

                predictedValue = model.predict(test_x)[0][0]

                newState[modelname] = [predictedValue]


            # Analyze the predicted new state, do reward calculation
            newStateString = ''

            for key in newState.columns:
                newStateString += '{}:{}|'.format(key, newState.iloc[0][key])

            calcReward = self.Reward(newState)

            if calcReward > highestReward:
                highestReward = calcReward
                highestRewardingAction = actionID

            if self.Verbose:
                print('Predicted new Action {} State {} Reward:{}'.format(actionID, newStateString, calcReward))

            logLine = '{},{},{},{},{},{}\n'.format(datetime.datetime.now().strftime(self.DateFormat)
                                                   , self.RunDuration
                                                   , actionID
                                                   , newStateString
                                                   , calcReward
                                                   , state.to_dict())

            self.CurrentDecisionTraceFileDS.write(logLine)

            self.CurrentDecisionTraceFileDS.flush()

        # End action For
        return highestRewardingAction
