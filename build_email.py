from ogbujipt.embedding.pgvector import DataDB  # XXX: THIS IMPLEMENTATION OF OGBUJIPT REQUIRES BEING ON 0.9.1 OR HIGHER

async def search_news(newsDB, search_term):
    '''
    searches the DB to 
    '''
    search_term = "climate" # Search term to the database
    news_stories = 3 # limit of how many news stories 

    news_data = await newsDB.search(
        text = search_term,
        limit = news_stories
    )

    return news_data

def LLM_summarize(news_data):
    '''
    Assemble the news and article titles into a readable string for the LLM to read
    '''


    return

def news_content_collection():

    return 

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