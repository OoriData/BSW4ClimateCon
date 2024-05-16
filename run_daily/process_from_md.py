'''
For example:

```sh
./run_daily/process_from_md.py --process-file=sample_serps_plus_content.json
```
'''
import os
import json
import asyncio
from datetime import datetime

# XXX: We probably want to use the chat API rather than raw completion
from ogbujipt.llm_wrapper import openai_api

from config import PROMPT, SUMMARIZATION_LLM_URL, ACTIONGEN_LLM_URL, ensure_db, ensure_language_item

import click

from config import *

<<<<<<< Updated upstream
g_summarization_llm = openai_api(base_url=SUMMARIZATION_LLM_URL)
g_actiongen_llm = openai_api(base_url=ACTIONGEN_LLM_URL)
=======

app = FastAPI()

@app.post("/")
async def search_result_to_DB(file: UploadFile):
    searxng_JSON = json.load(file.file)
    await main(searxng_JSON)
    return 'success'
>>>>>>> Stashed changes


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
            'content': raw_result.get('markdown_content'),  # item content as MarkDown
            'search_engine': raw_result.get('engine'),      # engine that got this item
            'search_score': raw_result.get('score'),        # relevance score from engine
            'search_query': search_query
        }
        refined_data.append(extracted_item)

    return refined_data


# FIXME: Needs to be rethought
def summarize_article(batch):
    '''
    Assemble the news and article titles into a readable string for the LLM to read
    '''
    for item in batch:
        print(f'processing news item {item['title']}...')
        call_prompt = PROMPT['summarize_sysmsg'].format(news_content=item['content'])

        item['summary'] = g_summarization_llm.call(
            prompt = call_prompt,
            max_tokens=2047
        ).first_choice_text.strip()

        print(f'processed news item {item['title']}!')

    return batch


def write_news_to_dated_folder(news_batch):
    # Create a folder with today's date
    today = datetime.now().strftime("%Y-%m-%d")
    folder_path = os.path.join(f'{os.getcwd()}/workspace/daily_news', today)
    folder_path = SERPS_PATH / 'daily_news' / Path(today)
    os.makedirs(folder_path, exist_ok=True)

    # Write each news item to a JSON file
    for i, item in enumerate(news_batch, start=1):
        news_item = {
            'summary': item['summary'],
            'url': item['url'],
            'title': item['title'],
            'search_engine': item['search_engine'],
            'search_score': item['search_score'],
            'search_query': item['search_query']
        }

        # Construct the filename
        filename = f"news_{i}.json"
        file_path = os.path.join(folder_path, filename)

        # Write the news item to the JSON file
        with open(file_path, 'w') as json_file:
            json.dump(news_item, json_file, indent=4)

    print(f"News items written to folder: {folder_path}")


async def async_main(searxng_JSON):
    print('\nProcessing searxng results to Database:')

    print('\nProcessing searxng results JSON...')
    news_batch = MD_extract(searxng_JSON)
    print(f'Got {len(news_batch)} stories!')

    news_batch = summarize_article(news_batch)
    
    print('\nUploading stories to database...')
    write_news_to_dated_folder(news_batch)
    print('Uploaded!')

    print('\nDone!')


@click.command()
@click.option('--process-file', type=click.File('rb'))
def main(process_file):
    searxng_postprocessed = json.load(process_file)
    asyncio.run(async_main(searxng_postprocessed))


if __name__ == '__main__':
    main()
