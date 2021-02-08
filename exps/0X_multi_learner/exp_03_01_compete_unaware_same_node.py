# Simple CC experiment, involving two nodes
import numpy as np
import glob
import random
import math

# Setup the dir
DirOffset = '../../'

import os
import sys
sys.path.insert(0, os.getcwd())
sys.path.insert(0, DirOffset)
import networks.mahimahi
import networks
import exps

# Have a fixed environment, and see how the nodes behave when running together, apart, and similar for training

# Experiment Parameters
TestRepetitions = 10
ExperimentRunTime = 1900
IperfRunCount = 1000
IperfRunLength = 10
VerificationPatternFiles = ['./bbr-pattern.csv', './cubic-pattern.csv', './reno-pattern.csv', './vegas-pattern.csv']

# Setup Environment
mmEnv = networks.mahimahi.MahiMahiDelayShell(50)

# Do the meta calculations
NumberOfTests = 3 + (TestRepetitions * 2) + (TestRepetitions * 4) + (2 * (TestRepetitions * len(VerificationPatternFiles)))
TotalTimeInSeconds = NumberOfTests * ExperimentRunTime

print('Tests planned {} - Time ~{} hours'.format(NumberOfTests, TotalTimeInSeconds/60/60))
input("Press Enter to continue... or ctrl-c to stop")


def TrainTogether():

    # Train Together
    ccLearnerTogether1 = exps.common.Learner(
        '{}learners/congestion_control_manager/congestion_control_manager.py'.format(DirOffset)
        , traceFilePostFix=mmEnv.GetParaString() + '_trn'
        , learnerDir='./tmp/learnertogether-1/')

    ccLearnerTogether2 = exps.common.Learner(
        '{}learners/congestion_control_manager/congestion_control_manager.py'.format(DirOffset)
        , traceFilePostFix=mmEnv.GetParaString() + '_trn'
        , learnerDir='./tmp/learnertogether-2/'
        , learnerPort=8081)

    # Define network nodes
    iperfClientNode = networks.common.SetupLocalHost(dirOffset=DirOffset)

    iperfServerNode = networks.mahimahi.SetupMahiMahiNode([mmEnv], dirOffset=DirOffset)

    iperfClientNode.AddApplication(
        ['python3', '{}applications/Iperf/02_cc_manager/iperf_stub.py'.format(DirOffset)
            , '-c', '{}'.format(iperfServerNode.IpAddress), '-t', '{}'.format(IperfRunLength),
         '{}'.format(IperfRunCount), 'http://localhost:{}'.format(ccLearnerTogether1.LearnerPort)])

    iperfServerNode.AddApplication(['iperf3', '-s'])

    iperfClientNode.AddApplication(
        ['python3', '{}applications/Iperf/02_cc_manager/iperf_stub.py'.format(DirOffset)
            , '-c', '{}'.format(iperfServerNode.IpAddress), '-p', '5202', '-t', '{}'.format(IperfRunLength),
         '{}'.format(IperfRunCount), 'http://localhost:{}'.format(ccLearnerTogether2.LearnerPort)])

    iperfServerNode.AddApplication(['iperf3', '-s', '-p', '5202'])

    # run experiment
    exps.common.runExperimentUsingFramework([iperfServerNode, iperfClientNode]
                                            , [ccLearnerTogether1, ccLearnerTogether2]
                                            , ExperimentRunTime, learnerServerCooldown=30)


def TrainAlone():
    # ========= Train Alone
    ccLearnerAlone1 = exps.common.Learner(
        '{}learners/congestion_control_manager/congestion_control_manager.py'.format(DirOffset)
        , traceFilePostFix=mmEnv.GetParaString() + '_trn'
        , learnerDir='./tmp/learnerAlone-1/')

    ccLearnerAlone2 = exps.common.Learner(
        '{}learners/congestion_control_manager/congestion_control_manager.py'.format(DirOffset)
        , traceFilePostFix=mmEnv.GetParaString() + '_trn'
        , learnerDir='./tmp/learnerAlone-2/')


    learners = [ccLearnerAlone1, ccLearnerAlone2]

    for learner in learners:

        iperfClientNode = networks.common.SetupLocalHost(dirOffset=DirOffset)

        iperfServerNode = networks.mahimahi.SetupMahiMahiNode([mmEnv], dirOffset=DirOffset)

        iperfClientNode.AddApplication(
            ['python3', '{}applications/Iperf/02_cc_manager/iperf_stub.py'.format(DirOffset)
                , '-c', '{}'.format(iperfServerNode.IpAddress), '-t', '{}'.format(IperfRunLength),
             '{}'.format(IperfRunCount), 'http://localhost:{}'.format(learner.LearnerPort)])

        iperfServerNode.AddApplication(['iperf3', '-s'])

        # run experiment
        exps.common.runExperimentUsingFramework([iperfServerNode, iperfClientNode]
                                                , [learner]
                                                , ExperimentRunTime, learnerServerCooldown=30)


def TestTogether():

    # Do the testing for trained together
    for testNum in range(0, TestRepetitions):

        ccLearnerTogether1 = exps.common.Learner(
            '{}learners/congestion_control_manager/congestion_control_manager.py'.format(DirOffset)
            , training=0
            , traceFilePostFix=mmEnv.GetParaString() + '_tst_tgr'
            , learnerDir='./tmp/learnertogether-1/')

        ccLearnerTogether2 = exps.common.Learner(
            '{}learners/congestion_control_manager/congestion_control_manager.py'.format(DirOffset)
            , training=0
            , traceFilePostFix=mmEnv.GetParaString() + '_tst_tgr'
            , learnerDir='./tmp/learnertogether-2/'
            , learnerPort=8081)

        iperfClientNode = networks.common.SetupLocalHost(dirOffset=DirOffset)

        iperfServerNode = networks.mahimahi.SetupMahiMahiNode([mmEnv], dirOffset=DirOffset)


        iperfServerNode.AddApplication(['iperf3', '-s'])
        iperfServerNode.AddApplication(['iperf3', '-s', '-p', '5202'])

        iperfClientNode.AddApplication(
            ['python3',
             '{}applications/Iperf/02_cc_manager/iperf_stub.py'.format(DirOffset)
                , '-c', '{}'.format(iperfServerNode.IpAddress), '-t', '{}'.format(IperfRunLength),
             '{}'.format(IperfRunCount), 'http://localhost:{}'.format(ccLearnerTogether1.LearnerPort)])

        iperfClientNode.AddApplication(
            ['python3', '{}applications/Iperf/02_cc_manager/iperf_stub.py'.format(DirOffset)
                , '-c', '{}'.format(iperfServerNode.IpAddress), '-p', '5202', '-t', '{}'.format(IperfRunLength),
             '{}'.format(IperfRunCount), 'http://localhost:{}'.format(ccLearnerTogether2.LearnerPort)])

        # run experiment
        exps.common.runExperimentUsingFramework([iperfServerNode, iperfClientNode]
                                                , [ccLearnerTogether1, ccLearnerTogether2]
                                                , ExperimentRunTime, learnerServerCooldown=30)


    # Do the testing for trained alone
    for testNum in range(0, TestRepetitions):
        ccLearnerAlone1 = exps.common.Learner(
            '{}learners/congestion_control_manager/congestion_control_manager.py'.format(DirOffset)
            , training=0
            , traceFilePostFix=mmEnv.GetParaString() + '_tst_tgr'
            , learnerDir='./tmp/learnerAlone-1/')

        ccLearnerAlone2 = exps.common.Learner(
            '{}learners/congestion_control_manager/congestion_control_manager.py'.format(DirOffset)
            , training=0
            , traceFilePostFix=mmEnv.GetParaString() + '_tst_tgr'
            , learnerDir='./tmp/learnerAlone-2/'
            , learnerPort=8081)

        iperfClientNode = networks.common.SetupLocalHost(dirOffset=DirOffset)

        iperfServerNode = networks.mahimahi.SetupMahiMahiNode([mmEnv], dirOffset=DirOffset)

        iperfServerNode.AddApplication(['iperf3', '-s'])
        iperfServerNode.AddApplication(['iperf3', '-s', '-p', '5202'])

        iperfClientNode.AddApplication(
            ['python3',
             '{}applications/Iperf/02_cc_manager/iperf_stub.py'.format(DirOffset)
                , '-c', '{}'.format(iperfServerNode.IpAddress), '-t', '{}'.format(IperfRunLength),
             '{}'.format(IperfRunCount), 'http://localhost:{}'.format(ccLearnerAlone1.LearnerPort)])

        iperfClientNode.AddApplication(
            ['python3', '{}applications/Iperf/02_cc_manager/iperf_stub.py'.format(DirOffset)
                , '-c', '{}'.format(iperfServerNode.IpAddress), '-p', '5202', '-t', '{}'.format(IperfRunLength),
             '{}'.format(IperfRunCount), 'http://localhost:{}'.format(ccLearnerAlone2.LearnerPort)])

        # run experiment
        exps.common.runExperimentUsingFramework([iperfServerNode, iperfClientNode]
                                                , [ccLearnerAlone1, ccLearnerAlone2]
                                                , ExperimentRunTime, learnerServerCooldown=30)

    # Do verify together
    for verifyPattern in VerificationPatternFiles:

        for testNum in range(0, TestRepetitions):
            verifyLearner1 = exps.common.Learner(
                '{}learners/congestion_control_manager/congestion_control_manager.py'.format(DirOffset)
                , training=2
                , traceFilePostFix=mmEnv.GetParaString() + '_tst_tgr'
                , learnerDir='./tmp/verifyLearner-1/'
                , miscArgs=[verifyPattern])

            verifyLearner2 = exps.common.Learner(
                '{}learners/congestion_control_manager/congestion_control_manager.py'.format(DirOffset)
                , training=2
                , traceFilePostFix=mmEnv.GetParaString() + '_tst_tgr'
                , learnerDir='./tmp/verifyLearner-2/'
                , miscArgs=[verifyPattern]
                , learnerPort=8081)

            iperfClientNode = networks.common.SetupLocalHost(dirOffset=DirOffset)

            iperfServerNode = networks.mahimahi.SetupMahiMahiNode([mmEnv], dirOffset=DirOffset)

            iperfClientNode.AddApplication(
                ['python3',
                 '{}applications/Iperf/02_cc_manager/iperf_stub.py'.format(DirOffset)
                    , '-c', '{}'.format(iperfServerNode.IpAddress), '-t', '{}'.format(IperfRunLength),
                 '{}'.format(IperfRunCount), 'http://localhost:{}'.format(verifyLearner1.LearnerPort)])

            iperfServerNode.AddApplication(['iperf3', '-s'])

            iperfClientNode.AddApplication(
                ['python3',
                 '{}applications/Iperf/02_cc_manager/iperf_stub.py'.format(DirOffset)
                    , '-c', '{}'.format(iperfServerNode.IpAddress), '-p', '5202', '-t', '{}'.format(IperfRunLength),
                 '{}'.format(IperfRunCount), 'http://localhost:{}'.format(verifyLearner2.LearnerPort)])

            iperfServerNode.AddApplication(['iperf3', '-s', '-p', '5202'])

            # run experiment
            exps.common.runExperimentUsingFramework([iperfServerNode, iperfClientNode]
                                                    , [verifyLearner1, verifyLearner2]
                                                    , ExperimentRunTime, learnerServerCooldown=30)


def TestAlone():

    # Do the testing
    for testNum in range(0, TestRepetitions):

        ccLearnerTogether1 = exps.common.Learner(
            '{}learners/congestion_control_manager/congestion_control_manager.py'.format(DirOffset)
            , training=0
            , traceFilePostFix=mmEnv.GetParaString() + '_tst_tgr'
            , learnerDir='./tmp/learnertogether-1/')

        ccLearnerTogether2 = exps.common.Learner(
            '{}learners/congestion_control_manager/congestion_control_manager.py'.format(DirOffset)
            , training=0
            , traceFilePostFix=mmEnv.GetParaString() + '_tst_tgr'
            , learnerDir='./tmp/learnertogether-2/')

        ccLearnerAlone1 = exps.common.Learner(
            '{}learners/congestion_control_manager/congestion_control_manager.py'.format(DirOffset)
            , training=0
            , traceFilePostFix=mmEnv.GetParaString() + '_tst_tgr'
            , learnerDir='./tmp/learnerAlone-1/')

        ccLearnerAlone2 = exps.common.Learner(
            '{}learners/congestion_control_manager/congestion_control_manager.py'.format(DirOffset)
            , training=0
            , traceFilePostFix=mmEnv.GetParaString() + '_tst_tgr'
            , learnerDir='./tmp/learnerAlone-2/')

        learners = [ccLearnerTogether1, ccLearnerTogether2, ccLearnerAlone1, ccLearnerAlone2]

        for learner in learners:
            iperfClientNode = networks.common.SetupLocalHost(dirOffset=DirOffset)

            iperfServerNode = networks.mahimahi.SetupMahiMahiNode([mmEnv], dirOffset=DirOffset)

            iperfClientNode.AddApplication(
                ['python3',
                 '{}applications/Iperf/02_cc_manager/iperf_stub.py'.format(DirOffset)
                    , '-c', '{}'.format(iperfServerNode.IpAddress), '-t', '{}'.format(IperfRunLength),
                 '{}'.format(IperfRunCount), 'http://localhost:{}'.format(learner.LearnerPort)])

            iperfServerNode.AddApplication(['iperf3', '-s'])

            # run experiment
            exps.common.runExperimentUsingFramework([iperfServerNode, iperfClientNode]
                                                    , [learner]
                                                    , ExperimentRunTime, learnerServerCooldown=30)


    # Do verify alone
    for verifyPattern in VerificationPatternFiles:

        for testNum in range(0, TestRepetitions):

            verifyLearner1 = exps.common.Learner(
                '{}learners/congestion_control_manager/congestion_control_manager.py'.format(DirOffset)
                , training=2
                , traceFilePostFix=mmEnv.GetParaString() + '_tst_tgr'
                , learnerDir='./tmp/verifyLearner-1/'
                , miscArgs=[verifyPattern])


            iperfClientNode = networks.common.SetupLocalHost(dirOffset=DirOffset)

            iperfServerNode = networks.mahimahi.SetupMahiMahiNode([mmEnv], dirOffset=DirOffset)

            iperfClientNode.AddApplication(
                ['python3',
                 '{}applications/Iperf/02_cc_manager/iperf_stub.py'.format(DirOffset)
                    , '-c', '{}'.format(iperfServerNode.IpAddress), '-t', '{}'.format(IperfRunLength),
                 '{}'.format(IperfRunCount), 'http://localhost:{}'.format(verifyLearner1.LearnerPort)])

            iperfServerNode.AddApplication(['iperf3', '-s'])

            exps.common.runExperimentUsingFramework([iperfServerNode, iperfClientNode]
                                                    , [verifyLearner1]
                                                    , ExperimentRunTime, learnerServerCooldown=30)


TrainTogether()
TrainAlone()
TestTogether()
TestAlone()

print('Experiment Done')
