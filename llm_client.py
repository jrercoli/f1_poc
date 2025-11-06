# llm_client.py

import os
from google import genai
from langchain_community.embeddings import SentenceTransformerEmbeddings

# --- Configuración de Modelos ---
EMBEDDING_MODEL_LOCAL = "all-MiniLM-L6-v2"
LLM_MODEL = "gemini-2.0-flash"


def get_gemini_client():
    """
    Inicializa y retorna el cliente directo de Gemini (google.genai).
    La clave GEMINI_API_KEY se toma automáticamente del entorno.
    """
    try:
        if not os.getenv("GEMINI_API_KEY"):
            raise ValueError("GEMINI_API_KEY no está configurada.")
        return genai.Client()
    except Exception as e:
        # Re-lanzamos la excepción para que Streamlit la muestre
        raise Exception(f"Error al inicializar cliente Gemini: {e}")


def get_local_embedding_function():
    """
    Inicializa y retorna la función de embeddings de Sentence Transformers (local).
    """
    return SentenceTransformerEmbeddings(model_name=EMBEDDING_MODEL_LOCAL)
