from sentence_transformers import SentenceTransformer
from ogbujipt.embedding.pgvector import DataDB

# setup
e_model = SentenceTransformer('all-MiniLM-L6-v2')  # Load the embedding model

# process JSON

    # Extract MD news articles
    # Vectorize news


# get a news article JSON

    # vectorize


# insert to DB

pacerDB = await DataDB.from_conn_params(
    embedding_model=e_model, 
    table_name='pacer',
    db_name=DB_NAME,
    host=HOST,
    port=int(PORT),
    user=USER,
    password=PASSWORD
)

await pacerDB.create_table()  # Create a new table

for index, text in enumerate(pacer_copypasta):          # For each line in the copypasta
    await pacerDB.insert(                               # Insert the line into the table
        content=text,                                   # The text to be embedded
        metadata={
            'title': 'Pacer Copypasta',                 # Title metadata
            'tags': ['fitness', 'pacer', 'copypasta'],  # Tag metadata
            'page_numbers': index,                      # Page number metadata
        }                               
    )