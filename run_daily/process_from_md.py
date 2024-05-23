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

from ogbujipt.llm_wrapper import prompt_to_chat, llama_cpp_http_chat

from config import PROMPT, SUMMARIZATION_LLM_URL, SCORING_LLM_URL, ACTIONGEN_LLM_URL

import click

from config import *

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

    return refined_data


# FIXME: Needs to be rethought (async requests?)
def summarize_news(batch):
    '''
    get summary of the news item from LLM
    '''
    for item in batch:
        print(f'Summarizing news item {item["title"]}...')
        call_prompt = PROMPT['summarize_sysmsg'].format(news_content=item["content"])

        item['summary'] = g_summarization_llm(prompt_to_chat(call_prompt),
            max_tokens=2047,
            stop='###'
        ).first_choice_text.strip()

    return batch


# FIXME: Needs to be rethought (async requests?)
def score_news(batch):
    '''
    have an LLM score the item
    '''
    for item in batch:
        print(f'Scoring news item {item["title"]}...')
        call_prompt = PROMPT['score_sysmsg'].format(target_reader=PROMPT['demo_persona'], news_content=item['summary'])

        item['score'] = g_scoring_llm(prompt_to_chat(call_prompt),
            max_tokens=4,
            stop='###'
        ).first_choice_text.strip()

        print(f'Scored {item["score"]}/10!')

    return batch


# FIXME: Needs to be rethought (async requests?)
def generate_action_items(batch):
    '''
    have an LLM generate action items for the news items
    '''
    for item in batch:
        print(f'Generating action items for news item {item["title"]}...')
        call_prompt = PROMPT['action_plan_sysmsg'].format(target_reader=PROMPT['demo_persona'], news_content=item['summary'])

        item['action_items'] = g_actiongen_llm(prompt_to_chat(call_prompt),
            max_tokens=2047,
            stop='###'
        ).first_choice_text.strip()

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

    print(f"News items written to folder: {folder_path}")


async def async_main(searxng_JSON):
    print('\nProcessing searxng results to Database:')

    print('\nProcessing searxng results JSON...')
    news_batch = MD_extract(searxng_JSON)
    print(f'Got {len(news_batch)} stories!')

    news_batch = summarize_news(news_batch)

    # news_batch = score_news(news_batch)

    news_batch = generate_action_items(news_batch)
    
    print('\nUploading stories to database...')
    write_news_to_dated_folder(news_batch)
    print('Uploaded!')

    print('\nSUMMARY:', news_batch[0]['summary'])
    print('\nACTION ITEMS:', news_batch[0]['action_items'])

    print('\nDone!')


@click.command()
@click.option('--process-file', type=click.File('rb'))
def main(process_file):
    searxng_postprocessed = json.load(process_file)
    asyncio.run(async_main(searxng_postprocessed))


if __name__ == '__main__':
    main()
