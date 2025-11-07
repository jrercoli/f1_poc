# rag.py

import streamlit as st
import os
import time
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from llm_client import get_gemini_client, get_local_embedding_function, LLM_MODEL

# Configuración de FAISS
FAISS_PATH = "f1_faiss_index"

# --- Funciones de FAISS ---


def get_vector_store():
    """Inicializa FAISS con la función de embeddings local, cargando desde disco si existe."""
    embedding_function = get_local_embedding_function()

    try:
        if os.path.exists(FAISS_PATH):
            # Cargar el índice FAISS existente
            vector_store = FAISS.load_local(
                folder_path=FAISS_PATH,
                embeddings=embedding_function,
                allow_dangerous_deserialization=True
            )
            # FAISS no tiene .count() nativo, usamos ntotal del índice subyacente
            st.session_state['db_size'] = vector_store.index.ntotal 
            st.info(f"Index FAISS cargado con {st.session_state['db_size']} documentos.")
        else:
            # Crear un índice FAISS vacío (usamos un documento placeholder)
            st.warning("Creando nuevo índice FAISS...")
            vector_store = FAISS.from_texts(
                texts=["F1 AI System Initializer Placeholder"],
                embedding=embedding_function,
                metadatas=[{"source": "system", "driver": "none"}]
            )
            vector_store.save_local(FAISS_PATH)
            st.session_state['db_size'] = 0
        return vector_store

    except Exception as e:
        st.error(f"Error al inicializar FAISS: {e}")
        st.stop()


def update_db_with_news(vector_store: FAISS, placeholder_news: list):
    """
    Función de Actualización de la BD Vectorial (FAISS).
    """
    if not placeholder_news:
        st.warning("No hay noticias para actualizar.")
        return

    # 1. Preparar datos
    documents = [item["content"] for item in placeholder_news]
    metadatas = [
        {"source": item["source"], "driver": item["driver"], "date": time.ctime()}
        for item in placeholder_news
    ]

    # 2. Agregar a FAISS
    try:
        with st.spinner("Generando embeddings LOCALES e indexando noticias..."):
            # Añadir textos al índice FAISS
            vector_store.add_texts(
                texts=documents,
                metadatas=metadatas
            )
            # Persistir el índice actualizado
            vector_store.save_local(FAISS_PATH)

        st.success(f"✅ ¡Base de Datos Vectorial Actualizada! {len(documents)} documentos añadidos.")
        st.session_state['db_size'] = vector_store.index.ntotal 

    except Exception as e:
        st.error(f"Error al añadir documentos a FAISS: {e}")


def get_rag_context(query: str, vector_store: FAISS) -> tuple[str, list[Document]]:
    """
    Recuperación (Retrieval): Busca en FAISS y formatea el contexto.
    """
    if st.session_state.get('db_size', 0) == 0:
        return "", []

    # 1. Retrieval (Recuperación)
    with st.spinner("🔍 Buscando contexto relevante en la BD Vectorial (FAISS)..."):
        # Asumo que get_vector_store() retorna el objeto FAISS si es necesario
        docs = vector_store.similarity_search(query, k=3)
    # Extraer y formatear el contexto
    context = "\n---\n".join([doc.page_content for doc in docs])
    return context, docs


def query_rag_system(query: str, vector_store: FAISS):
    """
    Sistema RAG COMPLETO: Recuperación con FAISS y Generación con Gemini Client.
    (Esta función ahora se simplifica y reusa la lógica de arriba)
    """
    if st.session_state.get('db_size', 0) == 0:
        return "⚠️ La BD está vacía. Por favor, actualiza las noticias primero."

    # Reusa la lógica de recuperación
    context, docs = get_rag_context(query, vector_store)

    # 2. Generation (Generación)
    prompt_template = f"""
    Eres un experto en Fórmula 1. Genera una respuesta concisa, profesional y en español
    a la pregunta del usuario, basándote ÚNICAMENTE en el siguiente CONTEXTO 
    de noticias. Si el contexto no tiene la información, indica que no la sabes.

    PREGUNTA DEL USUARIO: {query}

    CONTEXTO DE NOTICIAS:
    {context}
    """

    try:
        client = get_gemini_client()

        with st.spinner(f"🤖 Generando respuesta con el LLM ({LLM_MODEL})..."):
            response = client.models.generate_content(
                model=LLM_MODEL,
                contents=[prompt_template]
            ).text

        # Generar metadatos para referencia del usuario
        source_info = "\n\n**Fuentes utilizadas:**\n"
        for i, doc in enumerate(docs):
            meta = doc.metadata
            source_info += f"- Fragmento {i+1} de **{meta.get('driver', 'N/A')}** (Fuente: {meta.get('source', 'N/A')})\n"

        return response + source_info

    except Exception as e:
        return f"Error al generar la respuesta con Gemini LLM: {e}"
