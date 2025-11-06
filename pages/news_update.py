# pages/news_update.py

import streamlit as st
import time
from rag import get_vector_store, update_db_with_news
from llm_client import EMBEDDING_MODEL_LOCAL

# Inicialización y obtención del Vector Store
vector_store = get_vector_store()

st.set_page_config(
    page_title="📡 Actualización de Noticias"
)
st.title("📡 Módulo de Actualización de Noticias (FAISS Local)")
st.caption(f"DB Indexada: **{st.session_state['db_size']}** documentos (Embeddings: {EMBEDDING_MODEL_LOCAL}).")
st.markdown("---")

# Datos de prueba (MOCK_NEWS) - Duplicados aquí por simplicidad de módulo
MOCK_NEWS = [
    {"driver": "Max Verstappen", "source": "f1.com", "content": "Verstappen consiguió su 18ª victoria de la temporada en el GP de Brasil, demostrando una superioridad sin precedentes. El equipo Red Bull confirmó que el coche del 2026 tendrá un enfoque aerodinámico radicalmente nuevo."},
    {"driver": "Fernando Alonso", "source": "motorlat.com", "content": "Alonso expresó su frustración tras un fallo en el pit-stop durante la última carrera. Sin embargo, el equipo Aston Martin está preparando grandes mejoras para las carreras restantes, enfocadas en la tracción a baja velocidad."},
    {"driver": "Lewis Hamilton", "source": "skysports.com", "content": "Hamilton está cerca de firmar su extensión de contrato con Mercedes. Las negociaciones se centran en el desarrollo del coche de 2026, con Lewis solicitando más influencia en la dirección técnica del nuevo motor."}
]

# Lógica de corrección de bug de reindexación
if 'mock_data_indexed' not in st.session_state:
    st.session_state['mock_data_indexed'] = False

st.header("1. Proceso de Indexación")
col1, col2 = st.columns([1, 2])

with col1:
    st.info("La generación de embeddings es **100% gratuita** y local.")

    if st.session_state['mock_data_indexed']:
        st.warning(f"Los datos de prueba (MOCK NEWS) ya fueron cargados en esta sesión.")
        if st.button("🔄 Actualizar BD con Noticias de Prueba", disabled=True):
            pass 
    else:
        if st.button("🔄 Actualizar BD con Noticias de Prueba"):
            update_db_with_news(vector_store, MOCK_NEWS)
            st.session_state['last_update'] = time.ctime()
            st.session_state['mock_data_indexed'] = True

with col2:
    if 'last_update' in st.session_state:
        st.metric("Última Actualización (Sesión)", st.session_state['last_update'])
    else:
        if st.session_state['db_size'] > 0:
            st.metric("Estado Inicial", f"Cargado desde disco ({st.session_state['db_size']} docs)")
        else:
            st.metric("Estado Inicial", "BD Vacía")

    st.markdown("**Contenido de Noticias de Prueba:**")
    for item in MOCK_NEWS:
        st.code(f"Piloto: {item['driver']} | Snippet: {item['content'][:50]}...", language="")
