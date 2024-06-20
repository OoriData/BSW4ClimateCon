import asyncio

# XXX: We probably want to use the chat API rather than raw completion
from ogbujipt.llm_wrapper import openai_api

from config import PROMPT, SUMMARIZATION_LLM_URL, ACTION_GEN_LLM_URL, ensure_db, ensure_language_item


g_summarization_llm = openai_api(base_url=SUMMARIZATION_LLM_URL)
g_action_gen_llm = openai_api(base_url=ACTION_GEN_LLM_URL)

async def init():
    sample_actions = PROMPT['sample_actions']
    for line in str(sample_actions).splitlines():
        line = line.strip()
        if line:
            # We process it line-by line, but the metadata is fixed
            line_lang_item = sample_actions.clone(line)
            await ensure_language_item(line_lang_item)


# TODO: Need to change this to be searching by recency rather than nearest neighbor. probably needs a more specialized table style than DataDB
async def search_news(newsDB, search_term):
    '''
    searches the DB to 
    '''
    search_term = "climate" # Search term to the database
    news_stories = 1 # limit of how many news stories 

    news_data = await newsDB.search(
        text = search_term,
        limit = news_stories
    )

    return news_data


def news_content_collection(news_data):
    news_content = ''
    num_sources = len(news_data)
    for i, source in enumerate(news_data):
        title = source.get('title')
        content = source.get('content')
        url = source.get('url')

        # Construct the article
        article = f"Article {i}/{num_sources} : "
        article += f"{title}\n\n"
        article += f"Content:\n{content}\n\n"
        article += f"Source: {url}\n\n"

        news_content += article + '\n\n'
    return news_content


# FIXME: Needs to be rethought
def summarize_article(news_content, sumarize_prompt):
    '''
    Assemble the news and article titles into a readable string for the LLM to read
    '''
    call_prompt = sumarize_prompt.format(news_content = news_content)

    summarized_news  = g_summarization_llm.call(
        prompt = call_prompt,
        max_tokens=2047
    ).first_choice_text

    return summarized_news


# XXX: Untested
def LLM_action_plan(news_summary, action_prompt):
    call_prompt = action_prompt.format(news_summary = news_summary)

    action_plan  = g_summarization_llm.call(
        prompt = call_prompt,
        max_tokens=2047
    ).first_choice_text

    return action_plan


async def async_main():
    await ensure_db()
    await init()


if __name__ == '__main__':
    asyncio.run(async_main())
