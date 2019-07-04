from datetime import datetime as dt
from datetime import timedelta
import os
import io

import flask
import pandas as pd
from bokeh.embed import components
from bokeh.plotting import figure
from bokeh.palettes import Set2_5 as palette
from bokeh.models import Legend, HoverTool
from bokeh.models.widgets import Panel, Tabs
from bokeh.models import DatetimeTickFormatter

import madison_lake_levels as mll

app = flask.Flask(__name__)

lldb = mll.db.LakeLevelDB(
    **mll.db.config_from_dburl(os.getenv('DATABASE_URL'))
)


def _main_page(df, date=''):
    df = df.sort_index()
    req_levels = mll.required_levels.required_levels
    req_maxes = req_levels['summer_maximum']
    lakes = ['mendota', 'monona', 'waubesa', 'kegonsa']
    is_high = []
    heights = []
    for lake in lakes:
        df_lake = df[lake].dropna()
        if not df_lake.size:
            return flask.render_template(
                'main.html',
                info=[],
                high_lakes='No data available at this time.',
                date=date
            )
        heights.append(df_lake.iloc[-1])
        is_high.append(df_lake.iloc[-1] > req_maxes[lake])
    total_diff = abs(pd.Series(dict(zip(lakes, heights))) - req_maxes[lakes])
    feet_diff = total_diff.astype(int)
    inches_diff = (total_diff - feet_diff) * 12
    info = zip(
        [lake.title() for lake in lakes],
        is_high,
        feet_diff.tolist(),
        inches_diff.tolist(),
    )
    high_lakes = [lake.title() for lake, high in zip(lakes, is_high) if high]
    if len(high_lakes) == 1:
        verb = 'is' if date == '' else 'was'
    else:
        verb = 'are' if date == '' else 'were'

    if not high_lakes:
        msg = f'All lakes {verb} below their state-required maximum.'
    elif len(high_lakes) == 1:
        msg = f'{high_lakes[0]} {verb} above its state-required maximum.'
    else:
        msg = ', '.join(high_lakes[:-1]) + f', and {high_lakes[-1]}'
        msg += f' {verb} above their state-required maximums.'
    return flask.render_template(
        'main.html', info=info, high_lakes=msg, date=date
    )


@app.route('/favicon.png')
def favicon():
    return flask.redirect(flask.url_for('static', filename='favicon.png'))


@app.route('/')
def main():
    df = lldb.to_df()
    return _main_page(df)


@app.route('/date/<date>')
def specific_date(date):
    df = lldb.to_df()
    date = pd.to_datetime(date)
    df = df[df.index <= date]
    return _main_page(
        df, date=f'<h5>Status on {date.strftime(r"%b %d, %Y")}</h5>'
    )


@app.route('/db')
def database_dump():
    df = lldb.to_df()
    return flask.send_file(
        io.BytesIO(df.to_csv().encode('utf-8')),
        mimetype='text/csv',
        attachment_filename='madison_lake_levels.csv',
        as_attachment=True
    )

@app.route('/plot-year')
def plot_mobile():
    df = lldb.to_df()
    req_levels = mll.required_levels.required_levels
    height = 550
    tabs = []

    for lake, color in zip(df.columns, palette):
        p = figure(title=lake.title(),
                x_axis_label='date',
                x_axis_type='datetime',
                y_axis_label='Lake Height (feet above sea level)',
                tools=[],
                height=height,
                sizing_mode='stretch_width')
        p.toolbar.logo = None

        curr_year = df.index.year.max()
        df = df[df.index.year >= curr_year - 8]
        gb = df.copy().groupby(df.index.year)
        curr_year_df = gb.get_group(curr_year)
        curr_day_of_year = curr_year_df.index.dayofyear.max()
        curr_day_of_year = min(curr_day_of_year, 365) # leap years don't exist
        first_day_of_year = curr_year_df.index[0]
        max_line = p.line([curr_year_df.index.min(), curr_year_df.index.max()],
                          2 * [req_levels.loc[lake, 'summer_maximum']],
                          color='#000000',
                          line_width=2,
                          line_dash=[5, 5],
                          line_alpha=0.5)
        for year, idx in gb.groups.items():
            year_df = df.loc[idx].copy()
            year_df = year_df[year_df.index.dayofyear <= curr_day_of_year]
            year_df.index = year_df.index.shift(
                1, first_day_of_year - year_df.index[0]
            )
            l = p.line(year_df.index, year_df[lake], color=color, line_width=2,
                       line_alpha=1 if year == curr_year else 0.3)
            if year == curr_year:
                this_year_line = l
            else:
                other_year_line = l
        p.xaxis.formatter = DatetimeTickFormatter(
            days = ['%b %d'],
            months = ['%b'],
            years = ['%b'],
        )
        legend = Legend(
            items=[
                ('This year', [this_year_line]),
                ('Past 8 years', [other_year_line]),
                ('State max', [max_line])
            ],
            location=(0, 0)
        )
        p.add_layout(legend, 'below')
        p.legend.orientation = "vertical"
        tabs.append(Panel(child=p, title=lake.title()))

    script, div = components(Tabs(tabs=tabs))
    return flask.render_template('plot.html', bokeh_script=script,
                                 plot_div=div)


@app.route('/plot-timeline')
def plot():
    df = lldb.to_df()
    req_levels = mll.required_levels.required_levels

    height = 700

    hover = HoverTool(
        names=[lake.title() for lake in df],
        tooltips=[('lake', '$name'), ('date', '$x{%F}'),
                  ('height above sea level', '$y{0.00} ft')],
        formatters={'$x': 'datetime'}
    )
    p = figure(title="Madison Lake Levels",
               x_axis_label='date',
               x_axis_type='datetime',
               y_axis_label='Lake Height (feet above sea level)',
               tools=["pan,wheel_zoom,box_zoom,reset,previewsave", hover],
               height=height,
               sizing_mode='stretch_width')
    p.toolbar.logo = None

    levels = []
    maxes = []
    for lake, color in zip(df.columns, palette):
        levels.append(p.line(df.index, df[lake],
                             color=color, line_width=2, name=lake.title()))
        maxes.append(p.line([df.index.min(), df.index.max()],
                            2 * [req_levels.loc[lake, 'summer_maximum']],
                            color=color,
                            line_width=2,
                            line_dash=[5, 5],
                            line_alpha=0.8))
    _msg = p.circle([], [], color='#ffffff')
    legend_items = [('Click to hide', [_msg])]
    for lake, level, _max in zip(df.columns, levels, maxes):
        lake = lake.title()
        legend_items.extend([(lake, [level]), (lake + ' max', [_max])])
    legend = Legend(items=legend_items, location=(0, 0))
    legend.click_policy = 'hide'
    p.add_layout(legend, 'left')
    tab1 = Panel(child=p, title="Absolute levels")

    hover = HoverTool(
        names=[lake.title() for lake in df],
        tooltips=[('lake', '$name'), ('date', '$x{%F}'),
                  ('height vs. max', '$y{+0.00} ft')],
        formatters={'$x': 'datetime'}
    )
    p = figure(title="Madison Lake Levels - difference from state max",
               x_axis_label='date',
               x_axis_type='datetime',
               y_axis_label='Lake Height (feet above State Max)',
               tools=["pan,wheel_zoom,box_zoom,reset,previewsave", hover],
               height=height,
               sizing_mode='stretch_width')
    p.toolbar.logo = None

    levels = []
    for lake, color in zip(df.columns, palette):
        levels.append(p.line(df.index,
                             df[lake] - req_levels.loc[lake, 'summer_maximum'],
                             name=lake.title(), color=color, line_width=2))
    _msg = p.circle([], [], color='#ffffff')
    legend_items = [('Click to hide', [_msg])]
    legend_items.append((
        'State Max',
        [p.line([df.index.min(), df.index.max()],
                [0, 0],
                color='black',
                line_dash=[5, 5])]
    ))
    for lake, level in zip(df.columns, levels):
        lake = lake.title()
        legend_items.append((lake, [level]))
    legend = Legend(items=legend_items, location=(0, 0))
    legend.click_policy = 'hide'
    p.add_layout(legend, 'left')

    tab2 = Panel(child=p, title='Levels compared to state maximum')

    tabs = Tabs(tabs=[tab1, tab2])

    script, div = components(tabs)
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
