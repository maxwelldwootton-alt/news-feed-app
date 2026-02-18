import streamlit as st
import requests
from textblob import TextBlob
from datetime import datetime, timedelta, date

# --- CONFIGURATION ---
# ⚠️ REPLACE THIS WITH YOUR ACTUAL KEY OR USE st.secrets["NEWS_API_KEY"]
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
if 'applied_topic' not in st.session_state:
    st.session_state.applied_topic = "Technology"
    st.session_state.applied_start_date = date.today() - timedelta(days=7)
    st.session_state.applied_end_date = date.today()
    st.session_state.applied_sources = NEUTRAL_SOURCES + ['the-verge', 'bbc-news', 'al-jazeera-english']
    st.session_state.applied_emotional = True

# --- FUNCTIONS ---

# OPTIMIZATION: Cache set to 1 hour (3600s) to save API calls.
@st.cache_data(ttl=3600, show_spinner=False) 
def fetch_news(query, sources, from_date, to_date, api_key):
    url = "https://newsapi.org/v2/everything"
    
    if sources:
        sources.sort()
        
    params = {
        'q': query if query else 'general',
        'sources': ','.join(sources),
        'from': from_date.strftime('%Y-%m-%d'),
        'to': to_date.strftime('%Y-%m-%d'),
        'language': 'en',
        'sortBy': 'publishedAt',
        'pageSize': 100,  # ALWAYS fetch max (100) to get the most value per credit
        'apiKey': api_key
    }
    try:
        response = requests.get(url, params=params)
        data = response.json()
        
        if data.get('status') == 'ok':
            articles = data['articles']
            valid_articles = [a for a in articles if a['title'] != "[Removed]"]
            valid_articles.sort(key=lambda x: x['publishedAt'], reverse=True)
            return valid_articles
            
        return []
    except Exception as e:
        return []

def analyze_sentiment(text):
    blob = TextBlob(text)
    return blob.sentiment.subjectivity, blob.sentiment.polarity

# --- APP CONFIGURATION ---
st.set_page_config(page_title="The Wire", page_icon="📰", layout="centered")

# --- CSS STYLING ---
st.markdown("""
    <style>
    /* IMPORT GOOGLE FONTS */
    @import url('https://fonts.googleapis.com/css2?family=Merriweather:ital,wght@0,300;0,400;0,700;0,900;1,300;1,400&family=Inter:wght@300;400;500;600&display=swap');

    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* --- Card Container & Hover Effects --- */
    .card-container {
        background-color: #262730; 
        padding: 24px; 
        border-radius: 12px;
        margin-bottom: 20px; 
        border: 1px solid #363636;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        transition: all 0.3s ease;
    }
    
    .card-container:hover {
        background-color: #2E2F38; 
        border-color: #3B82F6;     
        box-shadow: 0 8px 15px rgba(0,0,0,0.3); 
        transform: translateY(-3px); 
    }

    /* --- FLEX LAYOUT FOR IMAGE & TEXT --- */
    .card-content {
        display: flex;
        justify-content: space-between;
        align-items: flex-start;
        gap: 20px;
    }

    .text-column {
        flex: 1; /* Takes up all remaining space */
        min-width: 0; /* Prevents text from overflowing */
    }

    .img-column img {
        width: 120px;
        height: 120px;
        object-fit: cover;
        border-radius: 8px;
        border: 1px solid #444;
        flex-shrink: 0; /* Prevents image from squishing */
    }
    
    /* Headline Styling */
    .headline { 
        display: block; 
        font-family: 'Merriweather', serif; 
        font-size: 24px; 
        font-weight: 700; 
        color: #E0E0E0; 
        text-decoration: none; 
        line-height: 1.4;
        transition: color 0.2s;
        letter-spacing: -0.3px;
        margin-bottom: 8px;
    }
    
    .card-container:hover .headline {
         color: #60A5FA; 
    }
    
    /* Metadata Container */
    .metadata { 
        display: flex;
        align-items: center;
        flex-wrap: wrap;
        gap: 10px;
        font-family: 'Inter', sans-serif; 
        font-size: 12px; 
        color: #A0A0A0; 
    }
    
    /* CHIP STYLES */
    .chip {
        display: inline-flex;
        align-items: center;
        padding: 4px 10px;
        border-radius: 6px; 
        font-size: 11px;
        font-family: 'Inter', sans-serif;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 0.5px;
        color: white;
    }
    
    .chip-source {
        background-color: #374151; 
        color: #E5E7EB;
        border: 1px solid #4B5563;
    }
    
    .chip-neutral {
        background-color: #059669; 
        border: 1px solid #10B981;
    }
    
    .chip-emotional {
        background-color: #DC2626; 
        border: 1px solid #EF4444;
    }

    /* Description Text */
    .description-text {
        font-family: 'Inter', sans-serif;
        font-size: 15px;
        margin-top: 14px;
        color: #D1D5DB;
        line-height: 1.6;
        font-weight: 300;
    }
    
    /* Sidebar Button Styling */
    section[data-testid="stSidebar"] .stButton button {
        width: 100%;
        border-radius: 5px;
        transition: background-color 0.3s ease;
        font-family: 'Inter', sans-serif;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📰 The Wire")
st.caption("No algorithms. No comments. Just headlines.")

# --- SIDEBAR CONTROLS ---

with st.sidebar:
    st.header("Filters")
    
    # --- 1. TOPIC SELECTION ---
    # Added 'Nuclear' to the list
    SUGGESTED_TOPICS = ["Technology", "Artificial Intelligence", "Stock Market", "Crypto", "Politics", "Nuclear", "Space Exploration"]

    if "topic_pills" not in st.session_state:
        st.session_state.topic_pills = "Technology"
    if "custom_search" not in st.session_state:
        st.session_state.custom_search = ""

    def on_pill_change():
        if st.session_state.topic_pills:
            st.session_state.custom_search = ""
            
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
    
    if st.session_state.custom_search:
        current_topic = st.session_state.custom_search
    elif st.session_state.topic_pills:
        current_topic = st.session_state.topic_pills
    else:
        current_topic = "Technology"
    
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

    # --- REFRESH BUTTON ---
    if st.button("Refresh Feed"):
        st.session_state.applied_topic = current_topic
        st.session_state.applied_start_date = current_start
        st.session_state.applied_end_date = current_end
        st.session_state.applied_sources = current_sources
        st.session_state.applied_emotional = current_emotional
        st.rerun()

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
    st.warning("⚠️ Please enter a valid NewsAPI key in the code configuration.")
else:
    if not st.session_state.applied_sources:
        st.warning("⚠️ Please select at least one source in the sidebar.")
    else:
        with st.spinner(f"Fetching wire updates for '{st.session_state.applied_topic}'..."):
            articles = fetch_news(
                st.session_state.applied_topic, 
                st.session_state.applied_sources, 
                st.session_state.applied_start_date, 
                st.session_state.applied_end_date,
                API_KEY
            )
            
            count = 0
            if not articles:
                st.info("No articles found for this topic/timeframe.")
                
            for article in articles:
                title = article['title']
                url = article['url']
                image_url = article.get('urlToImage')
                
                # Date Formatting
                iso_date = article['publishedAt'][:10]
                date_obj = datetime.strptime(iso_date, '%Y-%m-%d')
                published_formatted = date_obj.strftime('%b %d, %Y')
                
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
                
                # Determine Chips
                source_chip = f'<span class="chip chip-source">{display_source}</span>'
                
                if is_emotional:
                    sentiment_chip = '<span class="chip chip-emotional">⚠️ High Emotion</span>'
                else:
                    sentiment_chip = '<span class="chip chip-neutral">✅ Objective</span>'
                
                # Build Image HTML (Only if exists)
                img_html = ""
                if image_url:
                    img_html = f"""
                    <div class="img-column">
                        <img src="{image_url}" alt="Thumbnail">
                    </div>
                    """
                
                # HTML Card Structure
                st.markdown(f"""
                <div class="card-container">
                    <div class="card-content">
                        <div class="text-column">
                            <a href="{url}" target="_blank" class="headline">{title}</a>
                            <div class="metadata">
                                {source_chip}
                                <span style="color: #6B7280; font-weight: bold;">•</span>
                                {sentiment_chip}
                                <span style="color: #6B7280; font-weight: bold;">•</span>
                                <span>{published_formatted}</span>
                            </div>
                            <p class="description-text">
                                {description if description else ''}
                            </p>
                        </div>
                        {img_html}
                    </div>
                </div>
                """, unsafe_allow_html=True)
                
            if count == 0 and articles:
                st.warning("Articles found, but all were filtered by the 'Sensationalism Filter'. Try unchecking the filter in the sidebar.")