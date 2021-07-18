import pandas
import numpy

# https://ai.stackexchange.com/questions/5051/rl-agents-view-of-state-transitions
# https://ai.stackexchange.com/questions/7763/how-to-define-states-in-reinforcement-learning


class State(object):

    def __init__(self, metricRules:list, actions:list=None):
        """"""

        # List of rules that define this state
        # patterned as a list of functions (predicates/rules) can also be lambdas
        self.MetricRules:list = metricRules

        # List of actions
        self.Actions:list = actions

    def IsState(self, metrics:dict) -> bool:
        """Check metrics against state rules to see if they indeed fall into this state"""

        for rule in self.MetricRules:
            if rule(metrics):
                return True

        return False

    def AdjustMetrics(self, metrics:dict) -> dict:
        """Cluster the values"""
        return metrics


def AnalyzeTrace(trace:pandas.DataFrame, possibleStates:list):
    """process traces into MDP states"""

    states = []
    stateIDs = []

    for idx, row in trace.iterrows():
        rowDict = dict()

        for col in row.keys():
            rowDict[col] = row[col]

        state, id = AnalyzeObservation(rowDict, possibleStates)

        states.append(state)
        stateIDs.append(id)

    return states, stateIDs


def AnalyzeObservation(observation:dict, possibleStates:list):
    """process metrics into MDP states"""

    for idx, state in enumerate(possibleStates):

        if state.IsState(observation):
            return state, idx


import apps.framework_DMF


class PartialMDPModule(apps.framework_DMF.AdaptationModule):

    def __init__(self, mdp:list, desiredObservationMetrics:list, logPath:str=None, logFileName:str=None, actionSpace:list=None, actionFields:dict=None):
        """Partial-defined Markovian Decision Process system"""
        super().__init__(desiredObservationMetrics=desiredObservationMetrics, logPath=logPath, logFileName=logFileName, actionSpace=actionSpace, actionFields=actionFields)
        self.MDP = mdp

    def DefineActionSpaceSubset(self, rawObservation:dict, observation:dict) -> list:
        """Action space is defined by what state the system is currently in"""

        # Get current State
        currentState, _ = AnalyzeObservation(rawObservation, self.MDP)

        return currentState.Actions.copy()

    def DefineObservation(self, rawObservation:dict) -> list:
        """Observation is provided by the MDP that defines the states"""

        # Get current State based on metrics
        currentState, id = AnalyzeObservation(rawObservation, self.MDP)

        rawObservation['StateID'] = id

        # Add to the observation, state id
        newObv = super().DefineObservation(rawObservation)

        newObv = currentState.AdjustMetrics(newObv)

        return newObv