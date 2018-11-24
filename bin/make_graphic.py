import sys
sys.path.append('..')

import os
from datetime import datetime, timedelta

import numpy as np
import matplotlib.pyplot as plt
import matplotlib

import madison_lake_levels as mll

def main():
    lldb = mll.db.LakeLevelDB(**mll.db.config_from_dburl(os.getenv('DATABASE_URL')))
    req = mll.required_levels.required_levels
    df = lldb.to_df()
    df = df[df.columns[::-1]]
    f, ax = plt.subplots(figsize=(9,2))
    for i, name in enumerate(df.columns):
        x = (df[name] > req.loc[name, 'summer_maximum']).astype(float)
        x[x == 0] = np.nan
        x *= i
        ax.plot(x, 'k.', label=name, lw=3)
    ax.set_yticks(range(df.shape[1]))
    ax.set_yticklabels(df.columns)
    ax.set_ylim([-1, df.shape[1]])
    ax.set_xticks([datetime(year, 1, 1) for year in range(2008, 2019)])
    ax.xaxis.grid()
    for child in ax.get_children():
        if isinstance(child, matplotlib.spines.Spine):
            child.set_color('#cccccc')
    ax.tick_params(axis=u'both', which=u'both',length=0)
    plt.savefig('../static/imgs/timeline.png')
    # plt.show()

if __name__ == '__main__':
    main()
