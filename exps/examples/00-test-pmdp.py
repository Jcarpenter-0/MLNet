import pandas as pd
import networks.mininet
import mdp

# Test the auto-build
mnNet = networks.mininet.SetupMiniNetNetwork(dict())

input('Hold here')

mnNet.Shutdown()


mdpList = list()

upperBound = 242.0
lowerBound = 241.0

lowPerf = mdp.State([lambda x: x['rttAvg'] >= upperBound or x['packetLoss'] > 0])
ambPerf = mdp.State([lambda x: x['rttAvg'] < upperBound and x['rttAvg'] > lowerBound])
higPerf = mdp.State([lambda x: x['rttAvg'] <= lowerBound or x['packetLoss'] == 0])

mdpList.append(lowPerf)
mdpList.append(ambPerf)
mdpList.append(higPerf)

dataDF = pd.read_csv('exps/0X_ping_example/tmp/Traces/07-12-2020-13-47-11-trn-1-session-log.csv')

_, dataDF['state-id'] = mdp.AnalyzeTrace(dataDF, mdpList)

print(dataDF.head())

dataDF.to_csv('./tmp-mdp.csv')

print('Done')
