from datetime import datetime as dt
from datetime import timedelta
import os
import io

import flask
import pandas as pd
from bokeh.embed import components
from bokeh.plotting import figure
from bokeh.palettes import Set2_5 as palette
from bokeh.models import Legend

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
    total_high = []
    for lake in lakes:
        df_lake = df[lake].dropna()
        total_high.append((df_lake > req_maxes[lake]).sum())
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
        req_maxes[lakes].tolist(),
        total_high
    )
    high_lakes = [lake.title() for lake, high in zip(lakes, is_high) if high]
    if not high_lakes:
        high_lakes = 'All lakes are below their state-required maximum.'
    elif len(high_lakes) == 1:
        high_lakes = f'{high_lakes[0]} is above its state-required maximum.'
    else:
        high_lakes = ', '.join(high_lakes[:-1]) + f', and {high_lakes[-1]}'
        high_lakes += ' are above their state-required maximums.'
    return flask.render_template('main.html', info=info, high_lakes=high_lakes)


@app.route('/db')
def database_dump():
    df = lldb.to_df()
    return flask.send_file(
        io.BytesIO(df.to_csv().encode('utf-8')),
        mimetype='text/csv',
        attachment_filename='madison_lake_levels.csv',
        as_attachment=True
    )


@app.route('/plot')
def plot():
    df = lldb.to_df()
    req_levels = mll.required_levels.required_levels

    p = figure(title="Madison Lake Levels",
               x_axis_label='date',
               x_axis_type='datetime',
               y_axis_label='Lake Height (feet above sea level)',
               tools="pan,wheel_zoom,box_zoom,reset,previewsave",
               sizing_mode='scale_width')
    p.plot_height = 400

    levels = []
    maxes = []
    for lake, color in zip(df.columns, palette):
        levels.append(p.line(df.index, df[lake], color=color, line_width=2,
                             muted_alpha=0.2, muted_color=color))
        maxes.append(p.line([df.index.min(), df.index.max()],
                            2 * [req_levels.loc[lake, 'summer_maximum']],
                            color=color,
                            line_width=2,
                            line_dash=[5, 5],
                            line_alpha=0.8,
                            muted_alpha=0.1,
                            muted_color=color))
    _msg = p.circle([], [], color='#ffffff')
    legend_items = [('Click to fade', [_msg])]
    for lake, level, _max in zip(df.columns, levels, maxes):
        lake = lake.title()
        legend_items.extend([(lake, [level]), (lake + ' max', [_max])])
    legend = Legend(items=legend_items, location=(0, 0))
    legend.click_policy = 'mute'
    p.add_layout(legend, 'left')

    script, div = components(p)
    return flask.render_template('plot.html', bokeh_script=script,
                                 plot_div=div)


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
