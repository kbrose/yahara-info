![](/static/website-image.png)

**The code here no longer runs, and the website has been shutdown. This repository will be left up for historical purposes.**

# Lake levels from the Yahara Watershed

Madison Wisconsin and the surrounding Dane County saw near record level rainfalls in late August. Widespread flooding caused over two hundred million dollars in damage ([Associated Press](https://apnews.com/15a2ca91bcb94840bceb192365cf01a1)).

In the months leading up to the flood, the lakes surrounding Madison were higher than the maximum level set by the Wisconsin Department of Natural Resources in 1979.

How often has that been true? Are the lakes currently above that maximum level? Why were they kept so high? All of these questions and more we hope to address.

## Environment setup

Install [postgresql](https://www.postgresql.org/download/).

Make sure you have an environment variable named `USER` with your username as its value. On UNIX variants this likely already exists

Create a new user with your username who has permissions to create a database, e.g. with `sudo -u postgres createuser -s $USER`.

It is recommended to set up some sort of virtual environment. After that, install the requirements with

```bash
pip install -r requirements.txt
```

## Code

The code is in `madison_lake_levels`, and requires python >= 3.6. You can run tests with `python -m pytest` run from the top level of this project.

## Running locally

Run with

```bash
# Get env set up
export FLASK_APP=app.py
export DATABASE_URL=postgres://$USER:@:/madisonlakes # heroku's env var format
createdb madisonlakes -U $USER
# Run the app
flask run
# To run in debug mode (don't do in prod!):
export FLASK_ENV=development
flask run
```

![](https://travis-ci.com/kbrose/yahara-info.svg?branch=master)

## Deploy

The webapp used to be deployed to Heroku, but the USGS data source broke and Heroku got rid of their tier. The heroku-format `Procfile` and `runtime.txt` are used to control deployment.

A free-tier of a database on Heroku was used to persist the data.

A cron job runs every 30 minutes that updates the database. The job is created using [Heroku Scheduler](https://devcenter.heroku.com/articles/scheduler), and hits a simple API route on the web-app that causes an update. Running the job every 30 minutes has a nice side effect of preventing the website from going into hibernation mode (which Heroku does on the free tier).
