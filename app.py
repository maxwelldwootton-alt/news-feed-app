import streamlit as st
import requests
from textblob import TextBlob
from datetime import datetime, timedelta, date

# --- CONFIGURATION ---
API_KEY = '68bf6222804f431d9f3697e73d759099' 

# Map the API 'slugs' to clean Display Names
SOURCE_MAPPING = {
    'reuters': 'Reuters',
    'associated-press': 'Associated Press',
    'bloomberg': 'Bloomberg',
    'axios': 'Axios',
    'politico': 'Politico',
    'the-verge': 'The Verge',
    'bbc-news': 'BBC News',
    'al-jazeera-english': 'Al Jazeera'
}

# Reverse Mapping (Display Name -> Slug)
REVERSE_MAPPING = {v: k for k, v in SOURCE_MAPPING.items()}

# Default neutral list
NEUTRAL_SOURCES = [
    'reuters', 'associated-press', 'bloomberg', 'axios', 'politico'
]

# --- INITIALIZE SESSION STATE ---
# This controls the "Applied" state (what the feed is actually showing)
if 'applied_topic' not in st.session_state:
    st.session_state.applied_topic = "Technology"
    st.session_state.applied_start_date = date.today() - timedelta(days=7)
    st.session_state.applied_end_date = date.today()
    st.session_state.applied_sources = NEUTRAL_SOURCES + ['the-verge', 'bbc-news', 'al-jazeera-english']
    st.session_state.applied_emotional = True

# --- FUNCTIONS ---
def fetch_news(query, sources, from_date, to_date):
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
        return []
    except:
        return []

def analyze_sentiment(text):
    blob = TextBlob(text)
    return blob.sentiment.subjectivity, blob.sentiment.polarity

# --- APP CONFIGURATION ---
st.set_page_config(page_title="Pure News Feed", page_icon="📰", layout="centered")

# --- CSS STYLING (Dark Mode + Blue Theme) ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Card Styles */
    .headline { 
        font-family: 'Georgia', serif; 
        font-size: 22px; 
        font-weight: bold; 
        color: #E0E0E0; 
        text-decoration: none; 
        transition: color 0.2s;
    }
    .headline:hover {
        color: #3B82F6; 
    }
    .metadata { 
        font-family: 'Arial', sans-serif; 
        font-size: 12px; 
        color: #A0A0A0; 
    }
    .card-container {
        background-color: #262730; 
        padding: 15px; 
        border-radius: 8px; 
        margin-bottom: 20px; 
        border: 1px solid #363636;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    
    /* Button Transition */
    section[data-testid="stSidebar"] .stButton button {
        width: 100%;
        border-radius: 5px;
        transition: background-color 0.3s ease;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📰 The Wire")
st.caption("No algorithms. No comments. Just headlines.")

# --- SIDEBAR CONTROLS ---

with st.sidebar:
    st.header("Filters")
    
    # --- 1. TOPIC SELECTION ---
    SUGGESTED_TOPICS = ["Technology", "Artificial Intelligence", "Stock Market", "Crypto", "Politics", "Space Exploration"]

    # Initialize Defaults: Technology selected, Search box empty
    if "topic_pills" not in st.session_state:
        st.session_state.topic_pills = "Technology"
    if "custom_search" not in st.session_state:
        st.session_state.custom_search = ""

    # Callback: If Pill clicked -> Clear Text Input
    def on_pill_change():
        if st.session_state.topic_pills:
            st.session_state.custom_search = ""
            
    # Callback: If Text typed -> Deselect Pill
    def on_text_change():
        if st.session_state.custom_search:
            st.session_state.topic_pills = None

    st.pills(
        "Trending now:",
        options=SUGGESTED_TOPICS,
        key="topic_pills",
        on_change=on_pill_change,
        selection_mode="single"
    )

    st.text_input(
        "Or search custom topic:", 
        key="custom_search",
        on_change=on_text_change
    )
    
    # Logic: Decide which topic to use for the API
    if st.session_state.custom_search:
        current_topic = st.session_state.custom_search
    elif st.session_state.topic_pills:
        current_topic = st.session_state.topic_pills
    else:
        current_topic = "Technology" # Fallback if user clears everything
    
    st.divider()

    # --- 2. TIMEFRAME ---
    st.subheader("Timeframe")
    today = date.today()
    current_date_range = st.date_input(
        "Select Date Range",
        value=(today - timedelta(days=7), today),
        min_value=today - timedelta(days=29),
        max_value=today,
        format="MM/DD/YYYY"
    )
    if len(current_date_range) == 2:
        current_start, current_end = current_date_range
    else:
        current_start, current_end = today, today

    # --- 3. SOURCES ---
    st.subheader("Trusted Sources")
    display_names = list(SOURCE_MAPPING.values())
    
    selected_display_names = st.pills(
        "Toggle sources:",
        options=display_names,
        default=display_names,
        selection_mode="multi"
    )
    
    if selected_display_names:
        current_sources = [REVERSE_MAPPING[name] for name in selected_display_names]
    else:
        current_sources = []
    
    # --- 4. SENSATIONALISM FILTER ---
    st.subheader("Sensationalism Filter")
    current_emotional = st.checkbox("Hide emotionally charged headlines?", value=True)
    
    # --- DETECT CHANGES ---
    has_changes = False
    if (current_topic != st.session_state.applied_topic or
        current_start != st.session_state.applied_start_date or
        current_end != st.session_state.applied_end_date or
        set(current_sources) != set(st.session_state.applied_sources) or
        current_emotional != st.session_state.applied_emotional):
        has_changes = True

    # --- RENDER REFRESH BUTTON ---
    if st.button("Refresh Feed"):
        st.session_state.applied_topic = current_topic
        st.session_state.applied_start_date = current_start
        st.session_state.applied_end_date = current_end
        st.session_state.applied_sources = current_sources
        st.session_state.applied_emotional = current_emotional
        st.rerun()

    # --- DYNAMIC CSS (Modern Blue) ---
    if has_changes:
        st.markdown("""
            <style>
            section[data-testid="stSidebar"] .stButton button {
                background-color: #3B82F6 !important;
                color: white !important;
                border: 1px solid #2563EB !important;
            }
            </style>
        """, unsafe_allow_html=True)

# --- MAIN FEED ---

if not API_KEY or API_KEY == 'YOUR_NEWSAPI_KEY_HERE':
    st.warning("⚠️ Please enter a valid NewsAPI key.")
else:
    if not st.session_state.applied_sources:
        st.warning("⚠️ Please select at least one source in the sidebar.")
    else:
        with st.spinner(f"Fetching wire updates for '{st.session_state.applied_topic}'..."):
            articles = fetch_news(
                st.session_state.applied_topic, 
                st.session_state.applied_sources, 
                st.session_state.applied_start_date, 
                st.session_state.applied_end_date
            )
            
            count = 0
            if not articles:
                st.info("No articles found.")
                
            for article in articles:
                title = article['title']
                if title == "[Removed]": continue
                
                # Date Formatting
                iso_date = article['publishedAt'][:10]
                date_obj = datetime.strptime(iso_date, '%Y-%m-%d')
                published_formatted = date_obj.strftime('%m/%d/%Y')
                
                # Source Formatting
                api_source_name = article['source']['name']
                api_source_id = article['source']['id'] 
                display_source = SOURCE_MAPPING.get(api_source_id, api_source_name)

                description = article['description']
                subjectivity, polarity = analyze_sentiment(title + " " + (description or ""))
                
                is_emotional = subjectivity > 0.5
                
                if st.session_state.applied_emotional and is_emotional:
                    continue
                
                count += 1
                css_class = "emotional" if is_emotional else "neutral"
                emotional_label = "⚠️ Opinion/High Emotion" if is_emotional else "✅ Objective Tone"
                emotional_color = "#ef4444" if is_emotional else "#2ecc71" # Red vs Green
                
                # Dark Mode Card HTML
                st.markdown(f"""
                <div class="card-container {css_class}">
                    <a href="{article['url']}" target="_blank" class="headline">{title}</a>
                    <br><br>
                    <div class="metadata">
                        <b>{display_source}</b> | {published_formatted} | <span style="color: {emotional_color}">{emotional_label}</span>
                    </div>
                    <p style="font-family: Arial; font-size: 14px; margin-top: 10px; color: #D1D5DB;">
                        {description if description else ''}
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
            if count == 0 and articles:
                st.warning("Articles found, but all were filtered by the 'Sensationalism Filter'.")