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

# --- TOPIC & KEYWORD MAPPING ---
# We need this to "guess" which topic an article belongs to locally
TOPIC_KEYWORDS = {
    "Technology": ["tech", "technology", "software", "hardware", "silicon", "apple", "google", "microsoft", "internet"],
    "Artificial Intelligence": ["ai", "artificial intelligence", "llm", "gpt", "openai", "machine learning", "neural"],
    "Stock Market": ["stock", "market", "dow", "nasdaq", "s&p", "economy", "inflation", "fed", "rates"],
    "Crypto": ["crypto", "bitcoin", "btc", "ethereum", "coinbase", "blockchain", "nft"],
    "Politics": ["politics", "congress", "senate", "biden", "trump", "white house", "election", "law"],
    "Epstein Files": ["epstein", "ghislaine", "maxwell", "documents", "list", "court"],
    "Nuclear": ["nuclear", "atomic", "uranium", "fusion", "fission", "plant", "energy"],
    "Space Exploration": ["space", "nasa", "spacex", "moon", "mars", "rocket", "orbit", "galaxy"]
}

SUGGESTED_TOPICS = list(TOPIC_KEYWORDS.keys())

# --- INITIALIZE SESSION STATE ---
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

# --- LOCAL FILTERING FUNCTION ---
def filter_articles_local(articles, selected_topics):
    # If user selected EVERYTHING (or nothing, defaulting to all), return all
    if not selected_topics or len(selected_topics) == len(SUGGESTED_TOPICS):
        return articles
        
    filtered = []
    for article in articles:
        # Combine title and description for searching
        text_content = (article['title'] + " " + (article['description'] or "")).lower()
        
        # Check if article matches ANY of the selected topics
        match_found = False
        for topic in selected_topics:
            keywords = TOPIC_KEYWORDS.get(topic, [])
            # Also check the topic name itself
            if topic.lower() in text_content:
                match_found = True
                break
            # Check associated keywords
            for k in keywords:
                if k in text_content:
                    match_found = True
                    break
            if match_found: break
        
        if match_found:
            filtered.append(article)
            
    return filtered

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

# --- CONTROLS (MAIN PAGE) ---
if "topic_pills" not in st.session_state:
    st.session_state.topic_pills = SUGGESTED_TOPICS # Default: All Selected
    
if "custom_search" not in st.session_state:
    st.session_state.custom_search = ""

def on_pill_change():
    if st.session_state.topic_pills:
        st.session_state.custom_search = ""

def on_text_change():
    if st.session_state.custom_search:
        st.session_state.topic_pills = []

# 1. TOPIC CHIPS
selected_topics = st.pills(
    "Trending now:",
    options=SUGGESTED_TOPICS,
    key="topic_pills",
    on_change=on_pill_change,
    selection_mode="multi"
)

# 2. SEARCH BAR
custom_query = st.text_input(
    "Or search custom topic:", 
    key="custom_search",
    on_change=on_text_change,
    placeholder="e.g. Nvidia, Bitcoin, Election..."
)

# --- QUERY LOGIC (The Smart Part) ---
# We calculate two things:
# 1. 'api_query': What we send to the NewsAPI (Broad, Catch-all)
# 2. 'is_local_filtering': Whether we rely on Python to filter the results

if custom_query:
    # If user typed something specific, we MUST hit the API with that specific query
    api_query = custom_query
    is_local_filtering = False 
else:
    # If using chips, we ALWAYS ask API for ALL TOPICS combined.
    # This ensures the API call parameters never change, so we hit the Cache 100% of the time.
    formatted_topics = [f'"{t}"' if " " in t else t for t in SUGGESTED_TOPICS]
    api_query = " OR ".join(formatted_topics)
    is_local_filtering = True

# --- SIDEBAR (Settings that force API refresh) ---
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

    # We need a button to force refresh DATE or SOURCES, 
    # but NOT for chips (chips should be instant/cached)
    if st.button("Update Timeframe/Sources", type="primary"):
         st.session_state.applied_start_date = current_start
         st.session_state.applied_end_date = current_end
         st.session_state.applied_sources = current_sources
         st.session_state.applied_emotional = current_emotional
         st.rerun()

# --- MAIN FEED ---
st.divider()

if not API_KEY or API_KEY == 'YOUR_NEWSAPI_KEY_HERE':
    st.warning("⚠️ Please enter a valid NewsAPI key in the code configuration.")
else:
    if not st.session_state.applied_sources:
        st.warning("⚠️ Please select at least one source in the sidebar.")
    else:
        with st.spinner("Loading wire..."):
            # 1. FETCH (This hits Cache if api_query hasn't changed)
            raw_articles = fetch_news(
                api_query, 
                st.session_state.applied_sources, 
                st.session_state.applied_start_date, 
                st.session_state.applied_end_date,
                API_KEY
            )
            
            # 2. FILTER LOCALLY (If we are in Chips mode)
            if is_local_filtering and raw_articles:
                final_articles = filter_articles_local(raw_articles, selected_topics)
            else:
                final_articles = raw_articles

            # 3. RENDER
            count = 0
            if not final_articles:
                st.info("No articles found matching your filters.")
                
            for article in final_articles:
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
                
                # Check emotional filter
                # We use the sidebar value directly here so it updates instantly
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
                
            if count == 0 and final_articles:
                st.warning("Articles were fetched, but all were filtered by the 'Sensationalism Filter'.")