# pages/f1_drive_query.py

import streamlit as st
from rag import get_vector_store, query_rag_system

# Inicialización y obtención del Vector Store
vector_store = get_vector_store()

st.set_page_config(
    page_title="❓ Consulta de Pilotos"
)
st.title("❓ Consulta de Pilotos F1")
st.caption("Usa la inteligencia de Gemini para obtener respuestas basadas en las noticias indexadas.")
st.markdown("---")

st.header("Pregunta a la BD")

# El usuario ingresa su pregunta
user_query = st.text_input(
    "Ingresa tu pregunta sobre un piloto o equipo de F1:",
    placeholder="¿Qué ha dicho Hamilton sobre el desarrollo del motor de Mercedes para 2026?"
)

if st.button("🚀 Consultar con RAG") and user_query:
    st.subheader("Resultado de la Consulta (Generado por Gemini LLM):")

    # Llama a la función del módulo rag.py
    rag_answer = query_rag_system(user_query, vector_store)

    st.markdown(rag_answer)
