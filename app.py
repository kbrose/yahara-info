from datetime import datetime as dt
from datetime import timedelta
import os
import io

import flask
import pandas as pd
import pytz

import madison_lake_levels as mll

app = flask.Flask(__name__)

lldb = mll.db.LakeLevelDB(
    **mll.db.config_from_dburl(os.getenv('DATABASE_URL'))
)

@app.route('/')
def main():
    df = lldb.to_df()
    if not df.size:
        return flask.render_template('main.html', info=[])
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
                streaks.append('a good number of')
        else:
            if above_level_times.size:
                time_below = df_lake.index[-1] - above_level_times.max()
                streaks.append(time_below.days)
            else:
                streaks.append('a good number of')
    info = zip(
        [lake.title() for lake in lakes],
        is_high,
        streaks,
        df[lakes].iloc[-1, :].tolist(),
        req_maxes[lakes].tolist()
    )
    return flask.render_template('main.html', info=info)


@app.route('/db')
def database_dump():
    df = lldb.to_df()
    return flask.send_file(
        io.BytesIO(df.to_csv().encode('utf-8')),
        mimetype='text/csv',
        attachment_filename='madison_lake_levels.csv',
        as_attachment=True
    )


@app.route('/update/', defaults={'start': None, 'end': None},
           methods=['GET', 'POST'])
@app.route('/update/<start>/<end>', methods=['GET', 'POST'])
def update_db(start, end):
    if start is None:
        try:
            start_dt = lldb.most_recent().index[0].to_pydatetime()
        except IndexError:
            start_dt = dt.utcnow() - timedelta(days=1)
    else:
        start_dt = pd.to_datetime(start, utc=True).to_pydatetime()

    if end is None:
        end_dt = dt.utcnow()
    else:
        end_dt = pd.to_datetime(end, utc=True).to_pydatetime()

    mll.scrape.backfill(start_dt, end_dt, lldb, True)
    return flask.redirect('/')


if __name__ == '__main__':
    app.run()
