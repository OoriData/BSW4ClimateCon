# config
# Always separate config from code, but this is a 20 hour sprint, so compromise required
# Just at least putting shared routines & constants it in their own Python file,
# For simple import loading

import os
import sys
from pathlib import Path

from ogbujipt import word_loom
from ogbujipt.embedding.pgvector import DataDB
from utiloori.ansi_color import ansi_color

from sentence_transformers import SentenceTransformer  # noqa: E402
print(ansi_color('Importing SentenceTransformer; can be slow!', 'purple'), file=sys.stderr)

E_MODEL = SentenceTransformer('all-mpnet-base-v2')  # Load the embedding model

SEARCH_SETS = [
    'climate boulder',
]

SERPS_PATH = Path('./workspace')

#python date.weekday() 1 = Tuesdsay, 3 = Thursday, 5 = Saturday
DAYS_TO_RUN = [1,3,5]

# SearXNG config
SEARXNG_ENDPOINT =  os.getenv('SEARXNG_ENDPOINT', 'http://localhost:8888/search')
LIMIT = 3  # number of results to process

# LLMs endpoints
SUMMARIZATION_LLM_URL =  os.getenv('SUMMARIZATION_LLM_URL', 'http://localhost:8000')
SCORING_LLM_URL =  os.getenv('SCORING_LLM_URL', 'http://localhost:8000')
ACTIONGEN_LLM_URL =  os.getenv('ACTIONGEN_LLM_URL', 'http://localhost:8000')

LLM_TIMEOUT = 90.0

# Prompts & other natural language
with open('prompts.toml', mode='rb') as fp:
    PROMPT = word_loom.load(fp)

# PGVector connection
PGV_DB_NAME = os.environ['CLIMATE_ACTION_DB_NAME']
PGV_DB_HOST = os.environ['CLIMATE_ACTION_DB_HOST']
PGV_DB_PORT = int(os.environ['CLIMATE_ACTION_DB_PORT'])
PGV_DB_USER = os.environ['CLIMATE_ACTION_DB_USER']
PGV_DB_PASSWORD = os.environ['CLIMATE_ACTION_DB_PASSWORD']
# Just let a Traceback let the user know they're missing config, for now

PGV_DB_TABLENAME = 'climate_news'


# Shared vector DB table
async def ensure_db():
    '''
    Ensure the needed DB table exists & has the right initial data
    '''
    global VDB
    VDB = await DataDB.from_conn_params(  # connect to PG
        embedding_model=E_MODEL, 
        table_name=PGV_DB_TABLENAME,
        db_name=PGV_DB_NAME,
        host=PGV_DB_HOST,
        port=PGV_DB_PORT,
        user=PGV_DB_USER,
        password=PGV_DB_PASSWORD
    )

    await VDB.create_table()  # Create a new table (if doesn't exist)


async def ensure_language_item(litem):
    '''
    Given a language item, make sure it's in the DB, but avoid dupes
    '''
    # If we find anything with >98% similarity, treat it as a dupe
    litem_str = str(litem)
    matches = list(await VDB.search(litem_str, threshold=0.98))
    if matches:
        # FIXME: Should also check metadata
        print('✅', end='', flush=True)
        return False
    
    print('➕', end='', flush=True)
    await VDB.insert(content=litem_str, metadata=litem.meta)
    return True


MAILCHIMP_API_KEY = os.getenv("MAILCHIMP_API_KEY")
MAILCHIMP_API_SERVER = os.getenv("MAILCHIMP_API_SERVER")
MAILCHIMP_AUDIENCE_ID = os.getenv("MAILCHIMP_AUDIENCE_ID")


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
        <img src="https://10minclimate.org/api/logo" alt="Company Logo">
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
        
    <div class="footer">
        <p>Contact us at: <a href="mailto:info@10minclimate.org">info@10minclimate.org</a></p>
        <p><a href="unsubscribe-link">Unsubscribe</a></p>
        <p>&copy; 10 minute climate. All rights reserved.</p>
    </div>
</body>
</html>
'''
