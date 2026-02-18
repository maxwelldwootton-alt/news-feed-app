import streamlit as st
import requests
from textblob import TextBlob
from datetime import datetime, timedelta, date
import google.generativeai as genai

# --- CONFIGURATION ---
# 🔒 Pulling keys securely from Streamlit Secrets
NEWS_API_KEY = st.secrets["NEWS_API_KEY"]
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

# Initialize Gemini
genai.configure(api_key=GEMINI_API_KEY)

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
REVERSE_MAPPING = {v: k for k, v in SOURCE_MAPPING.items()}
NEUTRAL_SOURCES = ['reuters', 'associated-press', 'bloomberg', 'axios', 'politico']

DEFAULT_TOPICS = [
    "Technology", "Artificial Intelligence", "Stock Market", "Crypto", 
    "Politics", "Epstein Files", "Nuclear", "Space Exploration"
]

# --- KEYWORD MATCHING ENGINE ---
TOPIC_KEYWORDS = {
    "Technology": ["tech", "software", "hardware", "apple", "google", "microsoft", "internet", "device", "silicon", "meta", "amazon", "server", "cyber", "data", "app", "mobile", "ios", "android"],
    "Artificial Intelligence": ["ai", "artificial intelligence", "llm", "gpt", "openai", "machine learning", "neural", "nvidia", "altman", "chatbot", "generative"],
    "Stock Market": ["stock", "market", "dow", "nasdaq", "s&p", "economy", "rate", "fed", "trading", "investor", "bull", "bear", "wall st", "ipo", "shares", "revenue", "profit", "quarterly"],
    "Crypto": ["crypto", "bitcoin", "btc", "ethereum", "blockchain", "token", "coinbase", "binance", "wallet", "web3", "defi"],
    "Politics": ["politics", "biden", "trump", "congress", "senate", "law", "election", "campaign", "white house", "democrat", "republican", "gop", "bill", "vote", "voter"],
    "Epstein Files": ["epstein", "ghislaine", "maxwell", "document", "court", "list", "judge", "testimony", "deposition"],
    "Nuclear": ["nuclear", "atomic", "uranium", "fusion", "fission", "reactor", "plant", "energy", "radiation"],
    "Space Exploration": ["space", "nasa", "spacex", "moon", "mars", "orbit", "galaxy", "rocket", "launch", "satellite", "astronaut", "universe"]
}

# --- INITIALIZE SESSION STATE ---
if 'saved_custom_topics' not in st.session_state:
    st.session_state.saved_custom_topics = []

if 'active_default' not in st.session_state:
    st.session_state.active_default = DEFAULT_TOPICS.copy()

if 'active_custom' not in st.session_state:
    st.session_state.active_custom = []

if 'applied_start_date' not in st.session_state:
    yesterday = date.today() - timedelta(days=1)
    st.session_state.applied_start_date = yesterday
    st.session_state.applied_end_date = yesterday
    st.session_state.applied_sources = NEUTRAL_SOURCES + ['the-verge', 'bbc-news', 'al-jazeera-english']
    st.session_state.applied_emotional = True

# --- FUNCTIONS ---
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
        'pageSize': 100,
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
    except Exception:
        return []

def analyze_sentiment(text):
    blob = TextBlob(text)
    return blob.sentiment.subjectivity, blob.sentiment.polarity

def classify_article(text, active_defaults, active_customs):
    found_tags = []
    text_lower = text.lower()
    
    for topic in active_defaults:
        keywords = TOPIC_KEYWORDS.get(topic, [topic.lower()])
        if topic.lower() not in keywords:
            keywords.append(topic.lower())
        for k in keywords:
            if k in text_lower:
                found_tags.append(topic)
                break 
    
    for topic in active_customs:
        if topic.lower() in text_lower:
            found_tags.append(topic)
            
    return list(dict.fromkeys(found_tags))

@st.cache_data(show_spinner=False)
def get_gemini_summary(prompt_data_string):
    if not prompt_data_string.strip():
        return "No articles available to summarize."
    try:
        model = genai.GenerativeModel('gemini-3-flash-preview')
        prompt = f'''You are a professional news briefing assistant. 
I am providing you with a list of current news articles. Each article includes its assigned Categories, Title, and Description.
Please provide a well-structured, easy-to-read summary of the news, grouping the insights by Category. 
Keep it engaging, objective, and concise. Use markdown formatting (headers, bullet points) for readability.

Here is the news data:
{prompt_data_string}
'''
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        return f"⚠️ An error occurred while generating the AI Overview: {e}"

# --- CALLBACKS ---
def add_custom_topic():
    raw_query = st.session_state.search_input.strip()
    if raw_query:
        new_topic = raw_query.title()
        # Explicit list reassignment forces Streamlit to update the widget UI perfectly
        if new_topic not in st.session_state.saved_custom_topics:
            st.session_state.saved_custom_topics = [new_topic] + st.session_state.saved_custom_topics
        if new_topic not in st.session_state.active_custom:
            st.session_state.active_custom = st.session_state.active_custom + [new_topic]
    st.session_state.search_input = ""

# --- APP CONFIGURATION ---
st.set_page_config(page_title="The Wire", page_icon="📰", layout="centered")

# --- CSS STYLING ---
st.markdown('''
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Merriweather:ital,wght@0,300;0,400;0,700;0,900;1,300;1,400&family=Inter:wght@300;400;500;600&display=swap');
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    * { word-wrap: break-word; overflow-wrap: break-word; }
    .block-container { overflow-x: hidden; }

    .card-container {
        background-color: #262730; padding: 24px; border-radius: 12px;
        margin-bottom: 20px; border: 1px solid #363636;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2); transition: all 0.3s ease;
        width: 100%; box-sizing: border-box; overflow: hidden; 
    }
    .card-container:hover {
        background-color: #2E2F38; border-color: #3B82F6;     
        box-shadow: 0 8px 15px rgba(0,0,0,0.3); transform: translateY(-3px); 
    }
    .card-content { display: flex; justify-content: space-between; align-items: center; gap: 20px; }
    .text-column { flex: 1; min-width: 0; } 
    .img-column img { width: 120px; height: 120px; object-fit: cover; border-radius: 8px; border: 1px solid #444; flex-shrink: 0; display: block; }
    
    @media (max-width: 768px) {
        .card-content { flex-direction: column-reverse; align-items: stretch; }
        .img-column { width: 100%; margin-bottom: 16px; }
        .img-column img { width: 100%; height: 180px; }
        .headline { font-size: 20px; }
    }
    
    .headline { 
        display: block; font-family: 'Merriweather', serif; font-size: 24px; 
        font-weight: 700; color: #E0E0E0; text-decoration: none; line-height: 1.4;
        transition: color 0.2s; letter-spacing: -0.3px; margin-bottom: 8px;
    }
    .card-container:hover .headline { color: #60A5FA; }
    .metadata { display: flex; align-items: center; flex-wrap: wrap; gap: 8px; font-family: 'Inter', sans-serif; font-size: 12px; color: #A0A0A0; }
    
    .chip { display: inline-flex; align-items: center; padding: 3px 8px; border-radius: 6px; font-size: 10px; font-family: 'Inter', sans-serif; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; color: white; }
    .chip-source { background-color: #374151; color: #E5E7EB; border: 1px solid #4B5563; }
    .chip-neutral { background-color: #059669; border: 1px solid #10B981; }
    .chip-emotional { background-color: #DC2626; border: 1px solid #EF4444; }
    .chip-category { background-color: transparent; color: #60A5FA; border: 1px solid #3B82F6; }
    
    .chip-overflow { 
        background-color: transparent; color: #9CA3AF; border: 1px dashed #4B5563;
        cursor: default; position: relative; display: inline-block;
    }
    .chip-overflow .tooltip-text {
        visibility: hidden; width: 140px; background-color: #1F2937; color: #F3F4F6;
        text-align: center; border-radius: 6px; padding: 6px 8px; position: absolute;
        z-index: 10; bottom: 135%; right: 0; opacity: 0; transition: opacity 0.2s;
        font-size: 11px; font-weight: 400; border: 1px solid #374151;
        box-shadow: 0 4px 10px rgba(0,0,0,0.5); pointer-events: none;
    }
    .chip-overflow .tooltip-text::after {
        content: ""; position: absolute; top: 100%; right: 15px; border-width: 5px;
        border-style: solid; border-color: #1F2937 transparent transparent transparent;
    }
    .chip-overflow:hover .tooltip-text, .chip-overflow:active .tooltip-text { visibility: visible; opacity: 1; }
    .description-text { font-family: 'Inter', sans-serif; font-size: 15px; margin-top: 14px; color: #D1D5DB; line-height: 1.6; font-weight: 300; }
    .stButton button { width: 100%; border-radius: 5px; font-family: 'Inter', sans-serif; }
    </style>
''', unsafe_allow_html=True)

st.title("📰 The Wire")
st.caption("No algorithms. No comments. Just headlines.")

col_search, col_edit = st.columns([4, 1])
with col_search:
    st.text_input("Add a custom feed:", key="search_input", on_change=add_custom_topic, placeholder="e.g. Nvidia, Bitcoin, Election...", label_visibility="collapsed")
with col_edit:
    is_edit_mode = st.toggle("Delete", key="edit_mode", help="Turn on to delete custom chips")

if st.session_state.saved_custom_topics:
    st.write("**My Feeds**")
    if is_edit_mode:
        st.warning("🗑️ **Delete Mode Active:** Uncheck to delete.")
        def on_delete_change():
            remaining = st.session_state.temp_delete_widget
            st.session_state.saved_custom_topics = remaining
            st.session_state.active_custom = [t for t in st.session_state.active_custom if t in remaining]
        st.pills("Delete", options=st.session_state.saved_custom_topics, default=st.session_state.saved_custom_topics, key="temp_delete_widget", on_change=on_delete_change, selection_mode="multi", label_visibility="collapsed")
    else:
        st.pills("My Feeds", options=st.session_state.saved_custom_topics, key="active_custom", selection_mode="multi", label_visibility="collapsed")

st.write("**Trending Topics**")
st.pills("Trending Topics", options=DEFAULT_TOPICS, key="active_default", selection_mode="multi", label_visibility="collapsed")

# --- STRICT ACTIVE QUERY BUILDER ---
# We ONLY query the API for chips that are currently checked. 
active_topics = st.session_state.active_default + st.session_state.active_custom
query_parts = []
for t in active_topics:
    part = f'"{t}"' if " " in t else t
    if len(" OR ".join(query_parts + [part])) < 450: 
        query_parts.append(part)

api_query = " OR ".join(query_parts) if query_parts else "General"

# --- SIDEBAR ---
with st.sidebar:
    st.header("Advanced Filters")
    today = date.today()
    yesterday = today - timedelta(days=1)
    current_date_range = st.date_input(
        "Select Date Range", 
        value=(yesterday, yesterday), 
        min_value=today - timedelta(days=29), 
        max_value=today, 
        format="MM/DD/YYYY"
    )
    
    if len(current_date_range) == 2:
        current_start, current_end = current_date_range
    elif len(current_date_range) == 1:
        current_start, current_end = current_date_range[0], current_date_range[0]
    else:
        current_start, current_end = yesterday, yesterday
    
    display_names = list(SOURCE_MAPPING.values())
    selected_display_names = st.pills("Toggle sources:", options=display_names, default=display_names, selection_mode="multi")
    current_sources = [REVERSE_MAPPING[name] for name in selected_display_names] if selected_display_names else []
    current_emotional = st.checkbox("Hide emotionally charged headlines?", value=True)
    if st.button("Update Timeframe/Sources", type="primary"):
         st.session_state.applied_start_date = current_start
         st.session_state.applied_end_date = current_end
         st.session_state.applied_sources = current_sources
         st.session_state.applied_emotional = current_emotional
         st.rerun()

st.divider