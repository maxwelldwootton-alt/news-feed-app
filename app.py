import streamlit as st
import requests
from textblob import TextBlob
from datetime import datetime, timedelta, date

# --- CONFIGURATION ---
# ⚠️ REPLACE THIS WITH YOUR ACTUAL KEY OR USE st.secrets["NEWS_API_KEY"]
API_KEY = '68bf6222804f431d9f3697e73d759099' 

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

# --- TOPICS CONFIGURATION ---
DEFAULT_TOPICS = [
    "Technology", 
    "Artificial Intelligence", 
    "Stock Market", 
    "Crypto", 
    "Politics", 
    "Epstein Files", 
    "Nuclear", 
    "Space Exploration"
]

# --- INITIALIZE SESSION STATE ---
# We store 'custom_topics' separately so we know which ones can be removed
if 'custom_topics' not in st.session_state:
    st.session_state.custom_topics = []

# This acts as the 'Master List' of what is currently checked in the UI
if 'selected_topics' not in st.session_state:
    st.session_state.selected_topics = DEFAULT_TOPICS.copy()

if 'applied_start_date' not in st.session_state:
    st.session_state.applied_start_date = date.today() - timedelta(days=7)
    st.session_state.applied_end_date = date.today()
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

# --- APP CONFIGURATION ---
st.set_page_config(page_title="The Wire", page_icon="📰", layout="centered")

# --- CSS STYLING ---
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Merriweather:ital,wght@0,300;0,400;0,700;0,900;1,300;1,400&family=Inter:wght@300;400;500;600&display=swap');
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Card Styles */
    .card-container {
        background-color: #262730; padding: 24px; border-radius: 12px;
        margin-bottom: 20px; border: 1px solid #363636;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2); transition: all 0.3s ease;
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
    
    .metadata { display: flex; align-items: center; flex-wrap: wrap; gap: 10px; font-family: 'Inter', sans-serif; font-size: 12px; color: #A0A0A0; }
    .chip { display: inline-flex; align-items: center; padding: 4px 10px; border-radius: 6px; font-size: 11px; font-family: 'Inter', sans-serif; font-weight: 600; text-transform: uppercase; letter-spacing: 0.5px; color: white; }
    .chip-source { background-color: #374151; color: #E5E7EB; border: 1px solid #4B5563; }
    .chip-neutral { background-color: #059669; border: 1px solid #10B981; }
    .chip-emotional { background-color: #DC2626; border: 1px solid #EF4444; }
    .description-text { font-family: 'Inter', sans-serif; font-size: 15px; margin-top: 14px; color: #D1D5DB; line-height: 1.6; font-weight: 300; }
    .stButton button { width: 100%; border-radius: 5px; font-family: 'Inter', sans-serif; }
    </style>
""", unsafe_allow_html=True)

st.title("📰 The Wire")
st.caption("No algorithms. No comments. Just headlines.")

# --- SEARCH LOGIC ---

# Callback to add new topics
def add_custom_topic():
    new_query = st.session_state.search_input.strip()
    if new_query:
        # 1. Add to Custom List (if not exist)
        if new_query not in st.session_state.custom_topics:
            st.session_state.custom_topics.append(new_query)
        # 2. Add to Selected List (so it appears active immediately)
        if new_query not in st.session_state.selected_topics:
            st.session_state.selected_topics.append(new_query)
    st.session_state.search_input = "" # Clear input

# 1. SEARCH BAR
st.text_input(
    "Search to add a topic:", 
    key="search_input",
    on_change=add_custom_topic,
    placeholder="e.g. Nvidia, Bitcoin, Election..."
)

# 2. CHIP DISPLAY
# Combine Default + Custom for the options list
# We reverse custom_topics so the newest ones appear first, next to the defaults
all_options = st.session_state.custom_topics + DEFAULT_TOPICS

st.pills(
    "Active Feeds (Deselect to remove):",
    options=all_options,
    key="selected_topics", # This automatically binds to st.session_state.selected_topics
    selection_mode="multi"
)

# 3. CLEANUP LOGIC (The "X" Behavior)
# If a custom topic is in 'custom_topics' but NOT in 'selected_topics', 
# it means the user clicked it to turn it off. We should remove it entirely.
items_to_remove = [t for t in st.session_state.custom_topics if t not in st.session_state.selected_topics]

if items_to_remove:
    for t in items_to_remove:
        st.session_state.custom_topics.remove(t)
    st.rerun() # Force refresh so the chip disappears visually

# --- QUERY BUILDING ---
if st.session_state.selected_topics:
    # Wrap multi-word topics in quotes for exact matching
    formatted_topics = [f'"{t}"' if " " in t else t for t in st.session_state.selected_topics]
    api_query = " OR ".join(formatted_topics)
else:
    api_query = "General" # Fallback

# --- SIDEBAR FILTERS ---
with st.sidebar:
    st.header("Advanced Filters")
    today = date.today()
    current_date_range = st.date_input("Select Date Range", value=(today - timedelta(days=7), today), min_value=today - timedelta(days=29), max_value=today, format="MM/DD/YYYY")
    if len(current_date_range) == 2:
        current_start, current_end = current_date_range
    else:
        current_start, current_end = today, today

    display_names = list(SOURCE_MAPPING.values())
    selected_display_names = st.pills("Toggle sources:", options=display_names, default=display_names, selection_mode="multi")
    if selected_display_names:
        current_sources = [REVERSE_MAPPING[name] for name in selected_display_names]
    else:
        current_sources = []
    
    current_emotional = st.checkbox("Hide emotionally charged headlines?", value=True)

    if st.button("Update Timeframe/Sources", type="primary"):
         st.session_state.applied_start_date = current_start
         st.session_state.applied_end_date = current_end
         st.session_state.applied_sources = current_sources
         st.session_state.applied_emotional = current_emotional
         st.rerun()

st.divider()

# --- MAIN FEED ---

if not API_KEY or API_KEY == 'YOUR_NEWSAPI_KEY_HERE':
    st.warning("⚠️ Please enter a valid NewsAPI key in the code configuration.")
else:
    if not st.session_state.applied_sources:
        st.warning("⚠️ Please select at least one source in the sidebar.")
    else:
        with st.spinner("Loading wire..."):
            # FETCH (Auto-cached if query string matches previous calls)
            articles = fetch_news(
                api_query, 
                st.session_state.applied_sources, 
                st.session_state.applied_start_date, 
                st.session_state.applied_end_date,
                API_KEY
            )
            
            count = 0
            if not articles:
                st.info("No articles found matching these topics.")
                
            for article in articles:
                title = article['title']
                url = article['url']
                image_url = article.get('urlToImage')
                
                iso_date = article['publishedAt'][:10]
                date_obj = datetime.strptime(iso_date, '%Y-%m-%d')
                published_formatted = date_obj.strftime('%b %d, %Y')
                
                api_source_name = article['source']['name']
                api_source_id = article['source']['id'] 
                display_source = SOURCE_MAPPING.get(api_source_id, api_source_name)

                description = article['description']
                subjectivity, polarity = analyze_sentiment(title + " " + (description or ""))
                
                is_emotional = subjectivity > 0.5
                
                if current_emotional and is_emotional:
                    continue
                
                count += 1
                
                source_chip = f'<span class="chip chip-source">{display_source}</span>'
                sentiment_chip = '<span class="chip chip-emotional">⚠️ High Emotion</span>' if is_emotional else '<span class="chip chip-neutral">✅ Objective</span>'
                
                img_html = ""
                if image_url:
                    img_html = f'<div class="img-column"><img src="{image_url}" alt="Thumbnail"></div>'
                
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
                st.warning("Articles found, but all were filtered by the 'Sensationalism Filter'.")