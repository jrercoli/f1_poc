# pages/f1_unified_query.py

import requests
import streamlit as st
from llm_client import unified_query_gemini, CALENDAR_API_URL

st.set_page_config(
    page_title="🤖 Consulta Universal (RAG + Tools)"
)

st.title("🤖 Consulta Universal: RAG + Tools F1")
st.caption("Introduce cualquier pregunta sobre el calendario o noticias de pilotos. El LLM decidirá qué recurso utilizar.")
st.markdown("---")

st.header("Pregunta a Gemini:")

# --- Chequeo de Estado (Mejora la UX) ---
api_is_running = False
try:
    requests.get(CALENDAR_API_URL, timeout=1)
    api_is_running = True
    st.success("API Tool de Calendario **ACTIVA**.")
except requests.exceptions.RequestException:
    st.warning("❌ La API Tool de Calendario NO está ejecutandose. Las consultas sobre fechas/GPs fallarán.")
    st.caption("Ejecuta **`python api_tool.py`** en una terminal separada.")
# ------------------------------------------
user_query = st.text_input(
    "Ingresa tu pregunta:",
    placeholder="¿Qué GPs hay en junio? o ¿Qué ha dicho Leclerc sobre el coche?"
)

if st.button("🚀 Consultar", type="primary", use_container_width=True) and user_query:
    st.subheader("Resultado de la Consulta:")
    with st.spinner("Pensando... Gemini está orquestando el RAG y las Tools..."):
        # Llama a la nueva función unificada
        gemini_answer = unified_query_gemini(user_query)
    st.markdown("## Respuesta Final del LLM")
    st.markdown(gemini_answer)

st.markdown("---")
