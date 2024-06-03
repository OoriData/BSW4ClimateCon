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
import re
from pathlib import Path

from utiloori.ansi_color import ansi_color
import click
import httpx
from trafilatura import extract

import process_from_md as process_from_md  # Requires same directory import

from datetime import date

from config import SERPS_PATH, DAYS_TO_RUN, SEARXNG_ENDPOINT, LIMIT, SEARCH_SETS
from send_campaign_email import create_campaign, test_campaign

# SEARXNG_ENDPOINT = 'https://search.incogniweb.net/'  # Public instances seem all broken. Luckily, easy to self-host
DEFAULT_DOTS_SPACING = 0.2  # Number of seconds between each dot printed to console


async def indicate_progress(pause=DEFAULT_DOTS_SPACING):
    while True:
        print('.', end='', flush=True)
        await asyncio.sleep(pause)


async def do_sxng_news_search(terms):
    '''
    Main task: Uses SearXNG to pull & process news
    '''
    # https://docs.searxng.org/dev/search_api.html
    # curl "http://localhost:8888/search?q=solarpunk&categories=\!news&time_range=day&format=json"
    # curl -O "http://localhost:8888/search?q=climate+boulder&categories=\!news&time_range=week&format=json"
    qparams = {
        'q': terms,
        'categories': ['!bin','!gon','!yhn'],
        'time_range': 'day',
        'format': 'json'
    }
    # async with httpx.AsyncClient(verify=False) as client:
    print(ansi_color(f'\nRunning search for: "{terms}"', 'blue'))
    async with httpx.AsyncClient() as client:
        resp = await client.get(SEARXNG_ENDPOINT, params=qparams)
        # html = resp.content.decode(resp.encoding or 'utf-8')
        results_obj = resp.json()
        if LIMIT:
            results_list = results_obj['results'] = results_obj['results'][:LIMIT]
        else:
            results_list = results_obj['results']
        # Note: top-level `number_of_results` always seems to be 0
        results_count = len(results_list)
        print(ansi_color(f'\n{results_count} result(s) scraped', 'blue'), file=sys.stderr)
        # answers = results_obj['answers']
        # corrections = results_obj['corrections']
        # infoboxes = results_obj['infoboxes']
        # suggestions = results_obj['suggestions']
        # unresponsive_engines = results_obj['unresponsive_engines']

        # FIXME: Use asyncio.gather (or async for) properly here
        for result in results_list:
            await add_content_as_markdown(client, result)

        return results_obj


async def add_content_as_markdown(client, result):
    '''
    Load HTML from the content of the result HTML, converts it to Markdown & adds it back to the results structure
    '''
    url = result['url']
    resp = await client.get(url)
    print(ansi_color(f'\n Got URL: {url}', 'blue'))
    md_content = extract(resp.content,
                            output_format='markdown',
                            include_links=True,
                            include_comments=False)
    result['markdown_content'] = md_content


async def store_sxng_news_search(result_set):
    today = date.today()
    fname = SERPS_PATH / Path('SERPS-' + today.isoformat() + '.json')

    print(ansi_color(f'\nStoring search results in {fname}', 'cyan'))

    SERPS_PATH.mkdir(parents=True, exist_ok=True)
    with open(fname, 'w') as fp:
        json.dump(result_set, fp)


async def async_main(sterms, dryrun, set_date):
    '''
    Entry point (for cmdline, for now)
    Takes search engine results & launches the main task to pull & process news
    '''
    if sterms is None:
        search_sets = SEARCH_SETS
    else:
        search_sets = [sterms]

    search_tasks = asyncio.gather(*[
        asyncio.create_task(do_sxng_news_search(sterm)) for sterm in search_sets])

    # searx_task = asyncio.create_task(do_sxng_news_search(sterms))
    indicator_task = asyncio.create_task(indicate_progress())
    tasks = [indicator_task, search_tasks]
    done, _ = await asyncio.wait(
        tasks, return_when=asyncio.FIRST_COMPLETED)

    for result_set in search_tasks.result():
        await store_sxng_news_search(result_set)

    # Here we call the article summarizer (in process_from_md.py)
    today = date.today() if set_date is None else date.fromisoformat(set_date)
    fname = SERPS_PATH / Path('SERPS-' + today.isoformat() + '.json')
    with open(fname, 'rb') as fp:
        searxng_results = json.load(fp)
    await process_from_md.async_main(searxng_results)

    today_folder = SERPS_PATH / 'daily_news' / today.isoformat()
    today_folder.mkdir(parents=True, exist_ok=True)
    with open(today_folder / 'news_1.json', 'rb') as fp:  # TODO: need to actually consider multiple stories for the user, not just #1
        first_search_result = json.load(fp)

    summary = first_search_result['summary']
    action_items = first_search_result['action_items']

    # XXX : Temp solution untill
    summary = re.sub("<\|im_end\|>", '', summary)
    action_items = re.sub("<\|im_end\|>", '', action_items)

    url = first_search_result['url']

    # Is it a configured e-mail send day? Run e-mail blast if so
    run_email_blast = today.weekday() in DAYS_TO_RUN
    if run_email_blast:
        print(ansi_color('Configured to send e-mail on this day', 'yellow'), file=sys.stderr)
    else:
        print(ansi_color('Configured to NOT send e-mail on this day', 'yellow'), file=sys.stderr)
    if dryrun:
        print(ansi_color('Whether or not it\'s a configured day e-mail a dry run will simulate. Look for a browser pop-up.', 'yellow'), file=sys.stderr)
        test_campaign(url, summary, action_items)
    elif run_email_blast:
        # FIXME: Should be some sort of success/failure response, or better yet try/except
        create_campaign(url, summary, action_items)
        # If we sent an e-mail delete files in the working space
        for f in SERPS_PATH.glob('*.json'):
            f.unlink()


async def async_test(content):
    '''
    Just a quick & dirty test entry point for pulling Markdown from an already sownloaded SearXNG JSON result set
    '''
    async with httpx.AsyncClient() as client:
        results_obj = json.load(content)
        results_list = results_obj['results']
        # Note: top-level `number_of_results` always seems to be 0
        results_count = len(results_list)
        print(ansi_color(f'\n{results_count} result(s) scraped', 'blue'), file=sys.stderr)
        # FIXME: Use asyncio.gather (or async for) properly here
        for result in results_list:
            await add_content_as_markdown(client, result)


@click.command()
# @click.option('--verbose/--no-verbose', default=False)
@click.option('--testfile', type=click.File('rb'))
@click.option('--dry-run', is_flag=True, default=False,
              help='Don\'t actually send e-mail blast, but always generate & send output to stdout.')
@click.option('--dry-run-web', is_flag=True, default=False,
              help='Don\'t actually send e-mail blast, but always generate & pop-up HTML output.')
@click.option('--set-date',
              help='Run as if on the given date (in ISO8601 format). Only use with --dry-run flag.')
@click.argument('sterms', required=False)
def main(sterms, testfile, dry_run, dry_run_web, set_date):
    # print('Args:', (sterms, testfile, dry_run))
    if set_date: assert dry_run or dry_run_web  # noqa: E701
    if testfile:
        asyncio.run(async_test(testfile))
    else:
        asyncio.run(async_main(sterms, dry_run, set_date))


if __name__ == '__main__':
    main()
