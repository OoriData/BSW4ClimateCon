# BSW4ClimateCon

BSW for ClimateCon! We wanted to sprint up from scratch a tool to send a regular (thrice weekly) inspo e-mail to interested users, ideally with some level of community-building features. The automated e-mail would focus on one digestible contemporary climate news item and 3 simple actions the reader can take with that news item in mind. ClimateCon! in Boulder May 31st is a great opportunity to get a lot of interested eyes on such a project, and to demonstrate a positive bias to climate action.

[Boulder Startup Week](https://boulderstartupweek.com/)
[Boulder Startup Week Builder's Room event, 2024](https://boulderstartupweek2024.sched.com/event/1cEl1/builders-room-kickoff)
[ClimateCon!](https://climatecon.world/)


Code structure:

* For this BSW Builder sprint it will just be all-in-one run-daily command (presumed via cron)

```sh
pip install -Ur requirements.txt
./main/run_daily.py
```

`run_daily/main.py` will:

* pull news for the past day
* run LLM-based assessments, summarization, credibility scoring & storage of best candidates for next action e-mail
* check e-mail day criteria (we've discussed action only on Tuesday, Thursday and Saturday for this sprint scoping, obviously to be simulated for the showcase/demo)
* if it's an e-mail day, pull all pending news item candidates & LLM-generate action items
* Send e-mail to gethered addresses

Support code & processes:

* Gathering e-mail addresses. For now simple Google form
* Stretch: Online archive of past action e-mails


## TODO

### Product

* Establish "Boulderite in their 30s-40s" user/actor persona prompt
* Complete e-mail sender/action inspirer prompt
* Narrow down focus of daily news search criteria
* Outline process for credibility checking?
* ???

### Dev

* Complete pull process for e-mail addresses from Google Form
* Complete data pipeline
* Separate out language using [Word Loom](https://github.com/OoriData/OgbujiPT/wiki/Word-Loom:-A-format-for-managing-language-for-AI-LLMs-(including-prompts))
* Implement prototype LLM processing tree (via [OgbujiPT](https://github.com/OoriData/OgbujiPT))
* Data flow & other engineering diagrams
* Implement e-mail batch send process
* Combine separate program files such as `process_from_md.py` into `run_daily.py` (using )

# Dev setup

```sh
python3.11 -m venv $HOME/.local/venv/bsw
pip install -Ur requirements.txt 

```

# WHITEBOARD notes from Kickoff day (Tuesday)

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