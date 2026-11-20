import os
import streamlit as st
import json
import requests
from newspaper import Article
from newsapi import NewsApiClient

st.set_page_config(page_title='Short News App',
    layout = 'wide',
    initial_sidebar_state = 'expanded',
    menu_items={
        'About':'This is a demo application with One AI',
        'Get help':'https://studio.oneai.com/docs',
        'Report a Bug':'https://discord.com/channels/941458663493746698/941458828187287603'
    })

st.title('Short Summary News Application Demo with OneAI')
st.markdown('This application takes an input from the user and displays upto five latest news articles along with their summary. This application uses the free quota api calls.')
st.sidebar.image('logo.jpg')
st.sidebar.title('ONE AI')
st.sidebar.markdown('[One AI](https://www.oneai.com/) is an API-first, language AI service built for developers. Embed your API to analyze, process, and transform text in your project.')
st.sidebar.markdown('''It can perform several tasks like
- Sentiment Analysis
- Named Entity Recognition
- Topic Analysis
- Text Summarization
- Keyword Extraction
There are several more tasks that One AI can do. Please find the below links to explore more about this:''')
st.sidebar.markdown('[About us](https://www.oneai.com/about-us)')
st.sidebar.markdown('[Documentation](https://studio.oneai.com/docs)')
st.sidebar.markdown('[Contact](https://www.oneai.com/contact-us)')
st.sidebar.markdown('[Community](https://discord.com/channels/941458663493746698/942326235722309642)')
st.sidebar.markdown('© 2022 Logo rights reserved to One AI')

ONEAI_URL = "https://api.oneai.com/api/v0/pipeline"

# Free-tier keys. Streamlit secrets or environment variables (e.g. Hugging Face
# Spaces secrets) override these if they are set.
DEFAULT_KEYS = {
    "NEWSAPI_KEY": "e07356679fcb40e98d44a37b323e9dd6",
    "ONEAI_API_KEY": "1c93487c-695c-4089-adfc-5e4b7623718c",
}


def get_key(name):
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass  # no secrets.toml (e.g. on Hugging Face Spaces)
    return os.environ.get(name, DEFAULT_KEYS[name])


@st.cache_resource
def get_newsapi_client():
    # One NewsAPI client, created once and reused across reruns and users.
    return NewsApiClient(api_key=get_key("NEWSAPI_KEY"))


@st.cache_data(ttl=24 * 3600, show_spinner=False)
def fetch_summary(text):
    # Cached by article text, so the same article is only summarized once a day.
    # Errors are raised (not shown here) so a failed call is never cached.
    headers = {'api-key': get_key("ONEAI_API_KEY"), 'content-type': 'application/json'}
    payload = {
        'input': text,
        'input_type': 'article',
        'steps': [{'skill': 'summarize'}]
    }
    r = requests.post(ONEAI_URL, json=payload, headers=headers, timeout=60)
    r.raise_for_status()
    return r.json()['output'][0]['text']


@st.cache_data(ttl=15 * 60, show_spinner=False)
def fetch_links(query):
    # Cached for 15 minutes to save NewsAPI quota on repeated searches.
    all_articles = get_newsapi_client().get_everything(q=query,
                                                       language='en',
                                                       sort_by='relevancy',
                                                       page_size=5,
                                                       page=1)
    if all_articles['status'] != 'ok':
        raise RuntimeError(all_articles.get('message', 'Unknown error'))
    return [article['url'] for article in all_articles['articles']]


def run():
    def summary(text1):
        try:
            return fetch_summary(text1)
        except requests.exceptions.RequestException as e:
            st.error(f"Error calling One AI API: {str(e)}")
            return None
        except (KeyError, IndexError) as e:
            st.error(f"Error processing One AI response: {str(e)}")
            return None

    def get_links(query):
        try:
            return fetch_links(query)
        except Exception as e:
            st.error(f"Error fetching news: {str(e)}")
            return []

    input_text = st.text_input('Search your favorite topic:')
    submitted = st.button('Submit')
    
    if submitted and input_text:
        with st.spinner('Fetching news articles...'):
            links = get_links(input_text)
            
            if not links:
                st.warning("No articles found. Please try a different search term.")
                return
                
            for link in links:
                try:
                    with st.spinner(f'Processing article from {link}...'):
                        news_article = Article(link, language='en')
                        news_article.download()
                        news_article.parse()
                        
                        if news_article.top_image:
                            st.image(news_article.top_image)
                        
                        st.header(news_article.title)
                        st.markdown('*Summary of the Article:*')
                        
                        article_summary = summary(news_article.text)
                        if article_summary:
                            st.markdown(article_summary)
                        else:
                            st.warning("Could not generate summary for this article")
                            
                        with st.expander('Full Article'):
                            st.markdown(news_article.text)
                            
                except Exception as e:
                    st.error(f"Error processing article from {link}: {str(e)}")
                    continue
    elif submitted:
        st.warning("Please enter a search term")

if __name__ == '__main__':
    run()
