import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# https://pandas.pydata.org/pandas-docs/stable/user_guide/visualization.html
# https://jakevdp.github.io/PythonDataScienceHandbook/04.01-simple-line-plots.html

plt.style.use('seaborn-whitegrid')

df2 = pd.read_csv('./data/reward-only-groups-trunc.csv')

# MLNet, Pantheon, Park
colors = ['brown', 'green', 'orange']

ax = df2.plot(style=['--','--','--'], color=colors)

plt.yticks(np.arange(6, 18, step=2))
plt.xticks(np.arange(0.0, 40000, step=5000))
plt.show()
