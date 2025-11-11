# rag.py

import streamlit as st
import os
import time
from langchain_community.vectorstores import FAISS
from langchain_core.documents import Document
from llm_client import get_gemini_client, get_local_embedding_function, LLM_MODEL

FAISS_PATH = "f1_faiss_index"


def get_vector_store():
    """Initialize FAISS with the local embeddings function, loading from disk if it exists."""
    embedding_function = get_local_embedding_function()

    try:
        if os.path.exists(FAISS_PATH):
            # Load the existing FAISS index
            vector_store = FAISS.load_local(
                folder_path=FAISS_PATH,
                embeddings=embedding_function,
                allow_dangerous_deserialization=True
            )
            # FAISS does not have a native .count(), we use ntotal from the underlying index
            st.session_state['db_size'] = vector_store.index.ntotal 
            st.info(f" Index FAISS loaded with {st.session_state['db_size']} documents.")
        else:
            # Create an empty FAISS index (using a placeholder document)
            st.warning("Creating a new FAISS index...")
            vector_store = FAISS.from_texts(
                texts=["F1 AI System Initializer Placeholder"],
                embedding=embedding_function,
                metadatas=[{"source": "system", "driver": "none"}]
            )
            vector_store.save_local(FAISS_PATH)
            st.session_state['db_size'] = 0
        return vector_store

    except Exception as e:
        st.error(f"Error initializing FAISS: {e}")
        st.stop()


def update_db_with_news(vector_store: FAISS, placeholder_news: list):
    """
    Vector Database Update Function (FAISS).
    """
    if not placeholder_news:
        st.warning("There is no news to update.")
        return

    # 1. Prepare data
    documents = [item["content"] for item in placeholder_news]
    metadatas = [
        {"source": item["source"], "driver": item["driver"], "date": time.ctime()}
        for item in placeholder_news
    ]

    # 2. Add to FAISS DB
    try:
        with st.spinner("Generating local embeds and indexing news..."):
            # Add texts to FAISS index
            vector_store.add_texts(
                texts=documents,
                metadatas=metadatas
            )            
            vector_store.save_local(FAISS_PATH)

        st.success(f"✅ Vector Database Updated!{len(documents)} documents added.")
        st.session_state['db_size'] = vector_store.index.ntotal

    except Exception as e:
        st.error(f": Error adding documents to FAISS {e}")


def get_rag_context(query: str, vector_store: FAISS) -> tuple[str, list[Document]]:
    """
    Retrieval: Search in FAISS and format the context.
    """
    if st.session_state.get('db_size', 0) == 0:
        return "", []

    # 1. Retrieval 
    with st.spinner("🔍 Searching for relevant context in the Vector Database (FAISS)..."):        
        docs = vector_store.similarity_search(query, k=3)
    # Extract and format context
    context = "\n---\n".join([doc.page_content for doc in docs])
    return context, docs


def query_rag_system(query: str, vector_store: FAISS):
    """
    Complete RAG System: Recovery with FAISS and Generation with Gemini Client.
    """
    if st.session_state.get('db_size', 0) == 0:
        return "⚠️ The database is empty. Please update the news first."
    
    context, docs = get_rag_context(query, vector_store)
    
    prompt_template = f"""
    You are a Formula 1 expert. Generate a concise, professional response to the user's question, 
    based ONLY on the following news context. 
    If the context does not contain the information, indicate that you do not know it.

    USER QUESTION: {query}

    NEWS CONTEXT:
    {context}
    """

    try:
        client = get_gemini_client()

        with st.spinner(f"🤖 Generating response with the LLM ({LLM_MODEL})..."):
            response = client.models.generate_content(
                model=LLM_MODEL,
                contents=[prompt_template]
            ).text

        # Generate metadata for user reference
        source_info = "\n\n**Sources used:**\n"
        for i, doc in enumerate(docs):
            meta = doc.metadata
            source_info += f"- Fragment {i+1} of **{meta.get('driver', 'N/A')}** (Source: {meta.get('source', 'N/A')})\n"

        return response + source_info

    except Exception as e:
        return f"Error generating response with LLM: {e}"
