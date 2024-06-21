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
from ogbujipt.embedding.pgvector import match_exact
from utiloori.ansi_color import ansi_color

from config import try_func, PROMPT, SUMMARIZATION_LLM_URL, SCORING_LLM_URL, ACTION_GEN_LLM_URL, LLM_TIMEOUT, SERPS_PATH, BUNDLE_SIZE

SUMMARIZATION_LLM = llama_cpp_http_chat(base_url=SUMMARIZATION_LLM_URL)
SCORING_LLM = llama_cpp_http_chat(base_url=SCORING_LLM_URL)
ACTION_GEN_LLM = llama_cpp_http_chat(base_url=ACTION_GEN_LLM_URL)


def MD_extract(searxng_JSON):
    '''
    Takes in json from searchXNG(?) and extract the URL/Source, Title of article, and content of the page
    '''
    search_query = searxng_JSON['query']

    refined_items = []
    for raw_result in searxng_JSON['results']:

        extracted_item = {
            'url': raw_result.get('url'),
            'title': raw_result.get('title'),
            'content': raw_result.get('markdown_content'),  # item content as MarkDown
            'search_engine': raw_result.get('engine'),      # engine that got this item
            'search_score': raw_result.get('score'),        # relevance score from engine
            'search_query': search_query                    # query that was used for this search
        }
        
        refined_items.append(extracted_item)

    return refined_items


async def filter_news(news_batch, DB):
    '''
    Reads news and makes sure its a news story and nor 
    '''
    filtered_news = []
    for item in news_batch:
        if list(await DB.news.conn.search(text='', meta_filter=match_exact('url', item['url']))):  # Look for the article in the DB, if not found, continue
            print(ansi_color(f'News item "{item['title']}" is already in DB, skipping', 'purple'))
        elif not item['content']:
            print(ansi_color(f'No content for news item "{item['title']}", skipping', 'purple'))
        else:
            print(ansi_color(f'Filtering news item "{item['title']}"...', 'yellow'))

            call_prompt = PROMPT['filter_msg'].format(news_content=item['content'])

            response = (await try_func(
                SCORING_LLM,
                    prompt_to_chat(call_prompt),
                    timeout=LLM_TIMEOUT
            )).first_choice_text.strip()

            if 'true' in response.lower():
                filtered_news.append(item)
                print(ansi_color(f'"{item['title']}" is news: "{response}"', 'green'))
            else:
                print(ansi_color(f'"{item['title']}" is NOT news, skipping: "{response}"', 'red'))

    return filtered_news


# FIXME: Needs to be rethought (async requests?)
async def summarize_news(news_batch):
    '''
    get summary of the news item from LLM
    '''
    for item in news_batch:
        print(ansi_color(f'\nSummarizing news item "{item['title']}" (using {SUMMARIZATION_LLM_URL})...', 'yellow'))
        call_prompt = PROMPT['summarize_sysmsg'].format(news_content=item['content'])

        response = (await try_func(
            SUMMARIZATION_LLM,
                prompt_to_chat(call_prompt),
                timeout=LLM_TIMEOUT,
                max_tokens=2047
        )).first_choice_text.strip()
        item['summary'] = markdown2html(response)

    return news_batch


# FIXME: Needs to be rethought (async requests?)
async def generate_batch_action_items(news_batch, reader_description=PROMPT['demo_reader']):
    '''
    have an LLM generate action items for the news items
    '''
    for item in news_batch:
        print(ansi_color(f'\nGenerating action items for news item "{item['title']}"...', 'yellow'))

        if date.today().weekday() == 5:
            call_prompt = PROMPT['sat_action_plan_sysmsg'].format(target_reader=reader_description, news_content=item['summary'])
        else:
            call_prompt = PROMPT['action_plan_sysmsg'].format(target_reader=reader_description, news_content=item['summary'])

        response = (await try_func(
            ACTION_GEN_LLM,
                prompt_to_chat(call_prompt),
                timeout=LLM_TIMEOUT,
                max_tokens=2047
        )).first_choice_text.strip()
        item['action_items'] = markdown2html(response)

    return news_batch


async def generate_action_items(item, reader_description=PROMPT['demo_reader']):
    '''
    have an LLM generate action items for a news item
    '''
    print(ansi_color(f'\nGenerating action items for news item "{item['title']}"...', 'yellow'))

    if date.today().weekday() == 5:
        call_prompt = PROMPT['sat_action_plan_sysmsg'].format(target_reader=reader_description, news_content=item['summary'])
    else:
        call_prompt = PROMPT['action_plan_sysmsg'].format(target_reader=reader_description, news_content=item['summary'])

    response = (await try_func(
        ACTION_GEN_LLM,
            prompt_to_chat(call_prompt),
            timeout=LLM_TIMEOUT,
            max_tokens=2047
    )).first_choice_text.strip()
    item['action_items'] = markdown2html(response)

    return item


def make_bundles(seq, k):
    'Yield successive k-sized chunks from seq'
    for i in range(0, len(seq), k):
        yield seq[i:i + k]


async def narrow_down_call(news_batch, reader_description):
    prepped_bundle = ''
    print(ansi_color('CHOOSING between these 6 items:', 'yellow'))
    for index, item in enumerate(news_batch):
        print(f'  * "{item['title']}"')
        prepped_bundle += f'[news item {index}]:\n'
        prepped_bundle += f'{item['summary']}\n\n'

    call_prompt = PROMPT['score_sysmsg'].format(prepped_bundle=prepped_bundle, target_reader=reader_description)

    response = (await try_func(
        SCORING_LLM,
            prompt_to_chat(call_prompt),
            timeout=LLM_TIMEOUT,
            max_tokens=2047
    )).first_choice_text.strip()
    # response = response.first_choice_text.strip()

    response_lines = response.split('\n')
    most_relevant_index = int(response_lines[0])
    most_relevant_item = news_batch[most_relevant_index]
    
    print(ansi_color(f'SELECTION: "{most_relevant_item['title']}"', 'yellow'))
    print(ansi_color(response, 'cyan'))

    return most_relevant_item


async def narrow_down_items(news_batch, reader_description=PROMPT['demo_reader']):
    '''
    Narrow down items and find the best item via recursive elimination.
    '''
    if len(news_batch) <= 1:  # Base case: If the news_batch has one or fewer items, return the first item.
        return news_batch[0]

    news_bundles = list(make_bundles(news_batch, BUNDLE_SIZE))

    finalists = [await narrow_down_call(bundle, reader_description) for bundle in news_bundles]

    return await narrow_down_items(finalists, reader_description)  # Recursive call with the finalists


def write_news_to_dated_folder(news_batch):
    # Create a folder with today's date
    today = datetime.now().strftime('%Y-%m-%d')
    folder_path = os.path.join(f'{os.getcwd()}/workspace/daily_news', today)
    folder_path = SERPS_PATH / 'daily_news' / Path(today)
    os.makedirs(folder_path, exist_ok=True)

    # Write each news item to a JSON file
    for i, item in enumerate(news_batch, start=1):
        # Construct the filename
        filename = f'news_{i}.json'
        file_path = os.path.join(folder_path, filename)

        # Write the news item to the JSON file
        with open(file_path, 'w') as json_file:
            json.dump(item, json_file, indent=4)

    print(ansi_color(f'News items written to folder: {folder_path}', 'yellow'))


async def write_news_to_DB(news_batch, DB):
    today = datetime.now().strftime('%Y-%m-%d')

    bundled_news_batch = []
    for item in news_batch:
        item['search_timestamp'] = today
        bundled_news_batch.append((item['title'], item))  # Would prefer a very short summary to using the often goofy and truncated title
    
    await DB.news.conn.insert_many(bundled_news_batch)


async def async_main(searxng_JSON, DB):
    print(ansi_color('\nProcessing searxng results to Database:', 'yellow'))

    print(ansi_color('Processing searxng results JSON...', 'yellow'))
    news_batch = MD_extract(searxng_JSON)
    print(ansi_color(f'Got {len(news_batch)} stories!', 'yellow'))

    news_batch = await filter_news(news_batch, DB)

    news_batch = await summarize_news(news_batch)

    # news_batch = await generate_batch_action_items(news_batch)
    
    print(ansi_color('\nUploading stories to database...', 'yellow'))
    await write_news_to_DB(news_batch, DB)
    # write_news_to_dated_folder(news_batch)

    print(ansi_color('Uploaded!', 'yellow'))

    # print(ansi_color(f'\nSUMMARY: {news_batch[0]['summary']}', 'yellow'))
    # print(ansi_color(f'\nACTION ITEMS: {news_batch[0]['action_items']}', 'yellow'))


@click.command()
@click.option('--process-file', type=click.File('rb'))
def main(process_file):
    searxng_postprocessed = json.load(process_file)
    asyncio.run(async_main(searxng_postprocessed))


if __name__ == '__main__':
    main()
