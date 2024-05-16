# config
# Always separate config from code, but this is a 20 hour sprint, so compromise required
# Just at least putting shared routines & constants it in their own Python file,
# For simple import loading

import os
import sys
from pathlib import Path
from ogbujipt import word_loom
from ogbujipt.embedding.pgvector import DataDB

print('Importing SentenceTransformer; can be slow!', file=sys.stderr)
from sentence_transformers import SentenceTransformer  # noqa: E402

E_MODEL = SentenceTransformer('all-MiniLM-L6-v2')  # Load the embedding model

SERPS_PATH = Path('./working')

# LLMs endpoints
SUMMARIZATION_LLM_URL = 'https://localhost:8080'
ACTIONGEN_LLM_URL = 'https://localhost:8081'

# Prompts & other natural language
with open('prompts.toml', mode='rb') as fp:
    PROMPT = word_loom.load(fp)

# PGVector connection
PGV_DB_NAME = 'PGv'
PGV_DB_HOST = 'localhost'
PGV_DB_PORT = 5432
PGV_DB_USER = 'oori'
# Just let a Traceback let the user know they're missing config, for now
PGV_DB_PASSWORD = os.environ['CLIMATE_ACTION_DB_PASSWORD']

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
