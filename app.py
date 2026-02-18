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

# --- APP LAYOUT ---
st.set_page_config(page_title="Pure News Feed", page_icon="📰", layout="centered")

# BASE CSS
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .reportview-container { background: #f0f2f6; }
    .headline { font-family: 'Georgia', serif; font-size: 22px; font-weight: bold; color: #2c3e50; text-decoration: none; }
    .metadata { font-family: 'Arial', sans-serif; font-size: 12px; color: #7f8c8d; }
    .neutral { border-left: 5px solid #2ecc71; padding-left: 10px; }
    .emotional { border-left: 5px solid #e74c3c; padding-left: 10px; }
    
    /* STABLE BUTTON STYLING */
    section[data-testid="stSidebar"] .stButton button {
        width: 100%;
        border-radius: 5px;
        transition: background-color 0.3s ease;
    }

    /* --- FORCE CHIPS TO BE BLUE --- */
    /* We use a universal selector (*) to hit the span/div/button whatever Streamlit renders */
    
    /* SELECTED STATE: Blue Background, Blue Border, Bold Text */
    [data-testid="stPillsOption"][aria-selected="true"] {
        background-color: #007bff !important;
        color: white !important;
        border: 2px solid #0056b3 !important; /* Slightly darker blue border */
        font-weight: bold !important;
    }
    
    /* DESELECTED STATE: Ensure it looks clean */
    [data-testid="stPillsOption"][aria-selected="false"] {
        background-color: white !important;
        color: #333 !important;
        border: 1px solid #ddd !important;
    }
    
    /* HOVER EFFECT */
    [data-testid="stPillsOption"]:hover {
        border-color: #007bff !important;
        color: #007bff !important;
    }

    /* Optional: Force Checkbox to Blue too */
    div[data-baseweb="checkbox"] div[aria-checked="true"] {
        background-color: #007bff !important;
        border-color: #007bff !important;
    }
    </style>
""", unsafe_allow_html=True)

st.title("📰 The Wire")
st.caption("No algorithms. No comments. Just headlines.")

# --- SIDEBAR CONTROLS ---

with st.sidebar:
    st.header("Filters")
    
    # 1. Inputs
    current_topic = st.text_input("Topic / Trend", value="Technology")
    
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
    
    st.subheader("Sensationalism Filter")
    current_emotional = st.checkbox("Hide emotionally charged headlines?", value=True)
    
    # 2. Detect Changes
    has_changes = False
    if (current_topic != st.session_state.applied_topic or
        current_start != st.session_state.applied_start_date or
        current_end != st.session_state.applied_end_date or
        set(current_sources) != set(st.session_state.applied_sources) or
        current_emotional != st.session_state.applied_emotional):
        has_changes = True

    # 3. Render Button
    if st.button("Refresh Feed"):
        st.session_state.applied_topic = current_topic
        st.session_state.applied_start_date = current_start
        st.session_state.applied_end_date = current_end
        st.session_state.applied_sources = current_sources
        st.session_state.applied_emotional = current_emotional
        st.rerun()

    # 4. Inject Dynamic CSS *AFTER* the button
    if has_changes:
        st.markdown("""
            <style>
            section[data-testid="stSidebar"] .stButton button {
                background-color: #2ecc71 !important;
                color: white !important;
                border: 1px solid #27ae60 !important;
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
                
                # Format Date
                iso_date = article['publishedAt'][:10]
                date_obj = datetime.strptime(iso_date, '%Y-%m-%d')
                published_formatted = date_obj.strftime('%m/%d/%Y')
                
                # Format Source
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
                
                st.markdown(f"""
                <div class="{css_class}" style="background-color: white; padding: 15px; border-radius: 5px; margin-bottom: 20px; box-shadow: 0 1px 3px rgba(0,0,0,0.1);">
                    <a href="{article['url']}" target="_blank" class="headline">{title}</a>
                    <br><br>
                    <div class="metadata">
                        <b>{display_source}</b> | {published_formatted} | <span style="color: {'#e74c3c' if is_emotional else '#27ae60'}">{emotional_label}</span>
                    </div>
                    <p style="font-family: Arial; font-size: 14px; margin-top: 10px; color: #34495e;">
                        {description if description else ''}
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
            if count == 0 and articles:
                st.warning("Articles found, but all were filtered by the 'Sensationalism Filter'.")