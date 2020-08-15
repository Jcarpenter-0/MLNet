import os
import json
import pandas as pd
import datetime
import random
from sklearn import preprocessing


class ReinforcementLearner(object):
    """
    learnerMode = Mode to set the learner in, 0=testing, 1=training, 2=validating \n
    actionFields = dict {fieldName: rangeOfNumericInputs} \n
    validationPattern = Pandas Dataframe of action inputs \n
    """
    def __init__(self
                 , learnerName
                 , learnerMode
                 , inputFieldNames
                 , actionFields
                 , explorePercentage=65
                 , validationPattern = None
                 , traceFilePrefix = None
                 , normalizationApproach = None
                 , normalizationAxis = None
                 , fieldsExemptFromNormalization=None
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
        self.ActionFields = actionFields
        self.ValidationPattern = validationPattern
        self.LearnerMode = learnerMode
        self.Verbose = False

        self.Epsilon = explorePercentage
        self.NormalizationApproach = normalizationApproach
        self.NormalizationAxis = normalizationAxis
        self.FieldsExemptFromNormalization = fieldsExemptFromNormalization

        # Start time of the learner's session
        self.LearnerStartSession = datetime.datetime.now()

        # Some field Constants
        self.DateFormat = "%d-%m-%Y-%H-%M-%S"
        self.CoreFolderRoot = './tmp/' + learnerName + '/'
        self.ModelFolderRoot = self.CoreFolderRoot + 'models/'
        self.TracesFolderRoot = self.CoreFolderRoot + 'traces/'
        self.ReportFileName = self.CoreFolderRoot + learnerName + '-report.json'

        self.CurrentTraceFileHeaders = ['Timestamp', 'Reward', 'Normalized-Reward', 'Normalized-State']
        self.CurrentDecisionTraceFileHeaders = ['Timestamp', 'Step', 'Input-State', 'Predicted-State', 'Reward', 'Normalized-Reward']

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
                           #'ActionFields': self.ActionFields,
                           'OutputFieldDescriptions': self.OutputFieldDescriptions}

        return descriptionDict

    def ModifyState(self, state):
        """Modify the state, if at all before normalization and training/acting.
        State is python dict and expects to return one."""
        return state

    def ModifyNextActions(self, nextActions):
        """Modify the next action dict, and return it"""
        return nextActions

    def DefineActionSpace(self):
        """OVERRIDABLE, Map all the possible action states (returned as a list of dicts where each dict is the possible action row).
        \n default case is assume all action fields independent and thus multiplicative"""
        # List to hold what action para is to be used, will be n entries where n is number of action paras
        actionIndices = []

        for actionFieldNum in range(0, len(self.ActionFields)):
            actionIndices.append(0)

        # Get number of possible actions
        numberOfPossibleActions = 1

        for inputField in self.ActionFields.keys():
            inputFieldValues = self.ActionFields[inputField]

            numberOfPossibleActions = numberOfPossibleActions * len(inputFieldValues)

        # action para patterns
        inputPatterns = []

        # for all possible patterns of input paras
        for currentActionParaPatternIndex in range(0, numberOfPossibleActions):

            inputPatternDict = dict()

            # for every action and value of actions
            for index, actionField in enumerate(self.ActionFields.keys()):
                actionFieldInputRange = self.ActionFields[actionField]

                inputPlace = actionIndices[index]

                # check for wraparound
                if inputPlace != 0 and inputPlace % len(actionFieldInputRange) == 0:
                    actionIndices[index] = 0
                    inputPlace = 0

                    # increase the previous input's place as well
                    if index != 0:
                        actionIndices[index - 1] += 1

                inputPatternDict[actionField] = actionFieldInputRange[inputPlace]

                # increment the action indices
                actionIndices[index] += 1

            inputPatterns.append(inputPatternDict)

        return inputPatterns

    def Explore(self):
        """Take a curious move, to find out/probe the environment space.
        \n Default case simply picks 1 out of all possible actions defined by action space"""
        # pick a random action vector
        possibleActions = self.DefineActionSpace()

        return possibleActions[random.randint(0, len(possibleActions) - 1)]

    def Operate(self, stateData):
        """Take in raw state as python dict,
         process through RL components, then return python dict of action parameters"""

        # Dictionary for logging
        logDict = stateData.copy()

        # Optionally apply logic to modify incoming data
        stateData = self.ModifyState(stateData)

        # prep for conversion
        for key in stateData.keys():
            # box into lists each entry, for setting up dataframe
            stateData[key] = [stateData[key]]

        # Convert to data frame for training
        state = pd.DataFrame.from_dict(stateData)

        # only keep the fields defined for the learner for training/testing
        state = state[self.InputFieldNames]

        # Do potential normalization, for training
        normalizedState = state.copy()

        if self.NormalizationApproach is not None:
            # extract fields needed for normalization
            normalizeDF = normalizedState.copy()

            if self.FieldsExemptFromNormalization is not None:
                normalizeDF = normalizeDF.drop(columns=self.FieldsExemptFromNormalization)

            normalizeDF = pd.DataFrame(columns=normalizeDF.columns
                                       , data=preprocessing.normalize(normalizeDF.values
                                                                      , norm=self.NormalizationApproach
                                                                      , axis=self.NormalizationAxis))

            # return normalized fields to regular state
            for column in normalizeDF.columns:
                normalizedState[column] = normalizeDF[column]

            if self.Verbose:
                print('State-Normalized')
                print(normalizedState.head())

        # calculate reward
        logDict['Reward'] = self.Reward(state)
        logDict['Normalized-Reward'] = self.Reward(normalizedState)
        logDict['Normalized-State'] = '\"{}\"'.format(normalizedState.to_dict())
        logDict['Timestamp'] = datetime.datetime.now().strftime(self.DateFormat)
        logDict['Step'] = self.RunDuration

        logLine = ''

        # write out each of the state values
        for key in self.CurrentTraceFileHeaders:
            logLine += '{},'.format(logDict[key])

        self.CurrentTraceFileDS.write('{}\n'.format(logLine))
        self.CurrentTraceFileDS.flush()

        nextActions = dict()

        if self.LearnerMode == 2:
            patternRow = self.ValidationPattern.iloc[[self.RunDuration % len(self.ValidationPattern)]]

            for col in patternRow.columns:
                # unbox pandas data value to fit dict
                nextActions[col] = int(patternRow[col].values[0])

        # If not validating, then testing or training
        if self.LearnerMode != 2:

            # do potential training
            explore = False

            if self.Training:
                explore = self.Train(normalizedState)

            # Explore or Exploit for next action
            if explore:
                nextActions = self.Explore()
            else:
                nextActions = self.Act(state)

        self.RunDuration += 1

        # Optionally apply modification to the returned actions
        nextActions = self.ModifyNextActions(nextActions)

        return nextActions

    def Train(self, state):
        """Fit model with data from the state (as a pandas dataframe)"""
        return NotImplementedError

    def Act(self, state):
        """Apply the model to data from state (as a pandas dataframe) to make the next action"""
        return NotImplementedError

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

        for index, actionFieldKey in enumerate(self.ActionFields.keys()):

            if index == 0:
                runLogDF['ActionParasAsID'] = runLogDF[actionFieldKey].map(str)
            else:
                runLogDF['ActionParasAsID'] += runLogDF[actionFieldKey].map(str)

            if index < len(self.ActionFields.keys()):
                runLogDF['ActionParasAsID'] += '-'

        # Get the reward performance of each action
        actionInfoList = dict()

        uniqueActions = runLogDF['ActionParasAsID'].unique()

        for action in uniqueActions:
            actionDF = runLogDF[runLogDF['ActionParasAsID'] == action]
            normrewardDF = actionDF['Normalized-Reward']
            rewardDF = actionDF['Reward']

            nrmStd = normrewardDF.std()
            nrmavg = normrewardDF.mean()
            nrmCount = normrewardDF.count()
            nrmSum = normrewardDF.sum()

            std = rewardDF.std()
            avg = rewardDF.mean()
            count = rewardDF.count()
            sum = rewardDF.sum()

            actionInfoList[action] = {'mean': avg, 'std': std, 'count': int(count), 'sum': sum
                                      ,'nrm-mean': nrmavg, 'nrm-std': nrmStd, 'nrm-count': int(nrmCount), 'nrm-sum': nrmSum}

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

    def Reward(self, stateData):
        """Calculate reward from stateData (pandas dataframe), returned as a numeric value"""
        return NotImplementedError


class KerasBlackBox(ReinforcementLearner):
    """Take in inputs, define action space, learn target fields.
    Action Fields are defined as dict(nameofField, rangeOfpossiblevalues)"""
    def __init__(self
                 , learnerName
                 , learnerMode
                 , inputFieldNames
                 , actionFields
                 , targetFieldNames
                 , epochs
                 , validationPattern = None
                 , explorePercentage = 65
                 , fieldsExemptFromNormalization = None
                 , normalizationApproach = None
                 , normalizationAxis = None
                 , traceFilePrefix = None):
        super().__init__(
            learnerName=learnerName
            , learnerMode=learnerMode
            , validationPattern=validationPattern
            , explorePercentage=explorePercentage
            , inputFieldNames=inputFieldNames
            , actionFields=actionFields
            , normalizationApproach=normalizationApproach
            , normalizationAxis=normalizationAxis
            , traceFilePrefix=traceFilePrefix
            , fieldsExemptFromNormalization=fieldsExemptFromNormalization
        )

        self.Epochs = epochs
        self.TargetFields = targetFieldNames

        # Models
        self.ModelReferences = dict()

        # Feed in list of strings, the names of all the fields expected
        # The model names will be the patterns of fields and actions
        inputCount = len(inputFieldNames) - len(targetFieldNames)

        # Generate modelnames
        # Model naming scheme, 'predictedvariable'
        # Example: 'retransmits'
        for endVector in targetFieldNames:
            # Take a field, and then create a sequence of the other fields
            self.ModelReferences[endVector] = self.BaseModelGeneration(endVector, inputCount)

    def BaseModelGeneration(self, modelName, inputCount):
        """ Define the common model for predicting"""
        return NotImplementedError

    def Explore(self):
        return super(KerasBlackBox, self).Explore()

    def ModifyState(self, state):
        return super(KerasBlackBox, self).ModifyState(state)

    def ModifyNextActions(self, nextActions):
        return super(KerasBlackBox, self).ModifyNextActions(nextActions)

    def DefineActionSpace(self):
        return super(KerasBlackBox, self).DefineActionSpace()

    def Train(self, state):
        "Take the state, and the targeted values and fit them"
        for modelname in self.ModelReferences.keys():
            model = self.ModelReferences[modelname]

            # Get target values
            train_y = state[modelname]

            # Make dataframe of state, without the targeted field
            train_x = state.copy()
            train_x = train_x.drop(columns=self.TargetFields)

            # Fit action to reward, so that given an action we can see the potential impact
            trainingResult = model.fit(train_x, train_y
                                       , epochs=self.Epochs
                                       , verbose=self.Verbose)

            # Save model out
            model.save(self.ModelFolderRoot + modelname)

            if self.Verbose:
                print('Training with {} to make {}'.format(train_x, train_y))

        # Return explore/exploit
        return random.randint(1, 100) <= self.Epsilon

    def Reward(self, stateData):
        return NotImplementedError

    def Act(self, state):
        """Receive the state (dataframe) and stateData (raw state dataframe) and then act.
        You only need the raw dataframe if normalizing on the state."""

        # action para patterns
        inputPatterns = self.DefineActionSpace()

        # Go through all the possible input patterns and see what one gives highest reward
        highestRewardValue = -1
        highestRewardIndex = -1

        for inputIndex, inputPatternDict in enumerate(inputPatterns):

            newState = pd.DataFrame()

            for modelname in self.ModelReferences.keys():
                model = self.ModelReferences[modelname]

                test_x = state.copy()
                test_x = test_x.drop(columns=self.TargetFields)

                # append the inputPattern
                for col in inputPatternDict.keys():
                    # box the dict values so that they fit into the pandas dataframe
                    test_x[col] = [inputPatternDict[col]]

                # if normalizing, append the columns, then drop exempt ones, normalize, re-add exempts
                if self.NormalizationApproach is not None:
                    # extract fields needed for normalization
                    normalizeDF = test_x.copy()

                    if self.FieldsExemptFromNormalization is not None:
                        normalizeDF = normalizeDF.drop(columns=self.FieldsExemptFromNormalization)

                    normalizeDF = pd.DataFrame(columns=normalizeDF.columns
                                               , data=preprocessing.normalize(normalizeDF.values
                                            , norm=self.NormalizationApproach
                                            , axis=self.NormalizationAxis))

                    # return normalized fields to regular state
                    for column in normalizeDF.columns:
                        test_x[column] = normalizeDF[column]

                predictedValue = model.predict(test_x)[0][0]

                # Reverse the normalization of the predicted data

                # box the predicted value so that it fits into pandas dataframe
                newState[modelname] = [predictedValue]

            # calculate the reward
            rewardCalculatedFromPrediction = self.Reward(newState)

            if rewardCalculatedFromPrediction > highestRewardValue:
                highestRewardIndex = inputIndex
                highestRewardValue = rewardCalculatedFromPrediction

            # log the predicted state for the input state
            logDict = dict()

            logDict['Timestamp'] = datetime.datetime.now().strftime(self.DateFormat)
            logDict['Step'] = self.RunDuration
            logDict['Input-State'] = '\"{}\"'.format(inputPatternDict)
            logDict['Predicted-State'] = '\"{}\"'.format(newState.to_dict())
            logDict['Normalized-Reward'] = rewardCalculatedFromPrediction
            logDict['Reward'] = rewardCalculatedFromPrediction

            decLogString = ''
            for index, decLogField in enumerate(self.CurrentDecisionTraceFileHeaders):
                decLogString += '{}'.format(logDict[decLogField])

                if index < len(self.CurrentDecisionTraceFileHeaders):
                    decLogString += ','

            if self.Verbose:
                print("{}".format(decLogString))

            if self.CurrentDecisionTraceFileName is not None:
                self.CurrentDecisionTraceFileDS.write('{}\n'.format(decLogString))
                self.CurrentDecisionTraceFileDS.flush()

        returnDict = dict()

        highestRewardDF = inputPatterns[highestRewardIndex]

        for actionField in self.ActionFields.keys():
            returnDict[actionField] = int(highestRewardDF[actionField])

        if self.Verbose:
            print('Acting Return Actionset: {}'.format(str(returnDict)))

        return returnDict
