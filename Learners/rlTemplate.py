import base64
import sys
import os
import json
import numpy as np
import tensorflow as tf
import time
import keras
import random
import matplotlib.pyplot as plt
from sklearn import preprocessing

# https://keras.io/
# Handy links
# https://towardsdatascience.com/building-a-deep-learning-model-using-keras-1548ca149d37
# https://towardsdatascience.com/reinforcement-learning-w-keras-openai-dqns-1eed3a5338c
# https://stats.stackexchange.com/questions/284189/simple-linear-regression-in-keras
# https://matplotlib.org/devdocs/gallery/subplots_axes_and_figures/subplots_demo.html

# Observe, Reward, Respond
class ReinforcementLearner:

    def __init__(self, server, client, network, loadModelPath, training=True):

        # Configurations ----------------------------------------------------------------------------------------------

        self.Verbose = False

        # Training flag
        self.Training = training
        self.TraceOutputDir = './OutputLogs/'

        # number of epochs to train over (present the data obtained n times to the trainer)
        self.EpochCount = 32

        # threshold to explore/exploit
        self.Epsilon = 65

        # Total number of actions the system can take
        self.NumberOfActions = 4

        self.LearningRate = 0.001

        # Keras Model creation
        self.Model = keras.models.Sequential()

        self.ModelFilePath = './tmp/model'
        self.ModelLogFilePath = './tmp/model-report.json'

        # Testing logs
        self.TestingFilePath = './tmp/testing.json'

        self.ActivationStyle = 'relu'
        self.LossFunction = "mean_squared_error"

        # Add the layers
        self.LayerCount = 4
        # input shape should match the number of state tracked values
        self.Model.add(keras.layers.Dense(20, input_shape=(1 * 1,), activation=self.ActivationStyle))
        # Hidden Layer
        self.Model.add(keras.layers.Dense(20, activation=self.ActivationStyle))
        # Hidden Layer
        self.Model.add(keras.layers.Dense(20, activation=self.ActivationStyle))
        # Output Layer
        self.Model.add(keras.layers.Dense(1))

        # Fixed/Variables ----------------------------------------------------------------------------------------------
        self.CurrentStep = 1

        # the history of rewards and actions
        self.StateHistory = []
        self.RewardHistory = []
        self.ActionHistory = []
        # history of action types, explore/eploit
        self.ActionTypeHistory = []
        self.RewardByAction = []

        # Index of last action taken by agent
        self.LastAction = -1

        try:
            if loadModelPath is not None:
                # load in an existing model
                self.Model.load_weights(loadModelPath)
                self.ModelFilePath = loadModelPath
                print('Loading existing model, {}'.format(self.ModelFilePath))
        except:
            print('Issue loading model, creating new model')

        # Dropout is meant to be dropping of nodes in the model that are redudant or when a high density is reached
        #self.Model.add(keras.layers.Dropout(0.0))

        # set the learning rate
        optimizer = keras.optimizers.Adam(lr=self.LearningRate)

        # ???
        metrics = ['accuracy']

        # Finally put model together for training
        self.Model.compile(optimizer, loss=self.LossFunction, metrics=metrics)

        # loading the environment pieces
        self.Server = server
        self.Client = client
        self.Network = network

    # Based on association with reward, pick action with highest reward predicted
    def TakeHighestValueAction(self):
        # Of all possible actions, predict reward for each, take highest
        highestReward = -1
        highestRewardActionIndex = -1

        for actionIndex in range(0, self.NumberOfActions):
            predictedReward = self.Model.predict([actionIndex])

            if self.Verbose:
                print('Predicted Reward {} for Action {}'.format(predictedReward, actionIndex))

            if predictedReward > highestReward:
                highestReward = predictedReward
                highestRewardActionIndex = actionIndex

        selectedAction = highestRewardActionIndex

        return selectedAction

    # Observe environment, based on epsilon either explore or exploit (seek highest reward)
    def Train(self, state, reward):

        # Fit action to reward, so that given an action we can see the potential impact
        trainingResult = self.Model.fit([self.LastAction], [reward], epochs=self.EpochCount, verbose=0)

        print('Training: Associate action {} with reward {}'.format(self.LastAction, reward[0]))

        # Save model out
        self.Model.save(self.ModelFilePath)

        # determine if agent will take random action, or if it will select the highest rewarding action

        # Explore or Exploit
        if random.randint(1,100) <= self.Epsilon:
            # Explore

            # Pick a random action
            selectedAction = random.randint(0,self.NumberOfActions-1)
            self.ActionTypeHistory.append(0)

        else:
            # Exploit
            selectedAction = self.TakeHighestValueAction()
            self.ActionTypeHistory.append(1)

        return selectedAction

    # take highest reward action
    def Test(self):
        return self.TakeHighestValueAction()

    # Observe environment, make action decision, do action
    def Act(self,clientLogJson, serverLogJson, networkLogJson):

        # observe environment
        state, reward = self.ObserveEnvironment(clientLogJson, serverLogJson, networkLogJson)

        if (state is not None or reward is not None):

            # train
            if self.Training:
                nextAction = self.Train(state,reward)
            else:
                nextAction = self.Test()

            self.CurrentStep += 1

            self.ActionHistory.append(self.LastAction)
            self.StateHistory.append(state)
            self.RewardHistory.append(reward)

            # take an action
            self.TakeAction(nextAction)

            self.LastAction = nextAction

    # EDITABLE - Observe environment and return the relevant environmental states/info
    def ObserveEnvironment(self, clientLogJson, serverLogJson, networkLogJson):

        # extract state
        state = []

        # calculate reward
        reward = [0]

        return state, reward

    # EDITABLE - Resolve the picked action to actual environment impact
    def TakeAction(self, actionIndex):
        pass

    # EDITABLE - Create a training report to pair with the model
    def log(self):
        pass

    # EDITABLE - Visualize/Graph/Human readable
    def report(self):
        pass
