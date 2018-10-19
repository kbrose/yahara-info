from datetime import datetime, timedelta

import flask
import madison_lake_levels as mll

app = flask.Flask(__name__)

@app.route('/')
def main():
    ndays = 75
    df = mll.scrape.scrape(datetime.utcnow() - timedelta(days=ndays))
    df = df.sort_index()
    req_levels = mll.required_levels.required_levels
    req_maxes = req_levels['summer_maximum']
    lakes = ['mendota', 'monona', 'waubesa', 'kegonsa']
    is_high = []
    streaks = []
    for lake in lakes:
        df_lake = df[lake].dropna()
        is_high.append(df_lake.iloc[-1] > req_maxes[lake])
        below_level_times = df_lake[df_lake <= req_maxes[lake]].index
        above_level_times = df_lake[df_lake > req_maxes[lake]].index
        if is_high[-1]:
            if below_level_times.size:
                time_above = df_lake.index[-1] - below_level_times.max()
                streaks.append(time_above.days)
            else:
                streaks.append('at least {}'.format(ndays))
        else:
            if above_level_times.size:
                time_below = df_lake.index[-1] - above_level_times.max()
                streaks.append(time_below.days)
            else:
                streaks.append('at least {}'.format(ndays))
    info = zip(
        [lake.title() for lake in lakes],
        is_high,
        streaks,
        df[lakes].iloc[-1, :].tolist(),
        req_maxes[lakes].tolist()
    )
    return flask.render_template('main.html', info=info)


if __name__ == '__main__':
    app.run()
