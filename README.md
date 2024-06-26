# 10minclimate.com

At [Boulder Startup Week](https://boulderstartupweek.com/) Builder's Room Uche Ogbuji ([Oori Data](https://oori.dev)) had a simple idea: build a simple tool to regularly grab and select climate-related news, and bring these to a subscriber's attention alongside a few relevant action items—so it's not just downer after downer, but a way to feel involved and conscious. Before he knew it, he had a team of 9 folks interested in pitching in, over the course of a 20 hour sprint. We shipped a prototype, came in 2nd place, and 10minclimate.com was born. One inspiration for the project is [ClimateCon!](https://climatecon.world/), a conference in Boulder, a few weeks after BSW (31 May 2024).

The project continues, and we hope it will continue to be of use to busy people who care about the climate, and need an affirmative way to keep engaged.

Sprint prticipants:
 - [Micah Dew](https://github.com/micahtdew) ([LinkedIn](https://www.linkedin.com/in/micahdew/))
 - [Zachariah Malik](https://github.com/ZaMalik123) ([LinkedIn](https://www.linkedin.com/in/zachariah-malik-74a13a190/))
 - Troy Namath ([LinkedIn](https://www.linkedin.com/in/troynamath/))
 - [Osi Ogbuji](https://github.com/choccccy) ([LinkedIn](https://www.linkedin.com/in/osi-ogbuji/))
 - [Uche Ogbuji](https://github.com/uogbuji) ([LinkedIn](https://www.linkedin.com/in/ucheogbuji/))
 - [Aidan Reese](https://github.com/Aidan-Reese) ([LinkedIn](https://www.linkedin.com/in/aidan-c-reese/))
 - [Garrett Roberts](https://github.com/garrettmroberts) ([LinkedIn](https://www.linkedin.com/in/garrettmroberts/))
 - Elaine Yang ([LinkedIn](https://www.linkedin.com/in/elaine-yang-988a641/))
 - Sung Yi ([LinkedIn](https://www.linkedin.com/in/sung-carambito/))

## So what does it do, again?

10minclimate.com sends a regular (thrice weekly) e-mail to subscribers (e-mail only at present). This automated e-mail focuses on one digestible, contemporary climate news item, which it summarizes and presents along with three simple actions the reader can take with that news item in mind.

<!--
demonstrate a positive bias to climate action.

, ideally with some level of community-building features. 

a tree of hashtag#LLM processing

[Boulder Startup Week Builder's Room event, 2024](https://boulderstartupweek2024.sched.com/event/1cEl1/builders-room-kickoff)

Code structure:

* For this BSW Builder sprint it will just be all-in-one run-daily command (presumed via cron)

-->

10minclimate.com does run on an LLM workload, and it's well known that [AI itself has a Climate Change problem](https://builtin.com/artificial-intelligence/ai-climate-change-dilemma). We ran (courtesy [Zachariah Malik](https://github.com/ZaMalik123) ([LinkedIn](https://www.linkedin.com/in/zachariah-malik-74a13a190/))) some numbers to see that on the M1 Mac Studio we're using to host its LLM inference, the CO₂ contribution is less than that of one person breathing.

# Implementation

There are several key components for the project. You can tweak how these are all used in `run_daily/config.py`

## Prerequisites:

### Python

Python 3.11 or more recent, preferably in a virtual environment

example setup:
```sh
python3.11 -m venv $HOME/.local/venv/bsw
pip install -Ur requirements.txt
```

### SearXNG

Running [SearXNG](https://github.com/searxng/searxng) instance. You can just use the Docker container. To run this locally:

```sh
export SEARXNG_PORT=8888
docker run --rm \
    -d -p ${SEARXNG_PORT}:8080 \
    -v "${PWD}/searxng:/etc/searxng" \
    -e "BASE_URL=http://localhost:$SEARXNG_PORT/" \
    -e "INSTANCE_NAME=ten-min-climate-engine" \
    searxng/searxng
```

Note: We want to have some sort of API key, but doesn't seem there is any built-in approach (`SEARXNG_SECRET` is something different). We might have to use a reverse proxy with HTTP auth.

This gets SearXNG runing on port 8888. Feel free to adjust as necessary in the 10minclimate.com config.

You do need to edit `searxng/settings.yml` relative to where you launched the docker comtainer, making sure `server.limiter` is set to false and `- json` is included in `search.formats`.

You can then just restart the continer (use `docker ps` to get the ID, `docker stop [ID]` and then repeat the `docker run` command above).

<!-- Not needed at present
One trick for generating a secret key:

```sh
python -c "from uuid import uuid1; print(str(uuid1()))"
```
-->

### Running on a shared server

For production SearXNG will need to run on a shared server. Make sure that server has Docker installed, set it as the context. Create `/etc/searxng` on the remote server and ensure it's writable by the docker daemon.

```sh
sudo chgrp docker /etc/searxng
sudo chmod g+ws /etc/searxng
```

Then launch with the following setup, where `/etc/searxng` is mounted

```sh
export SEARXNG_PORT=8888
docker run --rm \
    -d -p ${SEARXNG_PORT}:8080 \
    -v "/etc/searxng:/etc/searxng" \
    -e "BASE_URL=http://localhost:$SEARXNG_PORT/" \
    -e "INSTANCE_NAME=oorihive-engine" \
    searxng/searxng
```


### LLM endpoint(s)

Uses [llama.cpp remotely hosted](https://github.com/ggerganov/llama.cpp/blob/master/examples/server/README.md) for LLM processing.

Set up an endpoint, and update your environment


### 3rd-party python libraries

From your virtual environment:

```sh
pip install -Ur requirements.txt
```

# Running the daily command

`run_daily/main.py` will:

* pull news for the past day
* run LLM-based assessments, summarization, credibility scoring & storage of best candidates for next action e-mail
* check e-mail day criteria (as configured, e.g. Tuesday, Thursday and Saturdays)
* if it's an e-mail day, pull all pending news item candidates & LLM-generate action items
* Send e-mail to gethered addresses

Until you're sure you know what you're doing, you probably want to use the dry run feature (see testing section, below)

## Testing
### Setting environment variables:

[Use a sound approach to set up the environment, including secrets.](https://github.com/OoriData/OgbujiPT/discussions/36)

For example, if you use 1password and have a file `op.env`, you can just set the environment inline to run any `COMMAND`:

```
op run —env-file op.env -- COMMAND
```

### Test command:

So in the case of tsting:

```
dotenv -f op.env run -- op run --env-file=op.env -- run_daily/main.py --dry-run
```

### example `.env`
```
SEARXNG_ENDPOINT="http://localhost:8888/search"
SEARXNG_LIMIT="6"

SUMMARIZATION_LLM_URL="http://localhost:8000"
SCORING_LLM_URL="http://localhost:8000"
ACTION_GEN_LLM_URL="http://localhost:8000"

CLIMATE_ACTION_DB_NAME="climateDB"
CLIMATE_ACTION_DB_HOST="localhost"
CLIMATE_ACTION_DB_PORT="1234"
CLIMATE_ACTION_DB_USER="user"
CLIMATE_ACTION_DB_PASSWORD="password"

MAILCHIMP_API_KEY="key"
MAILCHIMP_API_SERVER="localhost"
MAILCHIMP_AUDIENCE_ID="12345"
```

You can use both `--dry-run` and `--set-date` specify a date to test how the program would operate on a given day.

```
run_daily/main.py --dry-run --set-date=2024-05-23
```

# Docker setup

```sh
❯ docker build -t tmclimate-cron -f ./docker/rundaily/dockerfile  
```

# Design notes

* Separates language from code using [Word Loom](https://github.com/OoriData/OgbujiPT/wiki/Word-Loom:-A-format-for-managing-language-for-AI-LLMs-(including-prompts))


# TODO

## Product

* Personalization, which will be fed into prompting for summarization & suggested actions
* Credibility checking of news items

## Dev

* Data flow & other engineering diagrams
* Proper library setup & modularization (now all spaghetti-thrown into the `run_daily` dir)
* Online archive of past action e-mails

* Continue to think about managing/securing SearXNG (as well as PGVector & llama.cpp). [Security-minded "Searx Installation and Discussion" article](https://grahamhelton.com/blog/searx/).

# HISTORY: WHITEBOARD notes from Kickoff day (May 14)

## Problem:
**keeping up with climate news is overwhelming and demoralizing**

## Solution:
- Hub to push info/ideas/actions to user based on climate news
- utilizing AI to customize/agregate/summarize(/score on the backend?) feed based on specific interests
- email the user actionable steps
  - daily weather
  - summarize relevant news (for the user)
  - give users a selection of action items relevant to the situation

## maybe out of scope, but cool ideas!
- gamification?
  - UX focused around a big thermometer that's goin up with climate change and when you do an action, you make a dent on it!
- show/record what the user has done to keep them invested
- (geographical) scale filtering?
- politicization?
- group action?
