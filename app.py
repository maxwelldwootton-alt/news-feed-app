import streamlit as st
import requests
from textblob import TextBlob
import pandas as pd
from datetime import datetime, timedelta

# --- CONFIGURATION ---
# You will need a free API key from https://newsapi.org/
# In a real app, use environment variables. For this script, paste it below.
API_KEY = 'c85bd651b9c24f97918f8c85ddc4a36f' 

# "Wire Services" are generally considered the most neutral/unbiased
# because they sell facts to other news agencies.
NEUTRAL_SOURCES = [
    'reuters', 
    'associated-press', 
    'bloomberg', 
    'axios', 
    'politico'
]

# --- FUNCTIONS ---

def fetch_news(query, sources, days_ago=1):
    """Fetches news from the selected sources for a specific topic."""
    
    # Calculate date range
    from_date = (datetime.now() - timedelta(days=days_ago)).strftime('%Y-%m-%d')
    
    url = "https://newsapi.org/v2/everything"
    
    params = {
        'q': query if query else 'general',  # Topic
        'sources': ','.join(sources),        # Comma-separated sources
        'from': from_date,
        'language': 'en',
        'sortBy': 'publishedAt',
        'apiKey': API_KEY
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if data['status'] == 'ok':
            return data['articles']
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
    with st.spinner(f"Fetching wire updates for '{user_topic}'..."):
        articles = fetch_news(user_topic, selected_sources)
        
        if not articles:
            st.info("No recent articles found. Try a broader topic or more sources.")
        
        for article in articles:
            title = article['title']
            source = article['source']['name']
            url = article['url']
            published = article['publishedAt'][:10]
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

