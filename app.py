

import streamlit as st import streamlit.components.v1 as components import requests import re from datetime import datetime, timedelta, date, timezone import google.generativeai as genai import concurrent.futures import urllib.parse # --- CONFIGURATION --- NEWS_API_KEYS = [ st.secrets["NEWS_API

pasted

here is some code i have:

4:15 PM

Recognized code share, anticipated clarification request
Recognized code share, anticipated clarification request


I can see your Streamlit news aggregator app — "The Wire." It pulls articles from NewsAPI, categorizes them by topic with keyword matching, and offers AI-generated summaries via Gemini. Nice setup with the parallel fetching, caching, and custom topic management.

What would you like to do with it? Are you looking to add features, fix a bug, refactor something, or something else entirely?

1771535839093_image.png
there seems to be an additional line under the Tab Selector.  I want to keep the Tab border but remove this secondary line

4:17 PM

Identified Streamlit tab border element causing secondary line
Identified Streamlit tab border element causing secondary line




That's the default Streamlit tab border element. Add this to your CSS block to hide it:

css
div[data-baseweb="tab-border"] {
    display: none !important;
}
Just drop it inside your existing <style> block, for example right after your tab styling rules. Your custom border-bottom on the tab-list will remain intact.

ok that worked - now there is a large gap between the "Showing 90 articles" and the tab selector.  can we redue that?

4:18 PM

Identified spacing issue and devised CSS solution
Identified spacing issue and devised CSS solution

Add this to your CSS block to tighten the spacing below the tabs:

css
div[data-baseweb="tab-panel"] {
    padding-top: 0 !important;
}
And you may also want to reduce the margin-bottom on your existing tab-list rule from 24px to something smaller:

css
div[data-baseweb="tab-list"] {
    margin-bottom: 8px !important;
}
Between those two, the gap should shrink considerably. Adjust the 8px value to taste.

can we make the select all and clear all buttons much smaller

4:20 PM

Identified button sizing issue and devised CSS solution
Identified button sizing issue and devised CSS solution


Make the columns narrower and add some CSS to shrink those buttons.

First, update the columns ratio:

python
col_sel, col_clr, _ = st.columns([1, 1, 7])
Then add this to your CSS block:

css
/* Smaller Select/Clear All buttons */
div[data-testid="stColumns"] .stButton button {
    font-size: 11px !important;
    padding: 4px 8px !important;
    min-height: 0 !important;
    height: auto !important;
}
That'll make them compact, pill-sized controls instead of full-height buttons.

can we make the text smaller too

4:21 PM

Interpreted request to reduce button text size
Interpreted request to reduce button text size

Drop the font-size down further:

css
div[data-testid="stColumns"] .stButton button {
    font-size: 9px !important;
    padding: 3px 6px !important;
    min-height: 0 !important;
    height: auto !important;
}
Adjust 9px up or down to taste.

can we just remove the select all clear all buttons for now? give me the full code

4:22 PM

Prepared to deliver complete code without select/clear buttons
Prepared to deliver complete code without select/clear buttons





Here's the updated code with the Select All / Clear All buttons and their callback functions removed. Everything else is intact, including the earlier CSS fixes (tab border hidden, reduced tab panel padding, 8px tab-list margin).

App
PY 
What else could I do to improve the UI/UX?

4:55 PM

Evaluated UI/UX enhancement opportunities for news aggregator application
Evaluated UI/UX enhancement opportunities for news aggregator application

Here are some ideas, roughly ordered by impact:

Layout & Navigation

Add topic filtering within the feed via clickable category chips — tap "AI" to show only AI articles, tap again to show all
Add a sticky header so the masthead/tabs stay visible as you scroll through articles
Paginate or lazy-load articles instead of dumping all 90+ at once — it's a lot of DOM for the browser and a long scroll
Cards & Content

Hide the fallback placeholder image entirely instead of showing a generic icon — cards without images could go full-width text, which actually looks cleaner
Add a "time ago" format ("2h ago", "Yesterday") alongside or instead of "Feb 18" — it gives faster context for recency
Make the source chip clickable to filter by that source inline
Truncate long descriptions to 2–3 lines with a "read more" expansion
Search & Topics

Add autocomplete or suggestions when typing custom topics (based on trending queries or your keyword bank)
Show a small article count badge next to each topic pill so users know which topics are active vs. returning zero results
AI Overview

Auto-generate the summary when switching to the AI tab instead of requiring a button click — or at least make it a one-click experience with a loading skeleton
Add per-topic summaries (expandable sections) rather than one monolithic wall of text
Let users choose summary length (brief / detailed)
Polish

Add a subtle loading skeleton/shimmer animation while articles fetch instead of a blank page
Add keyboard shortcut support (e.g., j/k to navigate articles, / to focus search)
Dark/light theme toggle — you've built the dark theme well, but some users prefer light
Add a "last updated" timestamp near the article count so users know how fresh the cache is
If any of these jump out, I'm happy to help implement them.

ok lets first start with: Add topic filtering within the feed via clickable category chips — tap "AI" to show only AI articles, tap again to show all

8:53 PM
Good idea — we can add a st.pills filter right inside the Feed tab. Here's my plan:

Add a "Filter by topic" pills widget at the top of the feed tab with all applied topics as options
Default to showing all articles (nothing selected = show all)
When a topic is selected, filter processed_articles to only those tagged with it
Update the article count accordingly
Let me update the full code:


Created 2 files, ran a command, read a file
Created 2 files, ran a command, read a file

Add in-feed topic filtering via clickable pills inside the Feed tab
app.py

Remove old file to recreate

Script

Full code with in-feed topic filtering via clickable pills with article counts
app.py

Presented file
Done
Here's the updated code. The key addition is inside the Feed tab — a single-select st.pills filter that shows each topic with its article count (e.g., "AI (24)"). Selecting one filters the feed to just that topic; deselecting shows everything. The article count caption updates to reflect the filter ("Showing 24 of 90 articles").

App
PY 
ok - lets bring the Selected Topics/Chips into the sideBar AT the top over the Date Rage selection

9:00 PM

Ran a command, created a file, read a file
Ran a command, created a file, read a file
Everything is now consolidated in the sidebar, organized into three sections with dividers: Topics (search input, delete toggle, topic pills) → Date Range → Sources. The "Update Feed" button also lives at the bottom of the sidebar now, and the main content area is just the masthead + feed/AI tabs — much cleaner.

App
PY 
the "Update Feed" button appears to far down on the sidebar, so the user doesnt see and it and knows they need to click it to refresh

9:05 PM
Good catch. Let's move the Update Feed button right below the Topics section, before the Date Range — since topic changes are the most common trigger. That way it's always visible without scrolling.


Move Update Feed button to right after the topics pills, before the date range divider
Move Update Feed button to right after the topics pills, before the date range divider
Hmm, that approach is tricky because the date/source widgets haven't been rendered yet when the button needs to check for changes. Let me take a cleaner approach — place the button right after all widgets but use CSS to visually pin it at the top of the sidebar.

Actually, the simplest clean solution: just move the button to right after the topics section but compute changes only for topics there, then also show it at the bottom if date/source changed. But that's messy.

The cleanest approach: keep the sidebar order as-is but make the button sticky at the bottom of the sidebar viewport so it's always visible.


Revert the partial edit - remove the premature button placeholder
Revert the partial edit - remove the premature button placeholder
Now let's add CSS to make the button sticky at the bottom of the sidebar so it's always visible:


Edited a file, read a file
Edited a file, read a file
I made the Update Feed button sticky at the bottom of the sidebar viewport — so no matter how far the user scrolls in the sidebar, the blue button stays pinned and visible. This avoids the ordering problem (it needs to be rendered after all the widgets it checks) while keeping it always accessible.

App
PY 
that didnt work - maybe we have it located at the top here? marked with red box: https://screenshot.googleplex.com/BdJJf5wRBchESEY

9:07 PM
I can't access that screenshot URL — it's an internal Google link. But I understand what you want: put the Update Feed button at the very top of the sidebar, above everything else.

The challenge is that the button needs to know the current values of the date/source widgets, which haven't been rendered yet. The workaround: use the previous sidebar values from session state for date/source, and only check topics live. Since Streamlit reruns the whole script on any widget change, by the second rerun the button will always reflect the latest state.


Put Update Feed button at the very top of the sidebar, before Topics
Put Update Feed button at the very top of the sidebar, before Topics
Now update the date/source widgets to stash their current values into session state so the top button can read them:


Edited 2 files
Edited 2 files
Now remove the old bottom-of-sidebar button and the sticky CSS since we no longer need either:


Edited 2 files, read a file
Edited 2 files, read a file
The Update Feed button is now at the very top of the sidebar, right under "Filters" and above Topics. It stashes the date/source widget values into session state so that on the next rerun (triggered by any widget change), the button can detect pending changes and appear immediately. When you change a topic, date, or source, the blue button shows up at the top where it's impossible to miss.

App
PY 
can we revert back to the code before i said: ok - lets bring the Selected Topics/Chips into the sideBar AT the top over the Date Rage selection

9:10 PM
Sure — that's the version with the in-feed topic filter but topics/search still in the main content area. Here it is:


Ran a command, created a file, read a file
Ran a command, created a file, read a file
Reverted. Topics, search, delete toggle, and Update Feed button are back in the main content area. Sidebar only has date range and sources. The in-feed topic filter with counts is still included.

App
PY 


Want to be notified when Claude responds?



Claude is AI and can make mistakes. Please double-check responses.
App · PY
Copy

import streamlit as st
import streamlit.components.v1 as components
import requests
import re
from datetime import datetime, timedelta, date, timezone
import google.generativeai as genai
import concurrent.futures
import urllib.parse

# --- CONFIGURATION ---
NEWS_API_KEYS = [
    st.secrets["NEWS_API_KEY_1"],
    st.secrets["NEWS_API_KEY_2"],
    st.secrets["NEWS_API_KEY_3"],
]
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
    'al-jazeera-english': 'Al Jazeera',
    'the-wall-street-journal': 'WSJ',
    'cnbc': 'CNBC',
    'business-insider': 'Business Insider',
    'financial-post': 'Financial Post',
    'techcrunch': 'TechCrunch',
    'wired': 'Wired',
    'ars-technica': 'Ars Technica',
    'hacker-news': 'Hacker News'
}
REVERSE_MAPPING = {v: k for k, v in SOURCE_MAPPING.items()}
NEUTRAL_SOURCES = ['reuters', 'associated-press', 'bloomberg', 'axios', 'politico']

DEFAULT_TOPICS = [
    "Tech", "AI", "Stocks", "Politics", "Epstein", "Nuclear"
]

# --- KEYWORD EXPANSION ---
TOPIC_KEYWORDS = {
    "Tech": [
        "tech", "technology", "software", "hardware", "startup",
        "silicon valley", "app", "semiconductor", "cybersecurity", "cloud computing"
    ],
    "AI": [
        "ai", "artificial intelligence", "machine learning", "llm",
        "openai", "chatgpt", "deep learning", "neural network",
        "anthropic", "gemini", "large language model", "generative ai"
    ],
    "Stocks": [
        "stocks", "stock market", "equities", "s&p", "nasdaq",
        "dow jones", "shares", "earnings", "ipo", "wall street",
        "federal reserve", "interest rates", "hedge fund", "market rally"
    ],
    "Politics": [
        "politics", "election", "congress", "senate",
        "house of representatives", "white house", "legislation",
        "biden", "trump", "democrat", "republican", "gop",
        "governor", "ballot", "campaign", "executive order"
    ],
    "Epstein": [
        "epstein", "jeffrey epstein", "ghislaine maxwell",
        "epstein files", "epstein list"
    ],
    "Nuclear": [
        "nuclear", "uranium", "reactor", "warhead",
        "nonproliferation", "iaea", "fission", "nuclear weapon",
        "nuclear energy", "nuclear deal", "enrichment"
    ],
}

# --- INITIALIZE SESSION STATE ---
if 'saved_custom_topics' not in st.session_state:
    st.session_state.saved_custom_topics = []

if 'active_topics' not in st.session_state:
    st.session_state.active_topics = DEFAULT_TOPICS.copy()

if 'applied_topics' not in st.session_state:
    st.session_state.applied_topics = DEFAULT_TOPICS.copy()

if 'applied_start_date' not in st.session_state:
    current_utc = datetime.now(timezone.utc)
    today = (current_utc - timedelta(hours=5)).date()
    st.session_state.applied_start_date = today - timedelta(days=1)
    st.session_state.applied_end_date = today
    st.session_state.applied_sources = [src for src in SOURCE_MAPPING.keys() if src not in ('wired', 'hacker-news', 'ars-technica')]

if 'ai_summary_text' not in st.session_state:
    st.session_state.ai_summary_text = None
if 'ai_summary_signature' not in st.session_state:
    st.session_state.ai_summary_signature = None

# --- FUNCTIONS ---

def build_api_query(topic):
    keywords = TOPIC_KEYWORDS.get(topic, [topic.lower()])
    capped_keywords = keywords[:5]
    return " OR ".join(f'"{kw}"' for kw in capped_keywords)


@st.cache_data(ttl=timedelta(hours=6), show_spinner=False)
def fetch_news_parallel(topics, sources, from_date, to_date):
    if not topics:
        topics = ["General"]

    all_articles = []

    def fetch_single_topic(topic):
        url = "https://newsapi.org/v2/everything"
        params = {
            'q': build_api_query(topic),
            'searchIn': 'title,description',
            'sources': ','.join(sources) if sources else '',
            'from': from_date.strftime('%Y-%m-%d'),
            'to': to_date.strftime('%Y-%m-%d'),
            'language': 'en',
            'sortBy': 'publishedAt',
            'pageSize': 100,
        }
        for api_key in NEWS_API_KEYS:
            try:
                response = requests.get(url, params={**params, 'apiKey': api_key})
                data = response.json()
                if data.get('status') == 'ok':
                    return data.get('articles', [])
            except:
                pass
        return []

    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        results = executor.map(fetch_single_topic, topics)

    for res in results:
        all_articles.extend(res)

    valid_articles = [a for a in all_articles if a.get('title') and a['title'] != "[Removed]"]
    valid_articles.sort(key=lambda x: x['publishedAt'], reverse=True)

    return valid_articles


def classify_article(text, applied_topics):
    found_tags = []
    text_lower = text.lower()

    for topic in applied_topics:
        keywords = TOPIC_KEYWORDS.get(topic, [topic.lower()])
        for kw in keywords:
            if re.search(rf'\b{re.escape(kw)}\b', text_lower):
                found_tags.append(topic)
                break

    return list(dict.fromkeys(found_tags))


@st.cache_data(show_spinner=False)
def get_gemini_summary(prompt_data_string, date_context):
    if not prompt_data_string.strip():
        return "No articles available to summarize."
    try:
        model = genai.GenerativeModel('gemini-3-flash-preview')
        prompt = f'''You are a professional news briefing assistant. 
The following news articles were published between {date_context}.
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

        if new_topic not in st.session_state.saved_custom_topics and new_topic not in DEFAULT_TOPICS:
            st.session_state.saved_custom_topics = [new_topic] + st.session_state.saved_custom_topics

        current_active = st.session_state.get('active_topics', [])
        if new_topic not in current_active:
            st.session_state.active_topics = current_active + [new_topic]

    st.session_state.search_input = ""

# --- APP CONFIGURATION ---
st.set_page_config(page_title="The Wire", page_icon="📰", layout="centered")

st.markdown('<div id="top-of-page"></div>', unsafe_allow_html=True)

# --- CSS STYLING ---
st.markdown('''
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Merriweather:ital,wght@0,300;0,400;0,700;0,900;1,300;1,400&family=Inter:wght@300;400;500;600&display=swap');
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    
    * { word-wrap: break-word; overflow-wrap: break-word; }
    .block-container { overflow-x: hidden; }

    [data-testid="stHeaderActionElements"],
    h1 > div > a, h2 > div > a, h3 > div > a {
        display: none !important;
    }

    .masthead, .masthead h1, .masthead p, 
    [data-testid="stHeader"], 
    [data-testid="stTab"], 
    div[data-testid="stMarkdownContainer"] > h2 {
        user-select: none !important;
        -webkit-user-select: none !important;
        cursor: default !important;
    }

    /* PREMIUM DOMINANT TABS */
    div[data-baseweb="tab-list"] {
        gap: 8px !important;
        border-bottom: 2px solid #363636 !important;
        margin-bottom: 8px !important;
        padding-bottom: 0 !important;
    }
    button[data-baseweb="tab"] {
        font-family: 'Inter', sans-serif !important;
        font-size: 1.15rem !important;
        font-weight: 600 !important;
        color: #9CA3AF !important;
        padding: 12px 24px !important;
        border-radius: 8px 8px 0 0 !important;
        border: none !important;
        border-bottom: 3px solid transparent !important;
        background-color: transparent !important;
        transition: all 0.2s ease !important;
    }
    button[data-baseweb="tab"]:hover {
        color: #F3F4F6 !important;
        background-color: #2E2F38 !important;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #60A5FA !important;
        border-bottom: 3px solid #60A5FA !important;
        background-color: rgba(59, 130, 246, 0.1) !important;
    }
    div[data-baseweb="tab-border"] {
        display: none !important;
    }
    div[data-baseweb="tab-panel"] {
        padding-top: 0 !important;
    }

    .masthead {
        text-align: center;
        padding: 2rem 0 1.5rem 0;
        margin-bottom: 2rem;
        border-bottom: 1px solid #363636;
    }
    .masthead h1 {
        font-family: 'Merriweather', serif;
        font-size: 3.5rem;
        font-weight: 900;
        color: #F3F4F6;
        margin: 0;
        letter-spacing: -1.5px;
        line-height: 1.2;
    }
    .masthead p {
        font-family: 'Inter', sans-serif;
        color: #9CA3AF;
        font-size: 0.95rem;
        font-weight: 400;
        margin-top: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 3px;
    }

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
    
    .chip { 
        display: inline-flex; align-items: center; padding: 3px 8px; border-radius: 6px; 
        font-size: 10px; font-family: 'Inter', sans-serif; font-weight: 600; 
        text-transform: uppercase; letter-spacing: 0.5px; color: white;
        transition: all 0.2s ease; 
    }
    .chip:hover { transform: translateY(-2px); filter: brightness(1.2); box-shadow: 0 2px 4px rgba(0,0,0,0.3); }
    .chip-source { background-color: #374151; color: #E5E7EB; border: 1px solid #4B5563; }
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

    .ai-briefing-container {
        background: #1E1E24;
        border: 1px solid #2E2F38;
        border-top: 4px solid #3B82F6;
        border-radius: 12px;
        padding: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.4);
        color: #E5E7EB;
        font-family: 'Inter', sans-serif;
        line-height: 1.8;
        margin-top: 1rem;
    }

    .copy-btn {
        display: inline-flex;
        align-items: center;
        gap: 6px;
        padding: 8px 16px;
        background-color: #374151;
        color: #E5E7EB;
        border: 1px solid #4B5563;
        border-radius: 6px;
        cursor: pointer;
        font-family: 'Inter', sans-serif;
        font-size: 13px;
        font-weight: 500;
        transition: all 0.2s ease;
    }
    .copy-btn:hover {
        background-color: #4B5563;
        color: white;
    }

    html { scroll-behavior: smooth; }
    .back-to-top {
        position: fixed;
        bottom: 30px;
        right: 30px;
        width: 50px;
        height: 50px;
        background-color: #3B82F6;
        color: white !important;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.4);
        z-index: 99999;
        text-decoration: none;
        transition: all 0.3s ease;
    }
    .back-to-top:hover {
        background-color: #2563EB;
        transform: translateY(-3px) scale(1.05);
    }
    .back-to-top svg {
        width: 20px;
        height: 20px;
        fill: currentColor;
    }
    </style>
''', unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.header("Advanced Filters")

    current_utc = datetime.now(timezone.utc)
    today = (current_utc - timedelta(hours=5)).date()
    min_allowed_date = today - timedelta(days=29)

    safe_start = max(min(st.session_state.applied_start_date, today), min_allowed_date)
    safe_end = max(min(st.session_state.applied_end_date, today), min_allowed_date)
    if safe_start > safe_end:
        safe_start = safe_end

    current_date_range = st.date_input(
        "Select Date Range",
        value=(safe_start, safe_end),
        min_value=min_allowed_date,
        max_value=today,
        format="MM/DD/YYYY"
    )

    if len(current_date_range) == 2:
        current_start, current_end = current_date_range
    elif len(current_date_range) == 1:
        current_start, current_end = current_date_range[0], current_date_range[0]
    else:
        current_start, current_end = safe_start, safe_end

    display_names = list(SOURCE_MAPPING.values())
    selected_display_names = st.pills("Toggle sources:", options=display_names, default=[SOURCE_MAPPING[src] for src in st.session_state.applied_sources if src in SOURCE_MAPPING], selection_mode="multi")
    current_sources = [REVERSE_MAPPING[name] for name in selected_display_names] if selected_display_names else []

# --- MAIN UI MASTHEAD ---
st.markdown('''
<div class="masthead">
    <h1>📰 The Wire</h1>
    <p>No algorithms. No comments. Just headlines.</p>
</div>
''', unsafe_allow_html=True)

col_search, col_edit = st.columns([4, 1])
with col_search:
    st.text_input("Add a custom topic:", key="search_input", on_change=add_custom_topic, placeholder="e.g. Nvidia, Venture Capital, Election...", label_visibility="collapsed")
with col_edit:
    is_edit_mode = st.toggle("Delete", key="edit_mode", help="Turn on to delete custom topics")

# Unified Delete Mode for Custom Topics
if is_edit_mode and st.session_state.saved_custom_topics:
    st.warning("🗑️ **Delete Mode Active:** Uncheck to permanently remove a custom topic.")
    def on_delete_change():
        remaining = st.session_state.temp_delete_widget
        st.session_state.saved_custom_topics = remaining
        st.session_state.active_topics = [t for t in st.session_state.active_topics if t in DEFAULT_TOPICS or t in remaining]
    st.pills("Delete", options=st.session_state.saved_custom_topics, default=st.session_state.saved_custom_topics, key="temp_delete_widget", on_change=on_delete_change, selection_mode="multi", label_visibility="collapsed")

# UNIFIED TOPICS DISPLAY
st.write("**Selected Topics**")

all_combined_options = DEFAULT_TOPICS + st.session_state.saved_custom_topics
st.pills("Selected Topics", options=all_combined_options, key="active_topics", selection_mode="multi", label_visibility="collapsed")

# CONDITIONAL REFRESH BUTTON
current_selected_topics = st.session_state.active_topics

has_pending_changes = (
    set(current_selected_topics) != set(st.session_state.applied_topics) or
    current_start != st.session_state.applied_start_date or
    current_end != st.session_state.applied_end_date or
    set(current_sources) != set(st.session_state.applied_sources)
)

if has_pending_changes:
    st.write("")
    if st.button("🔄 Update Feed", type="primary", use_container_width=True):
        st.session_state.applied_topics = current_selected_topics
        st.session_state.applied_start_date = current_start
        st.session_state.applied_end_date = current_end
        st.session_state.applied_sources = current_sources
        st.rerun()

FALLBACK_IMG = "data:image/svg+xml;base64,PHN2ZyB4bWxucz0naHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmcnIHdpZHRoPScxMjAnIGhlaWdodD0nMTIwJz48cmVjdCB3aWR0aD0nMTIwJyBoZWlnaHQ9JzEyMCcgZmlsbD0nIzFGMjkzNycvPjx0ZXh0IHg9JzUwJScgeT0nNTAlJyBmb250LXNpemU9JzQwJyB0ZXh0LWFuY2hvcj0nbWlkZGxlJyBkeT0nLjNlbSc+8J+TsDwvdGV4dD48L3N2Zz4="

# --- MAIN APP BODY ---
if not NEWS_API_KEYS:
    st.warning("⚠️ Please enter at least one valid NewsAPI key.")
elif not st.session_state.applied_topics:
    st.info("👈 Please select at least one topic above and click 'Update Feed' to view articles.")
else:
    if not st.session_state.applied_sources:
        st.warning("⚠️ Please select at least one source in the sidebar.")
    else:
        try:
            raw_articles = fetch_news_parallel(
                st.session_state.applied_topics,
                st.session_state.applied_sources,
                st.session_state.applied_start_date,
                st.session_state.applied_end_date
            )
        except Exception as e:
            st.error(f"🚨 API Error: {e}")
            raw_articles = []

        processed_articles = []
        seen_titles = set()

        for article in raw_articles:
            title = article.get('title') or ""

            if title in seen_titles:
                continue
            seen_titles.add(title)

            description = article.get('description') or ""
            text_to_analyze = f"{title} {description}"

            article_tags = classify_article(text_to_analyze, st.session_state.applied_topics)

            if not article_tags:
                continue

            article_tags.sort(key=lambda x: st.session_state.applied_topics.index(x) if x in st.session_state.applied_topics else 999)

            article['computed_tags'] = article_tags
            processed_articles.append(article)

        tab_feed, tab_ai = st.tabs(["📰 Feed", "✨ AI Overview"])

        # --- TAB 1: THE FEED ---
        with tab_feed:
            if not processed_articles:
                if raw_articles:
                    st.info("Articles were found, but they were filtered out by your current chips.")
                else:
                    st.info("No articles found matching these topics on the selected dates.")
            else:
                # --- In-feed topic filter with article counts ---
                topic_counts = {}
                for a in processed_articles:
                    for tag in a['computed_tags']:
                        topic_counts[tag] = topic_counts.get(tag, 0) + 1

                filter_options = [
                    f"{t} ({topic_counts[t]})"
                    for t in st.session_state.applied_topics
                    if topic_counts.get(t, 0) > 0
                ]
                filter_label_to_topic = {
                    f"{t} ({topic_counts[t]})": t
                    for t in st.session_state.applied_topics
                    if topic_counts.get(t, 0) > 0
                }

                selected_filter = st.pills(
                    "Filter by topic",
                    options=filter_options,
                    default=None,
                    selection_mode="single",
                    key="feed_topic_filter",
                )

                if selected_filter:
                    active_filter_topic = filter_label_to_topic.get(selected_filter)
                    filtered_articles = [a for a in processed_articles if active_filter_topic in a['computed_tags']]
                else:
                    filtered_articles = processed_articles

                st.caption(f"Showing **{len(filtered_articles)}** of {len(processed_articles)} articles")

                for article in filtered_articles:
                    title = article.get('title') or ""
                    url = article.get('url') or "#"
                    image_url = article.get('urlToImage')
                    description = article.get('description') or ""

                    tags_html = ""
                    article_tags = article['computed_tags']
                    visible_tags = article_tags[:2]
                    hidden_tags = article_tags[2:]
                    overflow_count = len(hidden_tags)

                    for tag in visible_tags:
                        tags_html += f'<span class="chip chip-category">{tag}</span>'

                    if overflow_count > 0:
                        tooltip_text = ", ".join(hidden_tags)
                        tags_html += f'<span class="chip chip-overflow">+{overflow_count}<span class="tooltip-text">{tooltip_text}</span></span>'

                    iso_date = article.get('publishedAt', '')[:10]
                    published_formatted = datetime.strptime(iso_date, '%Y-%m-%d').strftime('%b %d') if iso_date else "Unknown Date"

                    api_source_name = article.get('source', {}).get('name', 'Unknown')
                    api_source_id = article.get('source', {}).get('id', '')
                    display_source = SOURCE_MAPPING.get(api_source_id, api_source_name)

                    source_chip = f'<span class="chip chip-source">{display_source}</span>'

                    if image_url:
                        img_html = f'<div class="img-column"><img src="{image_url}" alt="Thumbnail" onerror="this.onerror=null; this.src=\'{FALLBACK_IMG}\';"></div>'
                    else:
                        img_html = f'<div class="img-column"><img src="{FALLBACK_IMG}" alt="Placeholder"></div>'

                    st.markdown(f'''<div class="card-container"><div class="card-content"><div class="text-column"><a href="{url}" target="_blank" class="headline">{title}</a><div class="metadata">{source_chip}{tags_html}<span style="color: #6B7280; font-weight: bold;">•</span><span>{published_formatted}</span></div><p class="description-text">{description}</p></div>{img_html}</div></div>''', unsafe_allow_html=True)

        # --- TAB 2: AI OVERVIEW ---
        with tab_ai:
            st.header("✨ AI Overview", anchor=False)

            if not processed_articles:
                st.info("No articles available to summarize.")
            else:
                prompt_lines = []
                for a in processed_articles[:30]:
                    cat_string = ", ".join(a['computed_tags'][:2])
                    title = a.get('title') or "No Title"
                    desc = a.get('description') or "No Description"
                    content = a.get('content') or "No Content"
                    prompt_lines.append(f"Categories: [{cat_string}] | Title: {title} | Desc: {desc} | Content: {content}")

                prompt_data_string = "\n".join(prompt_lines)

                current_feed_signature = f"{st.session_state.applied_topics}_{st.session_state.applied_start_date}_{st.session_state.applied_end_date}_{st.session_state.applied_sources}"

                if st.session_state.get('ai_summary_signature') != current_feed_signature:
                    if st.button("Generate Summary", type="primary"):
                        with st.spinner("Gemini is reading the news..."):
                            date_context = f"{st.session_state.applied_start_date.strftime('%B %d')} and {st.session_state.applied_end_date.strftime('%B %d')}"
                            summary_markdown = get_gemini_summary(prompt_data_string, date_context)
                            st.session_state.ai_summary_text = summary_markdown
                            st.session_state.ai_summary_signature = current_feed_signature
                            st.rerun()

                if st.session_state.get('ai_summary_signature') == current_feed_signature:
                    encoded_summary = urllib.parse.quote(st.session_state.ai_summary_text)
                    st.markdown(f'''
                    <div class="ai-briefing-container">
                        {st.session_state.ai_summary_text}
                        <hr style="border-color: #363636; margin: 1.5rem 0 1rem 0;">
                        <button id="copy-ai-btn" class="copy-btn" data-text="{encoded_summary}">📋 Copy to Clipboard</button>
                    </div>
                    ''', unsafe_allow_html=True)

# Back to top button
st.markdown(
    '''
    <a href="#top-of-page" class="back-to-top" title="Return to top">
        <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 384 512">
            <path d="M214.6 41.4c-12.5-12.5-32.8-12.5-45.3 0l-160 160c-12.5 12.5-12.5 32.8 0 45.3s32.8 12.5 45.3 0L160 141.2V448c0 17.7 14.3 32 32 32s32-14.3 32-32V141.2L329.4 246.6c12.5 12.5 32.8 12.5 45.3 0s12.5-32.8 0-45.3l-160-160z"/>
        </svg>
    </a>
    ''',
    unsafe_allow_html=True
)

# Copy to clipboard JS
components.html(
    """
    <script>
    const parentDoc = window.parent.document;
    const parentWin = window.parent;
    
    const findCopyBtn = setInterval(() => {
        const btn = parentDoc.getElementById('copy-ai-btn');
        if (btn && !btn.hasAttribute('data-copy-listener')) {
            btn.setAttribute('data-copy-listener', 'true');
            
            btn.addEventListener('click', function() {
                const textToCopy = decodeURIComponent(btn.getAttribute('data-text'));
                
                function fallbackCopyTextToClipboard(text) {
                    var textArea = parentDoc.createElement("textarea");
                    textArea.value = text;
                    textArea.style.top = "0";
                    textArea.style.left = "0";
                    textArea.style.position = "fixed";
                    textArea.style.opacity = "0";
                    parentDoc.body.appendChild(textArea);
                    textArea.focus();
                    textArea.select();
                    try {
                        var successful = parentDoc.execCommand('copy');
                        return successful;
                    } catch (err) {
                        return false;
                    } finally {
                        parentDoc.body.removeChild(textArea);
                    }
                }

                function onSuccess() {
                    btn.innerHTML = "✅ Copied!";
                    btn.style.backgroundColor = "#059669"; 
                    btn.style.borderColor = "#047857";
                    setTimeout(() => { 
                        btn.innerHTML = "📋 Copy to Clipboard"; 
                        btn.style.backgroundColor = "#374151";
                        btn.style.borderColor = "#4B5563";
                    }, 2000);
                }

                function onError(err) {
                    console.error('Copy failed: ', err);
                    btn.innerHTML = "❌ Error Copying";
                    setTimeout(() => { 
                        btn.innerHTML = "📋 Copy to Clipboard"; 
                    }, 2000);
                }

                if (parentWin.navigator && parentWin.navigator.clipboard) {
                    parentWin.navigator.clipboard.writeText(textToCopy)
                        .then(onSuccess)
                        .catch(err => {
                            if (fallbackCopyTextToClipboard(textToCopy)) {
                                onSuccess();
                            } else {
                                onError(err);
                            }
                        });
                } else {
                    if (fallbackCopyTextToClipboard(textToCopy)) {
                        onSuccess();
                    } else {
                        onError("Clipboard API not available");
                    }
                }
            });
        }
    }, 250);
    </script>
    """,
    height=0,
    width=0
)


