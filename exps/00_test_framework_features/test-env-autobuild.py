import exps
import exps.auto
import agents

learner = agents.AgentWrapper('{}./agents/tcp-flavor-selection/tcp-flavor-selection-constrained.py'.format('./'))

networkModule = exps.auto.autoBuildEnv(learner, soughtMetrics=['throughput'], networkArgs={'hop count':3,'topology':'linear'}, tags=[''], dirOffset='./')

exps.runExperimentUsingFramework(networkModule, 45)

print('done')