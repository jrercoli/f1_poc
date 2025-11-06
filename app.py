# app.py (Página de Inicio)

import streamlit as st

# import ptvsd
# ptvsd.enable_attach(address=('localhost', 5678), redirect_output=True)
# ptvsd.wait_for_attach()

from dotenv import load_dotenv
# Cargar la clave de la API desde el archivo .env (siempre al inicio)
load_dotenv()

st.set_page_config(
    page_title="🏎️ Home F1 AI",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.title("🏎️ Bienvenido a la App de F1 Generativa (Prototipo)")
st.markdown("---")

st.markdown("""
¡Tu aplicación para fanáticos de la Fórmula 1 basada en IA está lista para ser explorada! 
Utilizamos LLMs, RAG con FAISS (local) y API Tools (próximamente) para darte información 
actualizada y valiosa.
""")

st.subheader("Selecciona una funcionalidad:")

# Usamos columnas para centrar y dar espacio a los botones/tarjetas

col1, col2, col3 = st.columns(3)

with col1:
    IMAGE_PATH = "images/f1_red_bull.jpg"
    st.image(
        IMAGE_PATH,
        caption='Red Bull F1',
        width=300
    )
    st.markdown("### ❓ Consulta de Pilotos F1")
    st.info("Pregunta cualquier cosa sobre los pilotos. La IA usará una base de datos vectorial con noticias actualizadas para responderte con contexto.")
    st.page_link(
        "pages/f1_drive_query.py",
        label="🚀 Ir a Consultar Pilotos",
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
    st.markdown("### 📡 Actualización de Noticias")
    st.info("Aquí puedes simular el proceso de 'scraping' para obtener nuevas noticias y generar los embeddings, manteniendo la base de datos fresca.")
    st.page_link(
        "pages/news_update.py",
        label="🔄 Ir a Actualizar BD",
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
    st.markdown("### 📰 Scrapeo Web y Resumen")
    st.info("Obtención de noticias de la web, resumen automático con Gemini, e indexación en el RAG.")

    st.page_link(
        "pages/f1_news_scraper.py",
        label="🕸️ Web Scraping",
        icon="📰",
        use_container_width=True
    )

st.markdown("---")
