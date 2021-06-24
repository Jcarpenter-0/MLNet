import pandas as pd
import numpy as np
import glob
import matplotlib.pyplot as plt

perfLogs = glob.glob('./tmp/*/learner/Traces/*.csv')

combinedDF = pd.DataFrame()

colorStrata = []
lineStrata = []
actorNames = []

for perfLog in perfLogs:

    # actor data
    perfDF = pd.read_csv(perfLog)

    # actor name
    actorName = perfLog.split('/')[-4]
    actorNames.append(actorName)

    if 'actor' in actorName:
        colorStrata.append('blue')
        lineStrata.append('--')
    else:
        colorStrata.append('red')
        lineStrata.append('--')

    combinedDF[actorName + '-' + 'Reward'] = perfDF['Reward']
    combinedDF[actorName + '-' + 'Sender-Bps'] = perfDF['sender-bps']
    combinedDF[actorName + '-' + 'Mean-RTT'] = perfDF['meanRTT']
    combinedDF[actorName + '-' + 'Sender-Retransmits'] = perfDF['sender-retransmits']


# Graph 1, each actor's performance as Reward
graph1DF = pd.DataFrame()

for actorName in actorNames:
    graph1DF[actorName + '-' + 'Reward'] = combinedDF[actorName + '-' + 'Reward']

ax = graph1DF.plot(style=lineStrata, color=colorStrata, title='Multi-Agent', figsize=(25, 11))
ax.set_ylabel('Reward')
ax.set_xlabel('Number of Actions (10s)')

plt.yticks(np.arange(12, 34, step=2))
plt.xticks(np.arange(0.0, 370, step=30))
plt.savefig('./tmp/multi-learner-reward.png')
plt.close()

# Graph 2, each actor's performance as Bps
graph1DF = pd.DataFrame()

for actorName in actorNames:
    graph1DF[actorName + '-' + 'Sender-Bps'] = combinedDF[actorName + '-' + 'Sender-Bps']

ax = graph1DF.plot(style=lineStrata, color=colorStrata, title='Multi-Agent', figsize=(25, 11))
ax.set_ylabel('Bps')
ax.set_xlabel('Number of Actions (10s)')

#plt.yticks(np.arange(12, 34, step=2))
plt.xticks(np.arange(0.0, 370, step=30))
plt.savefig('./tmp/multi-learner-bps.png')
plt.close()

# Graph 3, each actor's performance
graph3DF = pd.DataFrame()

for actorName in actorNames:
    graph3DF[actorName + '-' + 'Mean-RTT'] = combinedDF[actorName + '-' + 'Mean-RTT']

ax = graph3DF.plot(style=lineStrata, color=colorStrata, title='Multi-Agent', figsize=(25, 11))
ax.set_ylabel('RTT')
ax.set_xlabel('Number of Actions (10s)')

#plt.yticks(np.arange(12, 34, step=2))
plt.xticks(np.arange(0.0, 370, step=30))
plt.savefig('./tmp/multi-learner-rtt.png')
plt.close()

# Graph 4, each actor's performance
graph4DF = pd.DataFrame()

for actorName in actorNames:
    graph4DF[actorName + '-' + 'Sender-Retransmits'] = combinedDF[actorName + '-' + 'Sender-Retransmits']

ax = graph4DF.plot(style=lineStrata, color=colorStrata, title='Multi-Agent', figsize=(25, 11))
ax.set_ylabel('Retransmits')
ax.set_xlabel('Number of Actions (10s)')

#plt.yticks(np.arange(12, 34, step=2))
plt.xticks(np.arange(0.0, 370, step=30))
plt.savefig('./tmp/multi-learner-retransmits.png')
plt.close()
