# pages/news_update.py

import streamlit as st
import time
from rag import get_vector_store, update_db_with_news
from llm_client import EMBEDDING_MODEL_LOCAL

vector_store = get_vector_store()

st.set_page_config(
    page_title="📡 News Update"
)
st.title("📡 News update (local FAISS DB)")
st.caption(f"Indexed DB: **{st.session_state['db_size']}** documents (Embeddings: {EMBEDDING_MODEL_LOCAL}).")
st.markdown("---")

# dummy data (MOCK_NEWS)
MOCK_NEWS = [
    {"driver": "Max Verstappen", "source": "f1.com", "content": "Verstappen consiguió su 18ª victoria de la temporada en el GP de Brasil, demostrando una superioridad sin precedentes. El equipo Red Bull confirmó que el coche del 2026 tendrá un enfoque aerodinámico radicalmente nuevo."},
    {"driver": "Fernando Alonso", "source": "motorlat.com", "content": "Alonso expresó su frustración tras un fallo en el pit-stop durante la última carrera. Sin embargo, el equipo Aston Martin está preparando grandes mejoras para las carreras restantes, enfocadas en la tracción a baja velocidad."},
    {"driver": "Lewis Hamilton", "source": "skysports.com", "content": "Hamilton está cerca de firmar su extensión de contrato con Mercedes. Las negociaciones se centran en el desarrollo del coche de 2026, con Lewis solicitando más influencia en la dirección técnica del nuevo motor."}
]

# Lógica de corrección de bug de reindexación
if 'mock_data_indexed' not in st.session_state:
    st.session_state['mock_data_indexed'] = False

st.header("1. Index process")
col1, col2 = st.columns([1, 2])

with col1:
    st.info("Embeddings generation **100% free** and local.")

    if st.session_state['mock_data_indexed']:
        st.warning(f"The test data (MOCK NEWS) has already been loaded in this session.")
        if st.button("🔄 Update database with test news", disabled=True):
            pass 
    else:
        if st.button("🔄 Update database with test news"):
            update_db_with_news(vector_store, MOCK_NEWS)
            st.session_state['last_update'] = time.ctime()
            st.session_state['mock_data_indexed'] = True

with col2:
    if 'last_update' in st.session_state:
        st.metric("Last update", st.session_state['last_update'])
    else:
        if st.session_state['db_size'] > 0:
            st.metric("Initial state", f"Cargado desde disco ({st.session_state['db_size']} docs)")
        else:
            st.metric("Initial state", "empty DB")

    st.markdown("**Test News Content:**")
    for item in MOCK_NEWS:
        st.code(f"Driver: {item['driver']} | Snippet: {item['content'][:50]}...", language="")
