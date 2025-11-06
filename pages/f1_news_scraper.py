# pages/f1_news_scraper.py

import streamlit as st
from datetime import datetime, timedelta
from scraper import fetch_recent_news
from rag import get_vector_store, update_db_with_news

st.set_page_config(
    page_title="📡 Scrapeo y Resumen de Noticias"
)

st.title("📡 Scrapeo y Resumen de Noticias F1 (Beta)")
st.caption("Obtención de datos reales (simulada) de sitios web, resumen con Gemini, e indexación en FAISS.")
st.markdown("---")

st.header("1. Configuración de Scrapeo")

# --- Control de Fecha ---
default_date = datetime.today() - timedelta(days=7) # Por defecto, la última semana
start_date = st.date_input(
    "Fecha Mínima de Publicación",
    value=default_date,
    help="Solo se indexarán artículos publicados a partir de esta fecha."
)
start_datetime = datetime(start_date.year, start_date.month, start_date.day)

# --- Botón de Ejecución ---
if st.button("🚀 Iniciar Web Scraping y Resumen (Usando Gemini)",
             type="primary", use_container_width=True):

    # 1. Obtener la base de datos
    vector_store = get_vector_store()

    st.subheader("2. Proceso en Curso...")

    # 2. Ejecutar el scraping
    with st.status("Iniciando proceso de Scrapeo y Resumen...", expanded=True) as status:
        st.write(f"Buscando noticias desde: **{start_date.strftime('%Y-%m-%d')}**")

        try:
            # fetch_recent_news tiene lógica de MOCK/seguridad para evitar bloqueos de IP            
            new_data = fetch_recent_news(start_datetime)

            if new_data:
                st.success(f"🎉 Se encontraron y procesaron {len(new_data)} artículos.")

                # 3. Indexación en FAISS (Llamada al módulo rag.py)
                status.update(label="Indexando nuevos resúmenes en FAISS...", state="running", expanded=True)

                # Aquí llamamos directamente a la lógica de indexación de rag.py
                update_db_with_news(vector_store, new_data)

                # 4. Mostrar Resultados
                st.subheader("3. Resúmenes Indexados:")
                for item in new_data:
                    st.code(f"[{item['driver']} | {item['source']}]: {item['content']}", language="markdown")

                status.update(label="Proceso de Scrapeo e Indexación completo.", state="complete", expanded=False)
            else:
                st.warning("No se encontraron nuevos artículos o el scrapeo fue bloqueado. Intenta cambiar la fecha o las fuentes.")
                status.update(label="Proceso finalizado sin resultados.", state="complete", expanded=False)

        except Exception as e:
            st.error(f"Fallo crítico en el proceso de scraping/LLM: {e}")
            status.update(label="Proceso Fallido.", state="error")
