import pandas as pd
import numpy as np
import datetime
import keras
from sklearn import preprocessing

'''Useful links'''
'''https://towardsdatascience.com/building-a-deep-learning-model-using-keras-1548ca149d37'''
'''https://stats.stackexchange.com/questions/284189/simple-linear-regression-in-keras'''
''''''

# Simple script to test proper training approach
Verbose = False

# Report Output Header
TrainFile = '17-07-2020-22-57-33-training-runlogs'
TestFile = '17-07-2020-23-28-22-training-runlogs'

TARGETVALUEFIELDNAME = 'bps-1'

ReportFilePath = './Model-Training-Input-{}-Testing-Input-{}-Target-Value-{}.csv'.format(TrainFile, TestFile, TARGETVALUEFIELDNAME)
ReportHeader = 'Variation-Index' \
               ',Avg-Accuracy' \
               ',Accuracy-STD' \
               ',Max-Accuracy' \
               ',Avg-Difference' \
               ',Difference-STD' \
               ',Max-Difference' \
               ',Time-Taken' \
               ',Normalization' \
               ',Normalization-Axis' \
               ',Layer-Density' \
               ',Hidden-Layer-Count' \
               ',Layer-Activation-Function' \
               ',Loss-Function' \
               ',Optimizer' \
               ',Epochs' \
               ',Validation-Percentage' \
               '\n'

# Prep output file
ReportFileDS = open(ReportFilePath, 'w')

ReportFileDS.write(ReportHeader)
ReportFileDS.flush()

# Read in data
INPUTDF = pd.read_csv('../../experiments/experiment_02_congestion_control_micro/tmp/exp-02-cc-learner/traces/{}.csv'.format(TrainFile))
TESTDF = pd.read_csv('../../experiments/experiment_02_congestion_control_micro/tmp/exp-02-cc-learner/traces/{}.csv'.format(TestFile))

# Filter
DROPFILTER = [TARGETVALUEFIELDNAME, 'Timestamp', 'Reward', 'Exploit']

test_x = TESTDF.drop(columns=DROPFILTER)
train_x = INPUTDF.drop(columns=DROPFILTER)

# targets
train_y = INPUTDF[[TARGETVALUEFIELDNAME]]
test_y = TESTDF[[TARGETVALUEFIELDNAME]]

# Get input shape
n_cols = train_x.shape[1]

# Do variations of data?

# Training Configs
Normalizations = ['l2', 'l1']
NormalizationAxes = [1]
LayerDensities = range(25, 50, 25)
HiddenLayerCounts = range(1, 4)
LayerActivations = [
    'relu'
    , 'sigmoid'
#    , 'softmax'
#    , 'softplus'
#    , 'softsign'
#    , 'tanh'
#    , 'selu'
#    , 'elu'
#    , 'exponential'
]
LossFunctions = [
    'mean_squared_error'
#    , 'mean_absolute_error'
#    , 'mean_squared_logarithmic_error'
]
Optimizers = [
    'adam'
    , 'SGD'
#    , 'RMSprop'
#    , 'Adadelta'
#    , 'Adagrad'
#    , 'Adamax'
#    , 'Nadam'
]
Epochs = range(10, 70, 10)
ValidationSplits = [0.2]

Variations = len(LayerDensities) * len(LayerActivations) * len(LossFunctions) * len(Optimizers) * len(Epochs) * len(Normalizations) * len(NormalizationAxes) * len(HiddenLayerCounts) * len(ValidationSplits)
print('Variations: {}'.format(Variations))

LastRunTime = 999
global VariationIndex
VariationIndex = 0

def SetupAndRunModels(traininputs, traintargets, testinputs, testtargets, normalizationApproach=None, normalizationAxis=None):

    global VariationIndex

    # Build Training Model
    for activation in LayerActivations:

        for layerDensity in LayerDensities:

            for hiddenLayers in HiddenLayerCounts:

                for optimizer in Optimizers:

                    for lossFunction in LossFunctions:

                        for epochCount in Epochs:

                            for validationSplitPercentage in ValidationSplits:
                                StartTime = datetime.datetime.now()

                                model = keras.models.Sequential()

                                # Input Layer
                                model.add(keras.layers.Dense(layerDensity, activation=activation, input_shape=(n_cols,)))

                                # Hidden Layers
                                for layerNum in range(1, layerDensity):
                                    model.add(keras.layers.Dense(layerDensity, activation=activation))

                                # Output Layer
                                model.add(keras.layers.Dense(1))

                                model.compile(optimizer=optimizer, loss=lossFunction, metrics=['acc'])

                                # Train
                                results = model.fit(traininputs, traintargets, validation_split=validationSplitPercentage, epochs=epochCount)

                                accuResults = results.history['acc']

                                if Verbose:
                                    print(accuResults)

                                # Predictions
                                test_predictions = model.predict(testinputs)

                                # Differences between Actual and Predicted, adjusted by larger of two values
                                differences = []

                                for index, prediction in enumerate(test_predictions):
                                    predictionVal = prediction[0]
                                    actualVal = testtargets.iloc[index][TARGETVALUEFIELDNAME]

                                    diff = abs((predictionVal - actualVal)) / max(predictionVal, actualVal)

                                    differences.append(diff)

                                    if Verbose:
                                        print(diff)

                                EndTime = datetime.datetime.now()

                                TimeTaken = EndTime - StartTime

                                writeLine = '{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{},{}\n'.format(
                                    VariationIndex
                                    ,np.mean(accuResults)
                                    ,np.std(accuResults)
                                    ,max(accuResults)
                                    ,np.mean(differences)
                                    ,np.std(differences)
                                    ,max(differences)
                                    ,TimeTaken
                                    ,normalizationApproach
                                    ,normalizationAxis
                                    ,layerDensity
                                    ,hiddenLayers
                                    ,activation
                                    ,lossFunction
                                    ,optimizer
                                    ,epochCount
                                    ,validationSplitPercentage
                                )

                                ReportFileDS.write(writeLine)
                                ReportFileDS.flush()

                                VariationIndex += 1

                                print('Completed {}/{} {}/100'.format(VariationIndex, Variations, VariationIndex/Variations))

                                # Manual Cleanup
                                del model
                                EndTime = None
                                differences = None
                                TimeTaken = None
                                test_predictions = None
                                accuResults = None
                                results = None
                                model = None



for normalizationApproach in Normalizations:

    normalizationAxis = None
    if normalizationApproach is not None:
        # Do normalization
        for normalizationAxis in NormalizationAxes:

            # for each column, normalize then add to a data frame
            normalizedTrain_x = pd.DataFrame(columns=train_x.columns, data=preprocessing.normalize(train_x.values, norm=normalizationApproach, axis=normalizationAxis))
            normalizedTrain_y = pd.DataFrame(columns=train_y.columns, data=preprocessing.normalize(train_y.values, norm=normalizationApproach, axis=normalizationAxis))
            normalizedTest_x = pd.DataFrame(columns=test_x.columns, data=preprocessing.normalize(test_x.values, norm=normalizationApproach, axis=normalizationAxis))
            normalizedTest_y = pd.DataFrame(columns=test_y.columns, data=preprocessing.normalize(test_y.values, norm=normalizationApproach, axis=normalizationAxis))

            SetupAndRunModels(normalizedTrain_x, normalizedTrain_y
                             , normalizedTest_x, normalizedTest_y
                             , normalizationApproach, normalizationAxis)

            # manual cleanup
            del normalizedTrain_x
            del normalizedTrain_y
            del normalizedTest_x
            del normalizedTest_y

            normalizedTrain_x = None
            normalizedTrain_y = None
            normalizedTest_x = None
            normalizedTest_y = None

    else:
        SetupAndRunModels(train_x, train_y, test_x, test_y)


ReportFileDS.flush()
ReportFileDS.close()
