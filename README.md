# News Summarization Application 📰

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/downloads/)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.28.2-FF4B4B.svg)](https://streamlit.io)
[![NewsAPI](https://img.shields.io/badge/NewsAPI-Client-orange.svg)](https://newsapi.org)
[![Gemini](https://img.shields.io/badge/Google%20Gemini-API-4285F4.svg)](https://ai.google.dev/)

A Streamlit web application that fetches recent news articles based on user queries and provides AI-generated summaries from Google's Gemini models (free tier). The app helps users stay informed by providing quick access to news with concise summaries.



## Features ✨

- **News Search**: Search for news articles on any topic
- **AI-Powered Summaries**: Get 3–4 sentence summaries of articles from Google Gemini
- **Article Preview**: View full articles with their original images
- **User-Friendly Interface**: Clean and intuitive design built with Streamlit
- **Expandable Content**: Toggle between summary and full article text

## Technologies Used 🛠️

- **Python 3.10+**
- **Streamlit**: For the web interface
- **NewsAPI**: To fetch recent news articles
- **Google Gemini API**: For article summarization
- **Newspaper3k**: For article parsing and content extraction

## Installation 💻

1. Clone the repository:
```bash
git clone https://github.com/rajeshai/news-oneai-streamlit.git
cd news-summarization-app
```

2. Install the required packages:
```bash
pip install -r requirements.txt
```

3. Set up your API keys:
   - Get a NewsAPI key from [NewsAPI.org](https://newsapi.org)
   - Get a free Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey)

4. Create `.streamlit/secrets.toml` and add your keys (or set them as environment variables, e.g. Hugging Face Spaces secrets):
```toml
GEMINI_API_KEY = "your_gemini_api_key_here"
# Optional:
# NEWSAPI_KEY = "your_news_api_key_here"
# GEMINI_MODEL = "gemini-3.8-flash"
```

## Usage 🚀

1. Run the Streamlit app:
```bash
streamlit run app.py
```

2. Open your web browser and navigate to `http://localhost:8501`

3. Enter a search term in the text input field

4. Click "Submit" to fetch and summarize news articles

## Requirements 📋

Create a `requirements.txt` file with the following dependencies:
```
streamlit>=1.18
requests
newspaper3k
lxml[html_clean]
newsapi-python
```

## Project Structure 📁

```
news-summarization-app/
├── app.py              # Main application file
├── .streamlit/secrets.toml  # API keys (not committed)
├── requirements.txt   # Project dependencies
├── README.md         # Project documentation
└── assets/
    └── logo.jpg      # Application logo
```

## API Documentation 📚

### NewsAPI
- [NewsAPI Documentation](https://newsapi.org/docs)
- Used for fetching news articles
- Free tier includes:
  - 100 requests per day
  - Access to recent articles
  - Multiple news sources

### Google Gemini API
- [Gemini API Documentation](https://ai.google.dev/gemini-api/docs)
- Used for article summarization with a free-tier Flash model
- Free tier is rate-limited; the app shows a message when the limit is reached

## Contributing 🤝

1. Fork the repository
2. Create a new branch (`git checkout -b feature/improvement`)
3. Make your changes
4. Commit your changes (`git commit -am 'Add new feature'`)
5. Push to the branch (`git push origin feature/improvement`)
6. Create a Pull Request

## Acknowledgments 🙏

- [NewsAPI](https://newsapi.org) for providing access to news articles
- [Google Gemini](https://ai.google.dev/) for the summarization model
- [One AI](https://www.oneai.com/), which powered the original version of this app before the service shut down
- [Streamlit](https://streamlit.io/) for the awesome web framework


---
⭐️ Star this repo if you find it useful!
