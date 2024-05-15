import json
import asyncio

from sentence_transformers import SentenceTransformer
from ogbujipt.embedding.pgvector import DataDB  # XXX: THIS IMPLEMENTATION OF OGBUJIPT REQUIRES BEING ON 0.9.1 OR HIGHER

# setup embedding model
E_MODEL = SentenceTransformer('all-MiniLM-L6-v2')  # Load the embedding model

# setup PG connection
DB_NAME = 'PGv'
HOST = 'localhost'
PORT = 5432
USER = 'oori'
PASSWORD = 'example'


# process JSON --> DONE MD_extract()

    # Extract MD news articles
    # Vectorize news


# get a news article JSON

    # vectorize


# insert to DB

# pacerDB = await DataDB.from_conn_params(
#     embedding_model=e_model, 
#     table_name='pacer',
#     db_name=DB_NAME,
#     host=HOST,
#     port=int(PORT),
#     user=USER,
#     password=PASSWORD
# )

# await pacerDB.create_table()  # Create a new table

# for index, text in enumerate(pacer_copypasta):          # For each line in the copypasta
#     await pacerDB.insert(                               # Insert the line into the table
#         content=text,                                   # The text to be embedded
#         metadata={
#             'title': 'Pacer Copypasta',                 # Title metadata
#             'tags': ['fitness', 'pacer', 'copypasta'],  # Tag metadata
#             'page_numbers': index,                      # Page number metadata
#         }                               
#     )


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
            'content': raw_result.get('content'),           # item content as a MD
            'search_engine': raw_result.get('engine'),      # engine that got this item
            'search_score': raw_result.get('score'),        # relevance score from engine
            'search_query': search_query
        }
        refined_data.append(extracted_item)

    return refined_data


async def build_DB():
    '''
    Check if news table exists, if not create one
    '''
    newsDB = await DataDB.from_conn_params(  # connect to PG
        embedding_model=E_MODEL, 
        table_name='climate_news',
        db_name=DB_NAME,
        host=HOST,
        port=int(PORT),
        user=USER,
        password=PASSWORD
    )

    await newsDB.create_table()  # Create a new table (if doesn't exist)

    return newsDB

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


async def main(searxng_JSON):
    print('\nProcessing searxng results to Database:')

    print('\nProcessing searxng results JSON...')
    news_batch = MD_extract(searxng_JSON)
    print(f'Got {len(news_batch)} stories!')

    print('\nChecking if news table exists in database, if not creating one...')
    newsDB = await build_DB()
    print('Database ready!')
    
    print('\nUploading stories to database...')
    newsDB = await DB_upload(newsDB, news_batch)
    print('Uploaded!')

    print('\nDone!')


if __name__ == '__main__':
    # Open the JSON file in read mode
    with open('sample_serps_plus_content.json', 'r') as file:
        # Load the JSON data from the file
        searxng_JSON = json.load(file)

    # Run the main function asynchronously
    asyncio.run(main(searxng_JSON))