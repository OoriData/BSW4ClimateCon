from sentence_transformers import SentenceTransformer
from ogbujipt.embedding.pgvector import DataDB  # XXX: THIS IMPLEMENTATION OF OGBUJIPT REQUIRES BEING ON 0.9.1 OR HIGHER

# setup
e_model = SentenceTransformer('all-MiniLM-L6-v2')  # Load the embedding model


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




def MD_extract(data):
    '''
    Takes in json from searchXNG(?) and extract the URL/Source, Title of article, and content of the page
    '''
    refined_data = []
    for source in data['results']:

        extracted_item = {
        "url": source.get("url"),
        "title": source.get("title"),
        "content": source.get("content"),
        # "score": source.get("score") # Uncomment this line to include relivance score from SearchXNG
        }
        refined_data.append(extracted_item)

def Vectorize_MD(data):
    '''
    returns data with vectorized content included
    '''
    return

def DB_upload(data):
    '''
    uploads vectorized data/data to DB 
    '''
    return

def build_DB():
    '''
    Duh
    '''

def relivant_news():
    '''
    get relivant news from db
    '''

def main():
    return

if __name__ == '__main__':
    # load JSON

    # feed JSON to main loop
    main()