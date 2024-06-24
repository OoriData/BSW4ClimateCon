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
# import re
from pathlib import Path
from datetime import datetime, date, timedelta

from ogbujipt.embedding.pgvector import DataDB, match_exact
from utiloori.ansi_color import ansi_color
import click
import httpx
from httpx import ReadTimeout
from trafilatura import extract

import climate_pg
import llm_calls  # Requires same directory import

from config import (try_func, SERPS_PATH, DAYS_TO_RUN, SEARXNG_ENDPOINT, LIMIT, SEARCH_SETS,
                    E_MODEL, DB_NAME, DB_HOST, DB_PORT, DB_USER, DB_PASSWORD)
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
        resp = await try_func(client.get, SEARXNG_ENDPOINT, params=qparams)
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
    try:
        resp = await client.get(url)
        print(ansi_color(f'\n Got URL: {url}', 'blue'))
        md_content = extract(resp.content,
                                output_format='markdown',
                                include_links=True,
                                include_comments=False)
    except Exception as e:
        print(ansi_color(f'COULD NOT READ URL {url} DUE TO "{e}"', 'red'))
        md_content = 'URL ERROR'

    result['markdown_content'] = md_content


async def store_sxng_news_search(result_set):
    today = date.today()
    fname = SERPS_PATH / Path('SERPS-' + today.isoformat() + '.json')

    print(ansi_color(f'\nStoring search results in {fname}', 'cyan'))

    SERPS_PATH.mkdir(parents=True, exist_ok=True)
    with open(fname, 'w') as fp:
        json.dump(result_set, fp)


def get_past_dates(days):
    '''
    Get the date string for `days` previous days, including the current date.
    '''
    # List to store the dates
    dates = []
    
    # Get today's date
    today = datetime.now()
    
    # Loop to get the past x dates
    for i in range(days + 1):
        date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
        dates.append(date)
    
    return dates


async def init_DB():
    global DB
    db = await climate_pg.DBHelper.from_pool_params(DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD, E_MODEL)
    # Monkeypatch in a global DBHelper instance
    DB = climate_pg.DB = db


async def async_main(sterms, dryrun, set_date):
    '''
    Entry point (for cmdline, for now)
    Takes search engine results & launches the main task to pull & process news
    '''
    await init_DB()

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

    today = date.today() if set_date is None else date.fromisoformat(set_date)
    fname = SERPS_PATH / Path('SERPS-' + today.isoformat() + '.json')
    with open(fname, 'rb') as fp:
        searxng_results = json.load(fp)

    await llm_calls.async_main(searxng_results, DB)

    # Get the news
    date_range = get_past_dates(1)  # FIXME: this will fail to grab sunday's news, presuming a Tuesday-Thursday-Saturday cadence
    climate_news = []
    for day in date_range:
        daily_news = list(await DB.news.conn.search(
            text='',
            meta_filter=match_exact('search_timestamp', day)
        ))
        if daily_news:
            for item in daily_news:
                climate_news.append(item['metadata'])

    print(ansi_color(f'Got {len(climate_news)} from DB. Selecting most relevant item...', 'Blue'))
    selected_item = await llm_calls.narrow_down_items(climate_news)

    selected_item = await llm_calls.generate_action_items(selected_item)

    # Message from the developers.
    dev_text, dev_msg = '', ''
    with open('developer_message.txt', 'r') as file:
        dev_text = file.read()

    dev_text = await DB.motd.get_motd()

    if len(dev_text) != 0:
        try:
            dev_msg =  '''<div class="section">
            <h2>Message from the developers</h2>
            <p>{dev_copy}</p>
            </div>'''.format(dev_copy=dev_text[0]['message'])
        except Exception as e:
            dev_msg = ""

    # Is it a configured e-mail send day? Run e-mail blast if so
    run_email_blast = today.weekday() in DAYS_TO_RUN
    if run_email_blast:
        print(ansi_color('Configured to send e-mail on this day', 'yellow'), file=sys.stderr)
    else:
        print(ansi_color('Configured to NOT send e-mail on this day', 'yellow'), file=sys.stderr)
    if dryrun:
        print(ansi_color('Whether or not it\'s a configured day e-mail a dry run will simulate. Look for a browser pop-up.', 'yellow'), file=sys.stderr)
        test_campaign(selected_item['url'], selected_item['summary'], selected_item['action_items'], dev_msg)
    elif run_email_blast:
        # FIXME: Should be some sort of success/failure response, or better yet try/except
        create_campaign(selected_item['url'], selected_item['summary'], selected_item['action_items'], dev_msg)
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
