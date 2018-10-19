import flask
import madison_lake_levels as mll

app = flask.Flask(__name__)

@app.route('/')
def main():
    current = mll.scrape.scrape()
    required_levels = mll.required_levels.required_levels
    lakes = ['mendota', 'monona', 'waubesa', 'kegonsa']
    statuses = [
        current[lake].iloc[0] > required_levels.loc[lake, 'summer_maximum']
        for lake in lakes
    ]
    statuses = zip([lake.title() for lake in lakes], statuses)
    return flask.render_template('main.html', statuses=statuses)


if __name__ == '__main__':
    app.run()
