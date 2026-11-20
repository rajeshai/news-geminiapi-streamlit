import os
import time
import streamlit as st
import json
import requests
from newspaper import Article
from newsapi import NewsApiClient

st.set_page_config(page_title='Short News App',
    layout = 'wide',
    initial_sidebar_state = 'expanded',
    menu_items={
        'About': 'A demo news app that summarizes articles with Google Gemini.',
        'Get help': 'https://ai.google.dev/gemini-api/docs',
        'Report a Bug': 'https://github.com/rajeshai/news-oneai-streamlit/issues'
    })

st.title('Short Summary News Application with Google Gemini')
st.markdown('This application takes an input from the user and displays up to five latest news articles along with their summary. It uses the free tiers of NewsAPI and the Gemini API.')
st.sidebar.title('Google Gemini')
st.sidebar.markdown('[Gemini](https://ai.google.dev/) is Google\'s family of AI models. This app uses a free-tier Gemini Flash model through the Gemini API to write a short summary of each news article.')
st.sidebar.markdown('''Besides summarization, the Gemini API can do tasks like
- Sentiment Analysis
- Named Entity Recognition
- Topic Analysis
- Keyword Extraction
- Question Answering

Learn more:''')
st.sidebar.markdown('[Gemini API documentation](https://ai.google.dev/gemini-api/docs)')
st.sidebar.markdown('[Get a free API key (Google AI Studio)](https://aistudio.google.com/apikey)')
st.sidebar.markdown('[NewsAPI](https://newsapi.org)')

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
# Free-tier models, tried in order. If one is busy (503), rate-limited (429)
# or not available (404), the next one is used. GEMINI_MODEL, if set, is tried first.
# Flash-Lite models come first: they answer fastest and have the most free requests.
FALLBACK_GEMINI_MODELS = [
    "gemini-3.5-flash-lite",
    "gemini-flash-lite-latest",
    "gemini-3.8-flash",
    "gemini-3.6-flash",
]
REQUEST_TIMEOUT = (10, 30)  # seconds to connect, seconds to wait for the answer
RETRY_STATUSES = {500, 503}  # temporary server errors worth retrying
MAX_ARTICLE_CHARS = 12000  # enough for a summary; shorter input means faster answers

SUMMARY_PROMPT = (
    "Summarize the following news article in 3 to 4 sentences. "
    "Cover the main facts: who, what, when and why. "
    "Use only information from the article and write in plain, neutral language.\n\n"
    "Article:\n{article}"
)

class MissingKeyError(Exception):
    pass


def get_key(name, default=None):
    # API keys come from Streamlit secrets or environment variables
    # (e.g. Hugging Face Spaces secrets), never from the code.
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass  # no secrets.toml (e.g. on Hugging Face Spaces)
    value = os.environ.get(name, default)
    if value is None:
        raise MissingKeyError(f"{name} is not set. Add it to Streamlit secrets or as an environment variable.")
    return value


@st.cache_resource
def get_newsapi_client():
    # One NewsAPI client, created once and reused across reruns and users.
    return NewsApiClient(api_key=get_key("NEWSAPI_KEY"))


def gemini_models():
    preferred = get_key("GEMINI_MODEL", "")
    models = [preferred] if preferred else []
    return models + [m for m in FALLBACK_GEMINI_MODELS if m != preferred]


@st.cache_data(ttl=24 * 3600, show_spinner=False)
def fetch_summary(text):
    # Cached by article text, so the same article is only summarized once a day.
    # Errors are raised (not shown here) so a failed call is never cached.
    headers = {'x-goog-api-key': get_key("GEMINI_API_KEY"), 'content-type': 'application/json'}
    payload = {
        'contents': [{'parts': [{'text': SUMMARY_PROMPT.format(article=text[:MAX_ARTICLE_CHARS])}]}]
    }
    last_error = None
    for model in gemini_models():
        for attempt in range(2):  # one retry per model for temporary errors
            try:
                r = requests.post(GEMINI_URL.format(model=model), json=payload, headers=headers,
                                  timeout=REQUEST_TIMEOUT)
            except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
                last_error = e  # slow or unreachable: try the next model right away
                r = None
                break
            if r.ok:
                parts = r.json()['candidates'][0]['content']['parts']
                summary_text = ''.join(p.get('text', '') for p in parts if not p.get('thought')).strip()
                if not summary_text:
                    raise KeyError('empty summary')
                return summary_text
            try:
                r.raise_for_status()
            except requests.exceptions.HTTPError as e:
                last_error = e
            if r.status_code in RETRY_STATUSES and attempt == 0:
                time.sleep(2)
                continue
            break  # move on to the next model
        if r is not None and r.status_code not in RETRY_STATUSES | {404, 429}:
            raise last_error  # e.g. 400/403: a key or request problem, other models won't help
    raise last_error


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
        if not text1 or not text1.strip():
            return None
        try:
            return fetch_summary(text1)
        except MissingKeyError as e:
            st.error(str(e))
            return None
        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response is not None else None
            if status == 429:
                st.error("The free Gemini API limit has been reached. Please try again later.")
            elif status in (500, 503):
                st.error("Gemini is busy right now. Please try again in a minute.")
            else:
                st.error(f"Error calling Gemini API: {str(e)}")
            return None
        except requests.exceptions.Timeout:
            st.error("Gemini took too long to respond. Please try again in a minute.")
            return None
        except requests.exceptions.RequestException as e:
            st.error(f"Error calling Gemini API: {str(e)}")
            return None
        except (KeyError, IndexError) as e:
            st.error(f"Error processing Gemini response: {str(e)}")
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
