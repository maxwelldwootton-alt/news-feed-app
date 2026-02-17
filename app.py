import streamlit as st
import requests
from textblob import TextBlob
import pandas as pd
from datetime import datetime, timedelta, date

# --- CONFIGURATION ---
# You will need a free API key from https://newsapi.org/
API_KEY = 'c85bd651b9c24f97918f8c85ddc4a36f' 

# "Wire Services" are generally considered the most neutral/unbiased
NEUTRAL_SOURCES = [
    'reuters', 
    'associated-press', 
    'bloomberg', 
    'axios', 
    'politico'
]

# --- FUNCTIONS ---

def fetch_news(query, sources, from_date, to_date):
    """Fetches news from the selected sources for a specific topic and date range."""
    
    url = "https://newsapi.org/v2/everything"
    
    params = {
        'q': query if query else 'general',  # Topic
        'sources': ','.join(sources),        # Comma-separated sources
        'from': from_date.strftime('%Y-%m-%d'),
        'to': to_date.strftime('%Y-%m-%d'),
        'language': 'en',
        'sortBy': 'publishedAt', # Asks API for newest first
        'apiKey': API_KEY
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if data['status'] == 'ok':
            articles = data['articles']
            # DOUBLE CHECK SORTING: Ensure most recent is first (descending order)
            articles.sort(key=lambda x: x['publishedAt'], reverse=True)
            return articles
        else:
            st.error(f"Error fetching news: {data.get('message', 'Unknown error')}")
            return []
    except Exception as e:
        st.error(f"Connection error: {e}")
        return []

def analyze_sentiment(text):
    """
    Returns a 'Subjectivity' score (0.0 to 1.0).
    0.0 is very objective (fact-based).
    1.0 is very subjective (opinion/emotion-based).
    """
    blob = TextBlob(text)
    return blob.sentiment.subjectivity, blob.sentiment.polarity

# --- APP LAYOUT ---

st.set_page_config(page_title="Pure News Feed", page_icon="📰", layout="centered")

# Custom CSS to strip away "web app" feel and make it look like paper
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .reportview-container {
        background: #f0f2f6;
    }
    .headline {
        font-family: 'Georgia', serif;
        font-size: 22px;
        font-weight: bold;
        color: #2c3e50;
        text-decoration: none;
    }
    .metadata {
        font-family: 'Arial', sans-serif;
        font-size: 12px;
        color: #7f8c8d;
    }
    .neutral { border-left: 5px solid #2ecc71; padding-left: 10px; }
    .emotional { border-left: 5px solid #e74c3c; padding-left: 10px; }
    </style>
""", unsafe_allow_html=True)

st.title("📰 The Wire")
st.caption("No algorithms. No comments. Just headlines.")

# --- SIDEBAR CONTROLS ---

with st.sidebar:
    st.header("Filters")
    
    # Topic Input
    user_topic = st.text_input("Topic / Trend", value="Technology")
    
    # --- NEW: DATE RANGE SELECTOR ---
    st.subheader("Timeframe")
    today = date.today()
    last_week = today - timedelta(days=7)
    
    # Date Input returns a tuple (start, end)
    date_range = st.date_input(
        "Select Date Range",
        value=(last_week, today),
        min_value=today - timedelta(days=29), # NewsAPI Free tier limit is usually ~1 month
        max_value=today
    )
    
    # Handle the date range tuple logic
    if len(date_range) == 2:
        start_date, end_date = date_range
    else:
        # If user is in the middle of picking dates, just use today for both to prevent errors
        start_date, end_date = today, today

    # Source Selection
    st.subheader("Trusted Sources")
    st.info("Defaulted to Wire Services for minimal bias.")
    selected_sources = st.multiselect(
        "Select Sources:",
        options=['reuters', 'associated-press', 'bloomberg', 'the-verge', 'bbc-news', 'al-jazeera-english'],
        default=['reuters', 'associated-press', 'bloomberg', 'the-verge', 'bbc-news', 'al-jazeera-english']
    )
    
    # Emotional Filtering
    st.subheader("Sensationalism Filter")
    hide_emotional = st.checkbox("Hide emotionally charged headlines?")
    
    if st.button("Refresh Feed"):
        st.rerun()

# --- MAIN FEED ---

if not API_KEY or API_KEY == 'YOUR_NEWSAPI_KEY_HERE':
    st.warning("⚠️ Please enter a valid NewsAPI key in the code to start.")
else:
    with st.spinner(f"Fetching wire updates for '{user_topic}' from {start_date} to {end_date}..."):
        
        # Pass the specific dates to the function
        articles = fetch_news(user_topic, selected_sources, start_date, end_date)
        
        if not articles:
            st.info("No articles found in this date range. Try broadening the search.")
        
        for article in articles:
            title = article['title']
            source = article['source']['name']
            url = article['url']
            published = article['publishedAt'][:10] # Extract YYYY-MM-DD
            description = article['description']
            
            # Skip removed content
            if title == "[Removed]":
                continue

            # Analyze Tone
            subjectivity, polarity = analyze_sentiment(title + " " + (description or ""))
            
            # Determine if we show it
            is_emotional = subjectivity > 0.5
            
            if hide_emotional and is_emotional:
                continue
                
            # Render Article
            css_class = "emotional" if is_emotional else "neutral"
            emotional_label = "⚠️ Opinion/High Emotion" if is_emotional else "✅ Objective Tone"
            
            st.markdown(f"""
            <div class="{css_class}" style="background-color: white; padding: 15px; border-radius: 5px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <a href="{url}" target="_blank" class="headline">{title}</a>
                <br><br>
                <div class="metadata">
                    <b>{source}</b> | {published} | <span style="color: {'#e74c3c' if is_emotional else '#27ae60'}">{emotional_label}</span>
                </div>
                <p style="font-family: Arial; font-size: 14px; margin-top: 10px; color: #34495e;">
                    {description if description else ''}
                </p>
            </div>
            """, unsafe_allow_html=True)