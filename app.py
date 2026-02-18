import streamlit as st
import requests
from textblob import TextBlob
from datetime import datetime, timedelta, date

# --- CONFIGURATION ---
API_KEY = 'c85bd651b9c24f97918f8c85ddc4a36f' 

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

if 'topic_input' not in st.session_state:
    st.session_state.topic_input = "Technology"

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
            # Sort by date descending
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
    /* Clean up the default UI */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    /* Card Styles adapted for Dark Mode */
    .headline { 
        font-family: 'Georgia', serif; 
        font-size: 22px; 
        font-weight: bold; 
        color: #E0E0E0; /* Light text for dark mode */
        text-decoration: none; 
        transition: color 0.2s;
    }
    .headline:hover {
        color: #3B82F6; /* Modern Blue hover */
    }
    .metadata { 
        font-family: 'Arial', sans-serif; 
        font-size: 12px; 
        color: #A0A0A0; /* Dimmed grey for metadata */
    }
    .card-container {
        background-color: #262730; /* Streamlit Dark Grey */
        padding: 15px; 
        border-radius: 8px; 
        margin-bottom: 20px; 
        border: 1px solid #363636;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .neutral { border-left: 5px solid #2ecc71; }
    .emotional { border-left: 5px solid #ef4444; }
    
    /* Standardize Button Transition */
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
    
    # --- 1. TOPIC SELECTION (Synced Pills + Input) ---
    SUGGESTED_TOPICS = ["Technology", "Artificial Intelligence", "Stock Market", "Crypto", "Politics", "Space Exploration"]

    # Callback: Pill clicked -> Update Input
    def update_input_from_pills():
        # Only update if a pill is actually selected (not deselected)
        if st.session_state.topic_pills:
            st.session_state.topic_input = st.session_state.topic_pills

    # Callback: Text typed -> Clear Pills (visual cleanup)
    def clear_pills():
        st.session_state.topic_pills = None

    st.pills(
        "Trending now:",
        options=SUGGESTED_TOPICS,
        key="topic_pills",
        on_change=update_input_from_pills,
        selection_mode="single"
    )

    current_topic = st.text_input(
        "Or search custom topic:", 
        value=st.session_state.topic_input,
        key="topic_input_widget", # Unique key for the widget
        on_change=lambda: st.session_state.update(topic_input=st.session_state.topic_input_widget) or clear_pills()
    )
    # Ensure current_topic variable reflects the session state
    if current_topic != st.session_state.topic_input:
         current_topic = st.session_state.topic_input
    
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
                background-color: #3B82F6 !important; /* Modern Blue */
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
                
                # Logic: > 0.5 subjectivity is considered "emotional/opinion"
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