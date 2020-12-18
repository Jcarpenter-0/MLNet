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


if __name__ == '__main__':

    testState = State([lambda a: a['metric1'] == 'val' and a['metric2'] == 'val2'])

    foundState, idx = AnalyzeObservation({'metric1':'val', 'metric2':'val2'}, [testState])

    observationTrace = pandas.DataFrame(columns=['metric1', 'metric2'], data=[['val', 'val2']])

    foundStates, observationTrace['state-id'] = AnalyzeTrace(observationTrace, [testState])

    print('')

