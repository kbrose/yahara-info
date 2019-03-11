import sys
sys.path.append('..')

import os

import madison_lake_levels as mll

def main():
    lldb = mll.db.LakeLevelDB(**mll.db.config_from_dburl(os.getenv('DATABASE_URL')))
    req = mll.required_levels.required_levels
    df = lldb.to_df()
    df = df.loc[df.index < '2019']
    df = df.loc[df.index >= '2008-01-01']
    is_summer = (df.index.month >= 3) & (df.index.month < 11)
    df_summer = df.loc[is_summer, :]
    df_winter = df.loc[~is_summer, :]
    print('Start of data: {}'.format(df.index.min()))
    print('End of data  : {}'.format(df.index.max()))
    total_days = df.shape[0]
    summer_days = df_summer.shape[0]
    winter_days = df_winter.shape[0]
    print('Number of days in data: {}'.format(total_days))
    print('Number of Summer days: {}'.format(summer_days))
    print('Number of Winter days: {}'.format(winter_days))
    for lake in df.columns:
        print(f'For {lake}:')
        exceedances = (df[lake] > req.loc[lake, 'summer_maximum']).sum()
        summer_exceedances = (df_summer[lake] > req.loc[lake, 'summer_maximum']).sum()
        winter_exceedances = (df_winter[lake] > req.loc[lake, 'summer_maximum']).sum()
        print('  Total summer days over: {}'.format(summer_exceedances))
        print('                  as a %: {}'.format(100 * summer_exceedances / summer_days))
        print('  Total winter days over: {}'.format(winter_exceedances))
        print('                  as a %: {}'.format(100 * winter_exceedances / winter_days))
        print('  Total days over: {}'.format(exceedances))
        print('           as a %: {}'.format(100 * exceedances / df.shape[0]))
        summer_mins = (df_summer[lake] < req.loc[lake, 'summer_minimum']).sum()
        winter_mins = (df_winter[lake] < req.loc[lake, 'winter_minimum']).sum()
        mins = summer_mins + winter_mins
        print('  Total summer days below: {}'.format(summer_mins))
        print('                   as a %: {}'.format(100 * summer_mins / summer_days))
        print('  Total winter days below: {}'.format(winter_mins))
        print('                   as a %: {}'.format(100 * winter_mins / winter_days))
        print('  Total days below: {}'.format(mins))
        print('            as a %: {}'.format(100 * mins / total_days))

if __name__ == '__main__':
    main()
