![](/static/website-image.png)

# Madison's lake levels

https://madison-lake-levels.herokuapp.com/

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

![](https://travis-ci.com/kbrose/madison-lake-levels.svg?branch=master)

## Deploy

The webapp is deployed to Heroku. It can be found at https://madison-lake-levels.herokuapp.com/.

A free-tier of a database on Heroku is used to persist the data.

A daily cron job runs that updates the database. The job is created using [Heroku Scheduler](https://devcenter.heroku.com/articles/scheduler), and hits a simple API route on the web-app that causes an update.
