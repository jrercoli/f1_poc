# app.py 

import streamlit as st

# import ptvsd
# ptvsd.enable_attach(address=('localhost', 5678), redirect_output=True)
# ptvsd.wait_for_attach()

from dotenv import load_dotenv
load_dotenv()

st.set_page_config(
    page_title="🏎️ Home F1 AI",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🏎️ Welcome to the Generative F1 App (Prototype)")
st.markdown("---")

st.markdown("""
Your AI-powered Formula 1 fan app is ready to be explored!

We use LLMs, RAG with FAISS (local) and API Tools to give you up-to-date and valuable information.
""")

st.subheader("Select an option:")

col1, col2, col3, col4 = st.columns(4)
with col1:
    IMAGE_PATH = "images/f1_red_bull.jpg"
    st.image(
        IMAGE_PATH,
        caption='Red Bull F1',
        width=300
    )
    st.markdown("### ❓ F1 driver query")
    st.info("Ask anything about the drivers. The AI ​​will use a vector database with up-to-date news to answer you with context.")
    st.page_link(
        "pages/f1_drive_query.py",
        label="🚀 Driver query",
        icon="❓",
        use_container_width=True
    )

with col2:
    IMAGE_PATH = "images/f1_news.jpeg"
    st.image(
        IMAGE_PATH,
        caption='F1 News',
        width=300
    )
    st.markdown("### 📡 News Update")
    st.info("Here you can simulate the 'scraping' process to obtain new news and generate the embeddings, keeping the database fresh.")
    st.page_link(
        "pages/news_update.py",
        label="🔄 DB update (simulated news)",
        icon="📡",
        use_container_width=True
    )

with col3:
    IMAGE_PATH = "images/web_scraping.png"
    st.image(
        IMAGE_PATH,
        caption='F1 news web scrape',
        width=300
    )    
    st.markdown("### 📰 Web Scraping and Summary")
    st.info("Get news from the web, automatic summarization with Gemini, and indexing in the RAG")

    st.page_link(
        "pages/f1_news_scraper.py",
        label="🕸️ Web Scraping",
        icon="📰",
        use_container_width=True
    )

with col4:
    IMAGE_PATH = "images/f1_grid_start.jpg"
    st.image(
        IMAGE_PATH,
        caption='F1 grid start',
        width=300
    )
    st.markdown("### 🧠 Universal query")
    st.info("Ask anything. The LLM will use **RAG (News)** or **Tools (Calendar)** as needed.")
    
    st.page_link(
        "pages/f1_unified_query.py",
        label="⚙️ Universal query",
        icon="🧠",
        use_container_width=True
    )

st.markdown("---")
