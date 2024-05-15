#!/usr/bin/env python
# Shebang above SHOULD honor virtualenvs
'''
* pull news for the past day
* run LLM-based assessments, summarization, credibility scoring & storage of best candidates for next action e-mail
* check e-mail day criteria (we've discussed action only on Tuesday, Thursday and Saturday for this sprint scoping, obviously to be simulated for the showcase/demo)
  * if it's an e-mail day, pull all pending news item candidates & LLM-generate action items
  * Send e-mail to gethered addresses

Command-line entry point is `main()`, using the click library

For AWS Lambda entry point, we'll probbaly set up a function parallel to `async_main` (or modify this until it's dual purpose)
  
'''

import sys
import json
import asyncio

import click
import httpx
from trafilatura import extract

import process_from_md  # Requires same directory import

# SEARXNG_ENDPOINT = 'https://search.incogniweb.net/'  # Public instances seem all broken. Luckily, easy to self-host
SEARXNG_ENDPOINT = 'https://search.incogniweb.net/'
DEFAULT_DOTS_SPACING = 0.2  # Number of seconds between each dot printed to console


# Not currently used
# async def indicate_progress(pause=DEFAULT_DOTS_SPACING):
#     while True:
#         print('.', end='', flush=True)
#         await asyncio.sleep(pause)


async def do_sxng_news_search(terms):
    '''
    Main task: Uses SearXNG to pull & process news
    '''
    # https://docs.searxng.org/dev/search_api.html
    # curl "http://localhost:8888/search?q=solarpunk&categories=\!news&time_range=day&format=json"
    # curl -O "http://localhost:8888/search?q=climate+boulder&categories=\!news&time_range=week&format=json"
    qparams = {'q': terms,
               'categories': '!news',
               'time_range': 'week',
               'format': 'json'}
    # async with httpx.AsyncClient(verify=False) as client:
    async with httpx.AsyncClient() as client:
        resp = await client.get(SEARXNG_ENDPOINT, params=qparams)
        # html = resp.content.decode(resp.encoding or 'utf-8')
        results_obj = resp.json
        results_list = results_obj['results']
        # Note: top-level `number_of_results` always seems to be 0
        results_count = len(results_list)
        print(results_count, 'result(s)', file=sys.stderr)
        # answers = results_obj['answers']
        # corrections = results_obj['corrections']
        # infoboxes = results_obj['infoboxes']
        # suggestions = results_obj['suggestions']
        # unresponsive_engines = results_obj['unresponsive_engines']

        # FIXME: Use asyncio.gather (or async for) properly here
        for result in results_list:
            add_content_as_markdown(client, result)


async def add_content_as_markdown(client, result):
    '''
    Loads the HTML from the content of the result HTML, converts it to Markdown & adds it back to the results structure
    '''
    resp = await client.get(result['url'])
    md_content = extract(resp.content,
                            output_format='markdown',
                            include_links=True,
                            include_comments=False)
    result['markdown_content'] = md_content



async def async_main(sterms):
    '''
    Entry point (for cmdline, for now)
    Takes search engine results & launches the main task to pull & process news
    '''
    url_task_group = asyncio.gather(*[
        asyncio.create_task(do_sxng_news_search(sterms))])
    indicator_task = asyncio.create_task(indicate_progress())
    tasks = [indicator_task, url_task_group]
    done, _ = await asyncio.wait(
        tasks, return_when=asyncio.FIRST_COMPLETED)


async def async_test(content):
    '''
    Just a quick & dirty test entry point for pulling Markdown from an already sownloaded SearXNG JSON result set
    '''
    async with httpx.AsyncClient() as client:
        results_obj = json.load(content)
        results_list = results_obj['results']
        # Note: top-level `number_of_results` always seems to be 0
        results_count = len(results_list)
        print(results_count, 'result(s)', file=sys.stderr)
        # FIXME: Use asyncio.gather (or async for) properly here
        for result in results_list:
            # print(result)
            await add_content_as_markdown(client, result)
    print(json.dumps(results_obj, indent=2))


@click.command()
# @click.option('--verbose/--no-verbose', default=False)
# @click.option('--limit', default=4, type=int,
#               help='Maximum number of chunks matched against the posed question to use as context for the LLM')
@click.option('--testfile', type=click.File('rb'))
@click.argument('sterms')
def main(sterms, testfile):
    if testfile:
        asyncio.run(async_test(testfile))
    else:
        asyncio.run(async_main(sterms))


if __name__ == '__main__':
    main()