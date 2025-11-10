# pages/f1_news_scraper.py

import streamlit as st
from datetime import datetime, timedelta
from scraper import fetch_recent_news
from rag import get_vector_store, update_db_with_news

st.set_page_config(
    page_title="📡 News Scraping and Summary"
)

st.title("📡 F1 News Scraping and Summary")
st.caption("Obtaining real (simulated) data from websites, summarizing with Gemini, and indexing in FAISS.")
st.markdown("---")

st.header("1. Scrape setup")

default_date = datetime.today() - timedelta(days=7) # Por defecto, la última semana
start_date = st.date_input(
    "Minimum Publication Date",
    value=default_date,
    help="Only articles published from this date onwards will be indexed."
)
start_datetime = datetime(start_date.year, start_date.month, start_date.day)

if st.button("🚀 Start Web Scraping and Summary",
             type="primary", use_container_width=True):

    # 1. Obtener la base de datos
    vector_store = get_vector_store()

    st.subheader("2. Process in progress...")

    # 2. Ejecutar el scraping
    with st.status("Starting the scraping and summarization process...", expanded=True) as status:
        st.write(f"Searching for news from **{start_date.strftime('%Y-%m-%d')}**")

        try:
            # fetch_recent_news returns tuple (articles, status_messages)
            new_data, messages = fetch_recent_news(start_datetime)
            
            for msg_type, content in messages:
                if msg_type == 'info':
                    st.info(content)
                elif msg_type == 'success':
                    st.success(content)
                elif msg_type == 'warning':
                    st.warning(content)
                elif msg_type == 'error':
                    st.error(content)
                elif msg_type == 'code':
                    st.code(content, language="html")  # To show debug HTML code

            if new_data:
                st.success(f"🎉 They were found and processed {len(new_data)} articles.")

                # FAISS update and index
                status.update(label="Indexing new abstracts in FAISS...", state="running", expanded=True)                
                update_db_with_news(vector_store, new_data)

                st.subheader("3. Indexed Abstracts:")
                for item in new_data:
                    st.code(f"[{item['driver']} | {item['source']}]: {item['content']}", language="markdown")

                status.update(label="Complete Scraping and Indexing Process.", state="complete", expanded=False)
            else:
                st.warning("No new articles were found, or scraping was blocked. Try changing the date or fonts.")
                status.update(label="Process completed without results.", state="complete", expanded=False)

        except Exception as e:
            st.error(f"Critical failure in the scraping/LLM process: {e}")
            status.update(label="Process Failed.", state="error")
