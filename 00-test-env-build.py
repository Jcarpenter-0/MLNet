import exps
import exps.auto
import learners.common

learner = learners.common.Learner('{}./learners/congestion_control_manager/congestion_control_manager.py'.format('./'))

networkModule = exps.auto.autoBuildEnv(learner, soughtMetrics=['throughput'], networkArgs={'hop count':3,'topology':'linear'}, dirOffset='./')

exps.runExperimentUsingFramework(networkModule, [learner], 45)

print('done')