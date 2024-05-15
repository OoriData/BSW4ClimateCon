from ogbujipt.embedding.pgvector import DataDB  # XXX: THIS IMPLEMENTATION OF OGBUJIPT REQUIRES BEING ON 0.9.1 OR HIGHER
from ogbujipt.llm_wrapper import openai_api

import json

from dotenv import load_dotenv
import os



load_dotenv()
LLM_BASE = os.getenv("LLM_BASE")


LLM_obj = openai_api(base_url=LLM_BASE)

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

def LLM_summarize(news_content, sumarize_prompt):
    '''
    Assemble the news and article titles into a readable string for the LLM to read
    '''
    call_prompt = sumarize_prompt.format(news_content = news_content)

    summarized_news  = LLM_obj.call(
        prompt = call_prompt,
        max_tokens=2047
    ).first_choice_text

    return summarized_news


def LLM_action_plan(news_data):

    

    return



# XXX Prompts for action and summarization 

sumarize_prompt = '''
You are a summarization bot tasked with reading news articles and providing a TL;DR (Too Long; Didn't Read) that is concise and easy for users to understand. Below are the news articles provided:

```
{news_content}
```

Please respond with a summary of the news article(s). Ensure the summary is clear, concise, and provides the essential details for a quick and easy understanding of the main points.


'''

action_plan_prompt = '''
You are a climate activist bot. Your role is to read summaries of news articles related to climate change and suggest practical actions that users can take to contribute to the fight against climate change. Below is the summary of the news articles:

```
{news_summary} 
```

Based on the issues highlighted in the summary, please provide a simple, actionable step that the user can incorporate into their daily life to address one of the climate challenges mentioned. Ensure the action is feasible and directly related to the content of the summary.  Bonus points for a suggested action that is impactful and fun.

'''

def main():
    test_prompt = '''
    Article 1/2: Exploring the Impact of AI in Healthcare
Artificial Intelligence (AI) is revolutionizing the healthcare industry, offering promising solutions for various challenges. From diagnostic assistance to personalized treatment plans, AI has the potential to enhance patient care and streamline processes.
Source: https://example.com/article1

Article 2/2: The Role of Blockchain in Supply Chain Management
Blockchain technology is reshaping supply chain management by providing transparency, traceability, and security throughout the entire process. With blockchain, businesses can ensure authenticity and efficiency in their supply chains, leading to improved operations and customer satisfaction.
Source: https://example.com/article2
    '''
    print("AHHHHH")
    print(LLM_summarize(test_prompt, sumarize_prompt))

    return

main()