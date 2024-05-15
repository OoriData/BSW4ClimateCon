# BSW4ClimateCon

BSW for ClimateCon! We wanted to sprint up from scratch a tool to send a regular (thrice weekly) inspo e-mail to interested users, ideally with some level of community-building features. The automated e-mail would focus on one digestible contemporary climate news item and 3 simple actions the reader can take with that news item in mind. ClimateCon! in Boulder May 31st is a great opportunity to get a lot of interested eyes on such a project, and to demonstrate a positive bias to climate action.

[Boulder Startup Week](https://boulderstartupweek.com/)
[Boulder Startup Week Builder's Room event, 2024](https://boulderstartupweek2024.sched.com/event/1cEl1/builders-room-kickoff)
[ClimateCon!](https://climatecon.world/)


Code structure:

* For this BSW Builder sprint it will just be all-in-one run-daily command (presumed via cron)

```sh
pip install -Ur requirements.txt
./run_daily.py
```

`run_daily.py` will:

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
* Implement prototype LLM processing tree (via [OgbujiPT]())
* Data flow & other engineering diagrams
* Implement e-mail batch send process
