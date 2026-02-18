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

# Initialize the "Working" state for the chips (what the user sees before clicking Refresh)
if 'selected_chips' not in st.session_state:
    # Default to all available sources
    st.session_state.selected_chips = list(SOURCE_MAPPING.values())

# --- FUNCTIONS ---
def fetch_news(query, sources, from_date, to_date):
    if not sources: return []
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

def toggle_source(source_name):
    """Callback to toggle a source in the session state."""
    if source_name in st.session_state.selected_chips:
        st.session_state.selected_chips.remove(source_name)
    else:
        st.session_state.selected_chips.append(source_name)

# --- APP LAYOUT ---
st.set_page_config(page_title="Pure News Feed", page_icon="📰", layout="centered")

# --- CSS STYLING ---
st.markdown("""
    <style>
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    .reportview-container { background: #f0f2f6; }
    .headline { font-family: 'Georgia', serif; font-size: 22px; font-weight: bold; color: #2c3e50; text-decoration: none; }
    .metadata { font-family: 'Arial', sans-serif; font-size: 12px; color: #7f8c8d; }
    .neutral { border-left: 5px solid #2ecc71; padding-left: 10px; }
    .emotional { border-left: 5px solid #e74c3c; padding-left: 10px; }
    
    /* SIDEBAR BUTTON STABILITY */
    section[data-testid="stSidebar"] .stButton button {
        width: 100%;
        border-radius: 5px;
        transition: background-color 0.3s ease;
    }
    
    /* CUSTOM CHIP STYLING */
    /* We target specific div structures to style the columns as chips */
    
    div[data-testid="column"] button {
        width: 100% !important;
        padding: 0.25rem 0.5rem !important;
        font-size: 0.8rem !important;
        border-radius: 20px !important; /* Pill shape */
        min-height: 0px !important;
        height: auto !important;
    }

    /* Selected State (Blue, Bold, Thick) */
    /* Streamlit buttons have a 'kind' attribute we can't easily reach via pure CSS 
       so we use a specific border color hack or rely on the button type logic below */

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
    
    # --- CUSTOM CHIP GRID ---
    # We manually create a grid of buttons.
    # If a button is clicked, it triggers 'toggle_source'
    
    chip_options = list(SOURCE_MAPPING.values())
    
    # Create rows of 2 columns for the chips
    for i in range(0, len(chip_options), 2):
        cols = st.columns(2)
        for j in range(2):
            if i + j < len(chip_options):
                source_name = chip_options[i + j]
                is_selected = source_name in st.session_state.selected_chips
                
                # Visual Logic:
                # We use 'primary' (filled) for selected, 'secondary' (outline) for deselected.
                # Then we inject CSS to customize those specific look-and-feels.
                
                with cols[j]:
                    if st.button(
                        source_name, 
                        key=f"btn_{source_name}",
                        type="primary" if is_selected else "secondary",
                        on_click=toggle_source,
                        args=(source_name,)
                    ):
                        pass

    # INJECT CSS FOR CHIPS (Selected = Blue/Bold/Thick)
    st.markdown("""
        <style>
        /* Target the Primary (Selected) Buttons in the Sidebar columns */
        div[data-testid="column"] button[kind="primary"] {
            background-color: #E3F2FD !important; /* Very light blue background */
            color: #1976D2 !important;           /* Dark Blue Text */
            border: 2px solid #1976D2 !important; /* Thick Blue Border */
            font-weight: 800 !important;          /* Bold */
            box-shadow: none !important;
        }
        
        /* Target the Secondary (Deselected) Buttons */
        div[data-testid="column"] button[kind="secondary"] {
            background-color: white !important;
            color: #555 !important;
            border: 1px solid #ccc !important;    /* Thin Grey Border */
            font-weight: 400 !important;
        }
        
        /* Remove Default Hover effects to keep it clean */
        div[data-testid="column"] button:hover {
            border-color: #1976D2 !important;
            color: #1976D2 !important;
        }
        </style>
    """, unsafe_allow_html=True)

    # Convert the selected display names back to slugs for comparison
    current_sources_slugs = [REVERSE_MAPPING[name] for name in st.session_state.selected_chips]

    st.subheader("Sensationalism Filter")
    current_emotional = st.checkbox("Hide emotionally charged headlines?", value=True)
    
    # 2. Detect Changes
    has_changes = False
    
    # Check if the "Working" chips differ from the "Applied" chips
    if (current_topic != st.session_state.applied_topic or
        current_start != st.session_state.applied_start_date or
        current_end != st.session_state.applied_end_date or
        set(current_sources_slugs) != set(st.session_state.applied_sources) or
        current_emotional != st.session_state.applied_emotional):
        has_changes = True

    # 3. Render Refresh Button
    if st.button("Refresh Feed"):
        st.session_state.applied_topic = current_topic
        st.session_state.applied_start_date = current_start
        st.session_state.applied_end_date = current_end
        st.session_state.applied_sources = current_sources_slugs # Save the slugs
        st.session_state.applied_emotional = current_emotional
        st.rerun()

    # 4. Inject Dynamic Green Button CSS *AFTER* the button
    if has_changes:
        st.markdown("""
            <style>
            section[data-testid="stSidebar"] .stButton button:last-child {
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
    # Ensure at least one source is selected in the applied state
    if not st.session_state.applied_sources:
        st.warning("⚠️ Please select at least one source in the sidebar and click Refresh.")
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
                
                # --- DATE FORMATTING ---
                iso_date = article['publishedAt'][:10]
                date_obj = datetime.strptime(iso_date, '%Y-%m-%d')
                published_formatted = date_obj.strftime('%m/%d/%Y')
                
                # --- SOURCE FORMATTING ---
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