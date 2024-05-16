# Always better to separate config from code, but this is a 20 hour sprint,
# so compromise required. We're just at least putting it in its own Python file,
# For simple Python import loading

import os
from sentence_transformers import SentenceTransformer
E_MODEL = SentenceTransformer('all-MiniLM-L6-v2')  # Load the embedding model

# PGVector connection
PGV_DB_NAME = 'PGv'
PGV_DB_HOST = 'localhost'
PGV_DB_PORT = 5432
PGV_DB_USER = 'oori'
# Just let a Traceback let the user know they're missing config, for now
PGV_DB_PASSWORD = os.environ['CLIMATE_ACTION_DB_PASSWORD']

PGV_DB_TABLENAME = 'climate_news'

# LLMs in use
SUMMARIZATION_LLM_URL = 'https://localhost:8080'
ACTIONGEN_LLM_URL = 'https://localhost:8081'
