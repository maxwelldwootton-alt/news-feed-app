import streamlit as st
import requests
from textblob import TextBlob
import pandas as pd
from datetime import datetime, timedelta, date

# --- CONFIGURATION ---
API_KEY = 'c85bd651b9c24f97918f8c85ddc4a36f' 

NEUTRAL_SOURCES = [
    'reuters', 'associated-press', 'bloomberg', 'axios', 'politico'
]

# --- INITIALIZE SESSION STATE ---
# This ensures the feed only updates when the button is clicked,
# and allows us to detect "changes" to turn the button green.

if 'applied_topic' not in st.session_state:
    st.session_state.applied_topic = "Technology"
    st.session_state.applied_start_date = date.today() - timedelta(days=7)
    st.session_state.applied_end_date = date.today()
    st.session_state.applied_sources = NEUTRAL_SOURCES + ['the-verge', 'bbc-news', 'al-jazeera-english']
    st.session_state.applied_emotional = True  # Default enabled

# --- FUNCTIONS ---

def fetch_news(query, sources, from_date, to_date):
    """Fetches news using the APPLIED filters."""
    url = "https://newsapi.org/v2/everything"
    params = {
        'q': query if query else 'general',
        'sources': ','.join(sources),
        'from': from_date.strftime('%Y-%m-%d'),
        'to': to_date.strftime('%Y-%m-%d'),
        'language': 'en',
        'sortBy': 'publishedAt',
        'apiKey': API_KEY
    }
    
    try:
        response = requests.get(url, params=params)
        data = response.json()
        if data['status'] == 'ok':
            articles = data['articles']
            articles.sort(key=lambda x: x['publishedAt'], reverse=True)
            return articles
        else:
            st.error(f"Error fetching news: {data.get('message', 'Unknown error')}")
            return []
    except Exception as e:
        st.error(f"Connection error: {e}")
        return []

def analyze_sentiment(text):
    blob = TextBlob(text)
    return blob.sentiment.subjectivity, blob.sentiment.polarity

# --- APP LAYOUT ---

st.set_page_config(page_title="Pure News Feed", page_icon="📰", layout="centered")

st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .reportview-container { background: #f0f2f6; }
    .headline { font-family: 'Georgia', serif; font-size: 22px; font-weight: bold; color: #2c3e50; text-decoration: none; }
    .metadata { font-family: 'Arial', sans-serif; font-size: 12px; color: #7f8c8d; }
    .neutral { border-left: 5px solid #2ecc71; padding-left: 10px; }
    .emotional { border-left: 5px solid #e74c3c; padding-left: 10px; }
    
    /* CSS for the Green "Ready to Refresh" Button */
    .stButton button.green-button {
        background-color: #2ecc71 !important;
        color: white !important;
        border: 1px solid #27ae60 !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📰 The Wire")
st.caption("No algorithms. No comments. Just headlines.")

# --- SIDEBAR CONTROLS ---

with st.sidebar:
    st.header("Filters")
    
    # 1. Inputs (User changes these, but they don't update feed yet)
    current_topic = st.text_input("Topic / Trend", value="Technology")
    
    st.subheader("Timeframe")
    today = date.today()
    current_date_range = st.date_input(
        "Select Date Range",
        value=(today - timedelta(days=7), today),
        min_value=today - timedelta(days=29),
        max_value=today
    )
    # Handle tuple unpacking safely
    if len(current_date_range) == 2:
        current_start, current_end = current_date_range
    else:
        current_start, current_end = today, today

    st.subheader("Trusted Sources")
    all_options = ['reuters', 'associated-press', 'bloomberg', 'the-verge', 'bbc-news', 'al-jazeera-english']
    current_sources = st.multiselect(
        "Select Sources:",
        options=all_options,
        default=all_options
    )
    
    st.subheader("Sensationalism Filter")
    current_emotional = st.checkbox("Hide emotionally charged headlines?", value=True)
    
    # 2. Detect Changes
    # We compare the "Current" sidebar values with the "Applied" session state values
    has_changes = False
    if (current_topic != st.session_state.applied_topic or
        current_start != st.session_state.applied_start_date or
        current_end != st.session_state.applied_end_date or
        set(current_sources) != set(st.session_state.applied_sources) or
        current_emotional != st.session_state.applied_emotional):
        has_changes = True

    # 3. Dynamic Button Styling
    # If changes are detected, we inject CSS to turn the button green
    if has_changes:
        st.markdown("""
            <style>
            div[data-testid="stButton"] > button {
                background-color: #2ecc71 !important;
                color: white !important;
                border: none !important;
                box-shadow: 0 4px 6px rgba(0,0,0,0.2);
            }
            div[data-testid="stButton"] > button:hover {
                 background-color: #27ae60 !important;
                 color: white !important;
            }
            </style>
        """, unsafe_allow_html=True)
        button_label = "Refresh Feed"
    else:
        button_label = "Refresh Feed"

    # 4. Button Logic
    if st.button(button_label):
        # Update the Session State with the new values
        st.session_state.applied_topic = current_topic
        st.session_state.applied_start_date = current_start
        st.session_state.applied_end_date = current_end
        st.session_state.applied_sources = current_sources
        st.session_state.applied_emotional = current_emotional
        
        # Rerun to clear the "has_changes" flag and update the feed
        st.rerun()

# --- MAIN FEED ---
# Uses st.session_state variables so the feed acts "frozen" until button click

if not API_KEY or API_KEY == 'YOUR_NEWSAPI_KEY_HERE':
    st.warning("⚠️ Please enter a valid NewsAPI key.")
else:
    with st.spinner(f"Fetching wire updates for '{st.session_state.applied_topic}'..."):
        
        articles = fetch_news(
            st.session_state.applied_topic, 
            st.session_state.applied_sources, 
            st.session_state.applied_start_date, 
            st.session_state.applied_end_date
        )
        
        if not articles:
            st.info("No articles found for these filters.")
        
        count = 0
        for article in articles:
            title = article['title']
            if title == "[Removed]": continue
            
            description = article['description']
            subjectivity, polarity = analyze_sentiment(title + " " + (description or ""))
            is_emotional = subjectivity > 0.5
            
            # Use SESSION STATE filter
            if st.session_state.applied_emotional and is_emotional:
                continue
            
            count += 1
            css_class = "emotional" if is_emotional else "neutral"
            emotional_label = "⚠️ Opinion/High Emotion" if is_emotional else "✅ Objective Tone"
            
            st.markdown(f"""
            <div class="{css_class}" style="background-color: white; padding: 15px; border-radius: 5px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                <a href="{article['url']}" target="_blank" class="headline">{title}</a>
                <br><br>
                <div class="metadata">
                    <b>{article['source']['name']}</b> | {article['publishedAt'][:10]} | <span style="color: {'#e74c3c' if is_emotional else '#27ae60'}">{emotional_label}</span>
                </div>
                <p style="font-family: Arial; font-size: 14px; margin-top: 10px; color: #34495e;">
                    {description if description else ''}
                </p>
            </div>
            """, unsafe_allow_html=True)
            
        if count == 0 and articles:
            st.warning("Articles found, but all were filtered by the 'Sensationalism Filter'.")