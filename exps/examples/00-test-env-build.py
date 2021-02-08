import exps
import exps.auto
import learners

learner = learners.Learner('{}./learners/congestion_control_manager/congestion_control_manager.py'.format('./'))

networkModule = exps.auto.autoBuildEnv(learner, soughtMetrics=['throughput'], networkArgs={'hop count':3,'topology':'linear'}, tags=[''], dirOffset='./')

exps.runExperimentUsingFramework(networkModule, 45)

print('done')