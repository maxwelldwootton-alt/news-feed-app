That is a much better spot for them UX-wise. Grouping the bulk-action buttons right beneath the things you are actually selecting makes the visual flow a lot more intuitive.

I've taken the entire `col_sel, col_clr, _ = st.columns([1, 1, 3])` block and moved it directly below the `st.pills("Trending Topics"...)` line.

Here is your fully updated code with the buttons in their new home. Copy and paste this directly over your `app.py`:

```python
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

if 'active_default' not in st.session_state:
    st.session_state.active_default = DEFAULT_TOPICS.copy()

if 'active_custom' not in st.session_state:
    st.session_state.active_custom = []

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

        if new_topic not in st.session_state.saved_custom_topics:
            st.session_state.saved_custom_topics = [new_topic] + st.session_state.saved_custom_topics

        current_active = st.session_state.get('active_custom', [])
        if new_topic not in current_active:
            st.session_state.active_custom = current_active + [new_topic]

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
    st.text_input("Add a custom feed:", key="search_input", on_change=add_custom_topic, placeholder="e.g. Nvidia, Venture Capital, Election...", label_visibility="collapsed")
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

# 🌟 MOVED: Select All / Clear All Topic Controls below Trending Topics
col_sel, col_clr, _ = st.columns([1, 1, 3])
with col_sel:
    if st.button("☑️ Select All", use_container_width=True, help="Select all custom and trending topics"):
        st.session_state.active_default = DEFAULT_TOPICS.copy()
        st.session_state.active_custom = st.session_state.saved_custom_topics.copy()
        st.rerun()
with col_clr:
    if st.button("☐ Clear All", use_container_width=True, help="Deselect all topics"):
        st.session_state.active_default = []
        st.session_state.active_custom = []
        st.rerun()

# CONDITIONAL REFRESH BUTTON
current_selected_topics = st.session_state.active_default + st.session_state.active_custom

has_pending_changes = (
    set(current_selected_topics) != set(st.session_state.applied_topics) or
    current_start != st.session_state.applied_start_date or
    current_end != st.session_state.applied_end_date or
    set(current_sources) != set(st.session_state.applied_sources)
)

if has_pending_changes:
    st.info("⚠️ You have pending filter changes.")
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
    st.info("👈 Please select at least one feed category above and click 'Update Feed' to view articles.")
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
                st.caption(f"Showing **{len(processed_articles)}** articles")

            for article in processed_articles:
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

```