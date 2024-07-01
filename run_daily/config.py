# config
# Always separate config from code, but this is a 20 hour sprint, so compromise required
# Just at least putting shared routines & constants it in their own Python file,
# For simple import loading

import os
import sys
from pathlib import Path
import toml

from ogbujipt import word_loom
from utiloori.ansi_color import ansi_color

from sentence_transformers import SentenceTransformer  # noqa: E402

print(ansi_color('Importing SentenceTransformer; can be slow!', 'purple'), file=sys.stderr)
E_MODEL = SentenceTransformer('all-mpnet-base-v2')  # Load the embedding model

DEFAULT_DOTS_SPACING = 0.2  # Number of seconds between each dot printed to console

SEARCH_SETS = [
    'climate',
]

SERPS_PATH = Path('./workspace')

# python date.weekday() 1 = Tuesdsay, 3 = Thursday, 5 = Saturday
DAYS_TO_RUN = [1, 3, 5]

# SearXNG config
SEARXNG_ENDPOINT = os.getenv('SEARXNG_ENDPOINT', 'http://localhost:8888/search')
LIMIT = int(os.getenv('SEARXNG_LIMIT', '3'))  # number of results to process

# LLMs endpoints
SUMMARIZATION_LLM_URL = os.getenv('SUMMARIZATION_LLM_URL', 'http://localhost:9000')
SCORING_LLM_URL = os.getenv('SCORING_LLM_URL', 'http://localhost:9000')
ACTION_GEN_LLM_URL = os.getenv('ACTION_GEN_LLM_URL', 'http://localhost:9000')

LLM_TIMEOUT = 90.0
CALL_ATTEMPTS = 6

BUNDLE_SIZE = 6  # size of tournament rounds for narrowing down articles

# Prompts & other natural language
with open('prompt/prompt_frames.toml', mode='rb') as fp:
    PROMPT = word_loom.load(fp)

# PGVector connection
DB_NAME = os.environ['CLIMATE_ACTION_DB_NAME']
DB_HOST = os.environ['CLIMATE_ACTION_DB_HOST']
DB_PORT = int(os.environ['CLIMATE_ACTION_DB_PORT'])
DB_USER = os.environ['CLIMATE_ACTION_DB_USER']
DB_PASSWORD = os.environ['CLIMATE_ACTION_DB_PASSWORD']
# Just let a Traceback let the user know they're missing config, for now


async def try_func(func, *args, **kwargs):
    retries = 0
    succeeded = False
    while not succeeded:
        try:
            response = await func(*args, **kwargs)
            succeeded = True
        except Exception as e:
            retries += 1
            print(ansi_color(f'UH OH, had to retry a call due to "{e}"', bg_color='red'))
            print(ansi_color(f'retries: {retries}', bg_color='red'))
            if retries >= CALL_ATTEMPTS:
                raise e

    return response


MAILCHIMP_API_KEY = os.getenv('MAILCHIMP_API_KEY')
MAILCHIMP_API_SERVER = os.getenv('MAILCHIMP_API_SERVER')
MAILCHIMP_AUDIENCE_ID = os.getenv('MAILCHIMP_AUDIENCE_ID')


EMAIL_TEMPLATE = '''<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: Arial, sans-serif; }}
        .header {{ text-align: center; padding: 10px; background-color: #F4F4F4; }}
        .header img {{ max-width: 150px; }}
        .content {{ padding: 20px; }}
        .section {{ margin-bottom: 20px; }}
        .section h2 {{ font-size: 20px; color: #333; }}
        .cta-button {{ display: inline-block; padding: 10px 20px; color: #fff; background-color: #007BFF; text-decoration: none; border-radius: 5px; }}
        .footer {{ text-align: center; padding: 10px; background-color: #F4F4F4; font-size: 12px; }}
        .footer a {{ color: #007BFF; text-decoration: none; }}
    </style>
</head>
<body>
    <div class="header">
        <img src="https://raw.githubusercontent.com/OoriData/BSW4ClimateCon/main/logo.png" alt="Company Logo">
        <h1>Climate Action Newsletter</h1>
        <p>May 2024</p>
    </div>
    <div class="content">
        <div class="section">
            <h2>Welcome!</h2>
            <!-- <p>Dear [recipient],</p> -->
            <p>Welcome to your email update. Here's a quick overview of what’s happening in climate action since last time.</p>
        </div>
        <div class="section">
            <h2>Latest News</h2>
            <h3>This is a summary of the latest news:</h3>
            <p>{summary}</p>
            <p><a href="{url}">Read More</a></p>
        </div>
        <div class="section">
            <h2>Action</h2>
            <h3>This is what you can do to help:</h3>
            <p>{action_items}</p>
        </div>
        {dev_block}
        
    <div class="footer">
        <p>Contact us at: <a href="mailto:info@10minclimate.org">info@10minclimate.org</a></p>
        <p><a href="unsubscribe-link">Unsubscribe</a></p>
        <p>&copy; 10 minute climate. All rights reserved.</p>
    </div>
</body>
</html>
'''
