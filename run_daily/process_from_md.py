'''
For example:

```sh
./run_daily/main.py --process-file=sample_serps_plus_content.json
```
'''
import json
import asyncio

import click
from ogbujipt.embedding.pgvector import DataDB  # XXX: THIS IMPLEMENTATION OF OGBUJIPT REQUIRES BEING ON 0.9.1 OR HIGHER
from fastapi import FastAPI, UploadFile # File, 

from config import *


app = FastAPI()

@app.post("/")
async def search_result_to_DB(file: UploadFile):
    searxng_JSON = json.load(file.file)
    await main(searxng_JSON)
    return 'success'


async def ensure_db():
    '''
    Ensure the news table exists
    '''
    newsDB = await DataDB.from_conn_params(  # connect to PG
        embedding_model=E_MODEL, 
        table_name=PGV_DB_TABLENAME,
        db_name=PGV_DB_NAME,
        host=PGV_DB_HOST,
        port=PGV_DB_PORT,
        user=PGV_DB_USER,
        password=PGV_DB_PASSWORD
    )

    await newsDB.create_table()  # Create a new table (if doesn't exist)
    return newsDB


def MD_extract(searxng_JSON):
    '''
    Takes in json from searchXNG(?) and extract the URL/Source, Title of article, and content of the page
    '''
    search_query = searxng_JSON['query']

    refined_data = []
    for raw_result in searxng_JSON['results']:

        extracted_item = {
            'url': raw_result.get('url'),
            'title': raw_result.get('title'),
            'content': raw_result.get('markdown_content'),  # item content as a MD
            'search_engine': raw_result.get('engine'),      # engine that got this item
            'search_score': raw_result.get('score'),        # relevance score from engine
            'search_query': search_query
        }
        refined_data.append(extracted_item)

    return refined_data
 

async def DB_upload(newsDB, news_batch):
    '''
    uploads vectorized data/data to DB 
    '''
    prepped_news = (
        (
            item['content'],  # text body we are embedding and returning
            {                 # extra metadata
                'url': item['url'],                      # url
                'title': item['title'],                  # title
                'search_engine': item['search_engine'],  # search_engine
                'search_score': item['search_score'],    # search_score
                'search_query': item['search_query']
            }
        ) for item in news_batch)

    await newsDB.insert_many(prepped_news)  # Insert the item into the table
    return newsDB


async def async_main(searxng_JSON):
    print('\nProcessing searxng results to Database:')

    print('\nProcessing searxng results JSON...')
    news_batch = MD_extract(searxng_JSON)
    print(f'Got {len(news_batch)} stories!')

    print('\nChecking if news table exists in database, if not creating one...')
    newsDB = await ensure_db()
    print('Database ready!')
    
    print('\nUploading stories to database...')
    newsDB = await DB_upload(newsDB, news_batch)
    print('Uploaded!')

    print('\nDone!')


@click.command()
@click.option('--process-file', type=click.File('rb'))
def main(process_file):
    searxng_postprocessed = json.load(process_file)
    asyncio.run(async_main(searxng_postprocessed))


if __name__ == '__main__':
    main()
