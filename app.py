import streamlit as st
import requests
from textblob import TextBlob
from datetime import datetime, timedelta, date

# --- CONFIGURATION ---
API_KEY = 'c85bd651b9c24f97918f8c85ddc4a36f' 

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

# --- INITIALIZE SESSION STATE ---
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

# --- CSS STYLING (Dark Mode + Blue Theme + Pro UI) ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Card Container with Hover Lift */
    .card-container {
        background-color: #1E1E1E; /* Slightly darker for contrast */
        padding: 20px; 
        border-radius: 10px; 
        margin-bottom: 20px; 
        border: 1px solid #333;
        box-shadow: 0 4px 6px rgba(0,0,0,0.2);
        transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
    }
    .card-container:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 15px rgba(0,0,0,0.3);
        border-color: #3B82F6; /* Glow blue on hover */
    }

    /* Typography */
    .headline { 
        font-family: 'Georgia', serif; 
        font-size: 20px; 
        font-weight: 600; 
        color: #F3F4F6; 
        text-decoration: none; 
        line-height: 1.4;
    }
    .headline:hover { color: #60A5FA; }
    
    .metadata { 
        font-family: 'Inter', sans-serif; 
        font-size: 12px; 
        color: #9CA3AF; 
        margin-top: 12px;
        display: flex;
        align-items: center;
        gap: 10px;
    }

    /* Badges */
    .badge {
        padding: 3px 8px;
        border-radius: 4px;
        font-size: 10px;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.5px;
    }
    .badge-neutral { background-color: rgba(16, 185, 129, 0.15); color: #34D399; border: 1px solid rgba(16, 185, 129, 0.3); }
    .badge-emotional { background-color: rgba(239, 68, 68, 0.15); color: #F87171; border: 1px solid rgba(239, 68, 68, 0.3); }

    /* Button Transition */
    section[data-testid="stSidebar"] .stButton button {
        width: 100%;
        border-radius: 6px;
        transition: background-color 0.2s ease;
        font-weight: 600;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📰 The Wire")
st.caption("No algorithms. No comments. Just headlines.")

# --- SIDEBAR CONTROLS ---

with st.sidebar:
    st.header("Filters")
    
    # 1. TOPIC SELECTION
    SUGGESTED_TOPICS = ["Technology", "Artificial Intelligence", "Stock Market", "Crypto", "Politics", "Space Exploration"]

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

    # 2. TIMEFRAME
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

    # 3. SOURCES
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
    
    # 4. SENSATIONALISM FILTER
    st.subheader("Sensationalism Filter")
    current_emotional = st.checkbox("Hide emotionally charged headlines?", value=True)
    
    # DETECT CHANGES
    has_changes = False
    if (current_topic != st.session_state.applied_topic or
        current_start != st.session_state.applied_start_date or
        current_end != st.session_state.applied_end_date or
        set(current_sources) != set(st.session_state.applied_sources) or
        current_emotional != st.session_state.applied_emotional):
        has_changes = True

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
            
            if not articles:
                st.info("No articles found.")
            else:
                # --- NEW: NOISE DASHBOARD ---
                # Pre-calculate stats for the dashboard
                total_articles = len(articles)
                emotional_count = sum(1 for a in articles if analyze_sentiment(a['title'])[0] > 0.5)
                
                # Show dashboard
                c1, c2, c3 = st.columns(3)
                c1.metric("Total Stories", total_articles)
                c2.metric("Subjective / Emotional", emotional_count)
                
                # Calculate filtering percentage
                if total_articles > 0:
                    clean_ratio = int(((total_articles - emotional_count) / total_articles) * 100)
                else:
                    clean_ratio = 100
                    
                c3.metric("Signal Clarity", f"{clean_ratio}%", delta="Base Quality")
                st.markdown("---")

                # --- RENDER ARTICLES ---
                filtered_count = 0
                for article in articles:
                    title = article['title']
                    if title == "[Removed]": continue
                    
                    # Date
                    iso_date = article['publishedAt'][:10]
                    date_obj = datetime.strptime(iso_date, '%Y-%m-%d')
                    published_formatted = date_obj.strftime('%b %d, %Y')
                    
                    # Source
                    api_source_name = article['source']['name']
                    api_source_id = article['source']['id'] 
                    display_source = SOURCE_MAPPING.get(api_source_id, api_source_name)

                    description = article['description']
                    subjectivity, polarity = analyze_sentiment(title + " " + (description or ""))
                    
                    is_emotional = subjectivity > 0.5
                    
                    # Filter Logic