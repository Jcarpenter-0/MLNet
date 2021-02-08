# Simple Ping experiment to show abilities of learner and platform

# Setup the dir
DirOffset = '../../'

import os
import sys
sys.path.insert(0, os.getcwd())
sys.path.insert(0, DirOffset)
import exps
import networks.mahimahi
import networks
import apps
import apps.Ping
import learners

TrainingCount = 4

MahMahiNetworkDelay = 120
PingInterval = .2
PingAmount = 10
# Number of times the learner will decide a ping action
PingRuns = 100
PingPath = '../../apps/Ping.py'
InitialPingArgs = ['~dest', '100.64.0.1', '-c', PingAmount, '-s', '56', '-t', '255', '-i', PingInterval]
TestDuration = ((PingInterval + (MahMahiNetworkDelay/1000)) * PingAmount) * PingRuns

# Do the meta calculations
NumberOfTests = 3 + TrainingCount
TotalTimeInSeconds = NumberOfTests * TestDuration

print('Tests planned {} - Time ~{} hours'.format(NumberOfTests, TotalTimeInSeconds/60/60))
input("Press Enter to continue... or ctrl-c to stop")

# Do training
for trainCount in range(0, TrainingCount):
    # Define Learners
    print('Training count {}'.format(trainCount))

    pingManager = learners.Learner('../../learners/example_ping_manager/ping_manager.py'
                                      , traceFilePostFix='trn-{}'.format(trainCount))

    # Define network nodes
    pingNode = networks.mahimahi.SetupMahiMahiNode([networks.mahimahi.MahiMahiDelayShell(delayMS=MahMahiNetworkDelay)]
                                                   , dirOffset=DirOffset)

    pingNode.AddApplication(apps.PrepWrapperCall(PingPath
                                                        , InitialPingArgs
                                                        , PingRuns
                                                        , 'http://100.64.0.1:{}'.format(pingManager.LearnerPort)))


    # run experiment - training
    exps.runExperimentUsingFramework([pingNode], TestDuration)

print('Doing Learner Testing')

# run experiment - testing
pingManager = learners.Learner('../../learners/example_ping_manager/ping_manager.py'
                                  , training=0
                                  , traceFilePostFix='tst')

pingNode = networks.mahimahi.SetupMahiMahiNode([networks.mahimahi.MahiMahiDelayShell(delayMS=MahMahiNetworkDelay)]
                                               , dirOffset=DirOffset)

pingNode.AddApplication(apps.PrepWrapperCall(PingPath
                                                    , InitialPingArgs
                                                    , PingRuns
                                                    , 'http://100.64.0.1:{}'.format(pingManager.LearnerPort)))

exps.runExperimentUsingFramework([pingNode], TestDuration)

print('Doing Verification')

# run the verification exps
pingManagerVerificationLowEnd = learners.Learner('../../learners/example_ping_manager/ping_manager.py'
                                                    , training=2
                                                    , miscArgs=['./pattern-0.csv']
                                                    , traceFilePostFix='lowEnd')

pingManagerVerificationHighEnd = learners.Learner('../../learners/example_ping_manager/ping_manager.py'
                                                     , training=2
                                                     , miscArgs=['./pattern-1.csv']
                                                     , traceFilePostFix='highEnd')

verifications = [pingManagerVerificationLowEnd, pingManagerVerificationHighEnd]

for verifier in verifications:
    # Define network nodes
    pingNode = networks.mahimahi.SetupMahiMahiNode([networks.mahimahi.MahiMahiDelayShell(delayMS=MahMahiNetworkDelay)],
                                                   dirOffset=DirOffset)

    pingNode.AddApplication(apps.PrepWrapperCall(PingPath
                                                        , InitialPingArgs
                                                        , PingRuns
                                                        , 'http://100.64.0.1:{}'.format(pingManager.LearnerPort)))

    # run experiment
    exps.runExperimentUsingFramework([pingNode], TestDuration)
