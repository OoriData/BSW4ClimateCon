'''
For example:

```sh
./run_daily/process_from_md.py --process-file=sample_serps_plus_content.json
```
'''
import os
import json
import asyncio
from datetime import datetime, date
from pathlib import Path

from markdown import markdown as markdown2html
import click

from ogbujipt.llm_wrapper import prompt_to_chat, llama_cpp_http_chat
from ogbujipt.embedding.pgvector import DataDB
from utiloori.ansi_color import ansi_color

from config import (PROMPT, SUMMARIZATION_LLM_URL, SCORING_LLM_URL, ACTIONGEN_LLM_URL, LLM_TIMEOUT, SERPS_PATH,
                    E_MODEL, PGV_DB_NAME, PGV_DB_HOST, PGV_DB_PORT, PGV_DB_USER, PGV_DB_PASSWORD, PGV_DB_TABLENAME)

g_summarization_llm = llama_cpp_http_chat(base_url=SUMMARIZATION_LLM_URL)
g_scoring_llm = llama_cpp_http_chat(base_url=SCORING_LLM_URL)
g_actiongen_llm = llama_cpp_http_chat(base_url=ACTIONGEN_LLM_URL)


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
        if not extracted_item['content']:
            print(ansi_color(f'WARNING: No content for {extracted_item["title"]}', 'red'))

    return refined_data


# FIXME: Needs to be rethought (async requests?)
async def summarize_news(batch):
    '''
    get summary of the news item from LLM
    '''
    for item in batch:
        print(ansi_color(f'\nSummarizing news item {item["title"]} (using {SUMMARIZATION_LLM_URL})...', 'yellow'))
        call_prompt = PROMPT['summarize_sysmsg'].format(news_content=item['content'])

        response = await g_summarization_llm(prompt_to_chat(call_prompt),
            timeout=LLM_TIMEOUT,
            max_tokens=2047
        )
        item['summary'] = markdown2html(response.first_choice_text.strip())

    return batch


# FIXME: Needs to be rethought (async requests?)
async def score_news(batch):
    '''
    have an LLM score the item
    '''
    for item in batch:
        print(ansi_color(f'\nScoring news item {item["title"]}...', 'yellow'))
        call_prompt = PROMPT['score_sysmsg'].format(target_reader=PROMPT['demo_persona'], news_content=item['summary'])

        response = await g_scoring_llm(prompt_to_chat(call_prompt),
            timeout=LLM_TIMEOUT
        )
        item['score'] = response.first_choice_text.strip()

        print(f'Scored {item["score"]}/10!')

    return batch


# FIXME: Needs to be rethought (async requests?)
async def generate_action_items(batch):
    '''
    have an LLM generate action items for the news items
    '''
    for item in batch:
        print(ansi_color(f'\nGenerating action items for news item {item["title"]}...', 'yellow'))

        if date.today().weekday() == 5:
            call_prompt = PROMPT['sat_action_plan_sysmsg'].format(target_reader=PROMPT['demo_persona'], news_content=item['summary'])
        else:
            call_prompt = PROMPT['action_plan_sysmsg'].format(target_reader=PROMPT['demo_persona'], news_content=item['summary'])

        
        response = await g_actiongen_llm(prompt_to_chat(call_prompt),
            timeout=LLM_TIMEOUT,
            max_tokens=2047
        )
        item['action_items'] = markdown2html(response.first_choice_text.strip())

    return batch


def write_news_to_dated_folder(news_batch):
    # Create a folder with today's date
    today = datetime.now().strftime("%Y-%m-%d")
    folder_path = os.path.join(f'{os.getcwd()}/workspace/daily_news', today)
    folder_path = SERPS_PATH / 'daily_news' / Path(today)
    os.makedirs(folder_path, exist_ok=True)

    # Write each news item to a JSON file
    for i, item in enumerate(news_batch, start=1):
        # Construct the filename
        filename = f"news_{i}.json"
        file_path = os.path.join(folder_path, filename)

        # Write the news item to the JSON file
        with open(file_path, 'w') as json_file:
            json.dump(item, json_file, indent=4)

    print(ansi_color(f'News items written to folder: {folder_path}', 'yellow'))


async def write_news_to_DB(news_batch):
    today = datetime.now().strftime("%Y%m%d")

    # Upload news contents to DB
    climateDB = await DataDB.from_conn_params(  # Perhaps this should be a conn pool that we dip into from config. this whole program needs a hefty batch of actual async, tbh
        embedding_model=E_MODEL, 
        table_name=PGV_DB_TABLENAME,
        db_name=PGV_DB_NAME,
        host=PGV_DB_HOST,
        port=int(PGV_DB_PORT),
        user=PGV_DB_USER,
        password=PGV_DB_PASSWORD
    )
    await climateDB.create_table()

    bundled_news_batch = []
    for item in news_batch:
        item['searchTimestamp'] = today
        bundled_news_batch.append((item['title'], item))  # Would prefer a very short summary to using the often goofy and truncated title
    await climateDB.insert_many(bundled_news_batch)


async def filter_news(news_batch):
    '''
    Reads news and makes sure its a news story and nor 
    '''
    filtered_news = []
    print(len(news_batch))
    for article in news_batch:
        print(ansi_color(f'\Filtering news item {article["title"]}', 'yellow'))

        call_prompt = PROMPT['filter_msg'].format(news_content=article['content'])

        response = await g_scoring_llm(prompt_to_chat(call_prompt),
            timeout=LLM_TIMEOUT
        )

        response = response.first_choice_text.strip()

        if "true" in response.lower():
            filtered_news.append(article)
            print(ansi_color(f'Good - {response}', 'green'))
        else:
            print(ansi_color(f'Bad- {response}', 'red'))

    return filtered_news



async def filter_news(news_batch):
    '''
    Reads news and makes sure its a news story and nor 
    '''
    filtered_news = []
    print(len(news_batch))
    for article in news_batch:
        print(ansi_color(f'\Filtering news item {article["title"]}', 'yellow'))

        call_prompt = PROMPT['filter_msg'].format(news_content=article['content'])

        response = await g_scoring_llm(prompt_to_chat(call_prompt),
            timeout=LLM_TIMEOUT
        )

        response = response.first_choice_text.strip()

        if "true" in response.lower():
            filtered_news.append(article)
            print(ansi_color(f'Good - {response}', 'green'))
        else:
            print(ansi_color(f'Bad- {response}', 'red'))

    return filtered_news



async def async_main(searxng_JSON):
    print(ansi_color('\nProcessing searxng results to Database:', 'yellow'))

    print(ansi_color('Processing searxng results JSON...', 'yellow'))
    news_batch = MD_extract(searxng_JSON)
    print(ansi_color(f'Got {len(news_batch)} stories!', 'yellow'))

    # news_batch = [item for item in news_batch if 'wikipedia'.lower() not in item['title'].lower()]

    # TODO: make this into a function that just vibe checks if this is a story, or if it's wikipeidia entry or w/e
    news_batch = await filter_news(news_batch)

    news_batch = await summarize_news(news_batch)

    news_batch = await generate_action_items(news_batch)  # TODO: Move this to happen *after* the news item is selected to be sent in the email
    
    print(ansi_color('\nUploading stories to database...', 'yellow'))
    await write_news_to_DB(news_batch)
    # write_news_to_dated_folder(news_batch)
    print(ansi_color('Uploaded!', 'yellow'))

    # print(ansi_color(f'\nSUMMARY: {news_batch[0]["summary"]}', 'yellow'))
    # print(ansi_color(f'\nACTION ITEMS: {news_batch[0]["action_items"]}', 'yellow'))

    print(ansi_color('\nDone!', 'yellow'))


@click.command()
@click.option('--process-file', type=click.File('rb'))
def main(process_file):
    searxng_postprocessed = json.load(process_file)
    asyncio.run(async_main(searxng_postprocessed))


if __name__ == '__main__':
    main()
