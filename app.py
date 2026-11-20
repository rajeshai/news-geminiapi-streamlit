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
DEFAULT_GEMINI_MODEL = "gemini-3.8-flash"  # free-tier Flash model; override with GEMINI_MODEL
MAX_ARTICLE_CHARS = 20000  # keep requests small to stay within free-tier token limits

SUMMARY_PROMPT = (
    "Summarize the following news article in 3 to 4 sentences. "
    "Cover the main facts: who, what, when and why. "
    "Use only information from the article and write in plain, neutral language.\n\n"
    "Article:\n{article}"
)

# Free-tier keys. Streamlit secrets or environment variables (e.g. Hugging Face
# Spaces secrets) override these if they are set.
DEFAULT_KEYS = {
    "NEWSAPI_KEY": "e07356679fcb40e98d44a37b323e9dd6",
}


class MissingKeyError(Exception):
    pass


def get_key(name, default=None):
    try:
        if name in st.secrets:
            return st.secrets[name]
    except Exception:
        pass  # no secrets.toml (e.g. on Hugging Face Spaces)
    value = os.environ.get(name, DEFAULT_KEYS.get(name, default))
    if value is None:
        raise MissingKeyError(f"{name} is not set. Add it to Streamlit secrets or as an environment variable.")
    return value


@st.cache_resource
def get_newsapi_client():
    # One NewsAPI client, created once and reused across reruns and users.
    return NewsApiClient(api_key=get_key("NEWSAPI_KEY"))


@st.cache_data(ttl=24 * 3600, show_spinner=False)
def fetch_summary(text):
    # Cached by article text, so the same article is only summarized once a day.
    # Errors are raised (not shown here) so a failed call is never cached.
    model = get_key("GEMINI_MODEL", DEFAULT_GEMINI_MODEL)
    headers = {'x-goog-api-key': get_key("GEMINI_API_KEY"), 'content-type': 'application/json'}
    payload = {
        'contents': [{'parts': [{'text': SUMMARY_PROMPT.format(article=text[:MAX_ARTICLE_CHARS])}]}]
    }
    r = requests.post(GEMINI_URL.format(model=model), json=payload, headers=headers, timeout=60)
    r.raise_for_status()
    parts = r.json()['candidates'][0]['content']['parts']
    summary_text = ''.join(p.get('text', '') for p in parts if not p.get('thought')).strip()
    if not summary_text:
        raise KeyError('empty summary')
    return summary_text


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
            if e.response is not None and e.response.status_code == 429:
                st.error("The free Gemini API limit has been reached. Please try again later.")
            else:
                st.error(f"Error calling Gemini API: {str(e)}")
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
