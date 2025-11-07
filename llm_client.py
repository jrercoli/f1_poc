# llm_client.py

import os
import requests
from google import genai
from langchain_community.embeddings import SentenceTransformerEmbeddings
import streamlit as st

# --- Configuración de Modelos ---
EMBEDDING_MODEL_LOCAL = "all-MiniLM-L6-v2"
LLM_MODEL = "gemini-2.0-flash"

CALENDAR_API_URL = os.getenv("CALENDAR_API_URL", "http://127.0.0.1:8000")


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


from rag import get_vector_store, get_rag_context


def _prepare_tools() -> list[genai.types.Tool]:
    """
    Descarga el esquema OpenAPI de la API Tool y lo usa para configurar la Tool.
    """
    tools = []
    api_uri = f"{CALENDAR_API_URL}/openapi.json"

    try:
        st.info(f"⬇️ Intentando descargar esquema OpenAPI desde: {api_uri}")

        # DESCARGAR el esquema OpenAPI (JSON)
        response = requests.get(api_uri)
        response.raise_for_status()  # Lanza una excepción para códigos 4xx/5xx
        openapi_spec = response.json()

        # EXTRAER la declaración de función requerida por Gemini
        # FastAPI genera la especificación OpenAPI. Debemos adaptarla a Tool.
        # Buscamos la especificación de la única función /calendar/query

        # El nombre de la función en la especificación de FastAPI debe ser único.
        # Lo más fácil es extraer las declaraciones de función del componente 'paths'.        
        # Usamos una forma manual de construir la Tool a partir de la especificación
        # ya que genai.types.Tool.from_dict/from_json puede variar entre versiones.

        # Aquí asumiremos que conocemos la estructura de la función 'query_f1_calendar'
        # que es la única en tu API Tool:

        # 1. Definir el diccionario del esquema de parámetros
        parameters_dict = {
            'type': 'object',
            'properties': {
                p['name']: {
                    'type': p.get('schema', {}).get('type', 'string'),
                    'description': p.get('description', '')
                } 
                for p in openapi_spec['paths']['/calendar/query']['get']['parameters']
            }
        }
        # 2. Construir la FunctionDeclaration
        function_declaration = genai.types.FunctionDeclaration(
            name='query_f1_calendar',
            description=openapi_spec['paths']['/calendar/query']['get']['summary'],
            parameters=parameters_dict
        )

        calendar_tool = genai.types.Tool(function_declarations=[function_declaration])
        tools.append(calendar_tool)

        st.success(f"✅ Tool configurada: **{function_declaration.name}** (Calendario)")

    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error de red/HTTP al cargar la Tool desde {api_uri}. La API debe estar corriendo. Error: **{e}**")
    except Exception as e:
        st.error(f"❌ Error al parsear el esquema OpenAPI. Detalles: **{e}**")

    return tools


def _handle_function_call(client: genai.Client,
                          response_1: genai.types.GenerateContentResponse,                          
                          context_prompt: str) -> str:
    """
    Ejecuta la llamada a la función (API Tool) y pasa el resultado al LLM.    
    """
    function_call = response_1.function_calls[0]
    function_name = function_call.name
    st.warning(f"🤖 El LLM ha decidido **ignorar el RAG y llamar a la Tool**: {function_name}")

    # 1. Construir URL de la API
    url_endpoint = "/calendar/query"
    params = function_call.args
    query_string = "&".join(f"{key}={value}" for key, value in params.items())
    full_url = f"{CALENDAR_API_URL}{url_endpoint}?{query_string}"

    st.code(f"🔨 URL de la API generada:\n{full_url}", language="http")

    # 2. Ejecutar la llamada HTTP
    tool_output = None
    try:
        api_response = requests.get(full_url)
        api_response.raise_for_status()
        tool_output = api_response.json()
        # if tool output result is a list convert to dict
        if isinstance(tool_output, list):
            tool_output = {"calendar_entries": tool_output}
        st.success("✅ Tool ejecutada exitosamente. Datos obtenidos.")

    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error al llamar a la API Tool: {e}")
        # Aseguramos que tool_output sea un json dict para la segunda llamada
        tool_output = {"error": f"Fallo en la conexión/API: {e}"}

    # 3. Segunda Llamada a Gemini (Generación Final de la Respuesta)

    # 3.1 Build content history for the second call
    contents_for_second_call = [
        # prompt original del usuario (context_prompt)
        genai.types.Content(
            role="user",
            parts=[genai.types.Part(text=context_prompt)]
        ),
        # reutilizamos el objeto Content original del modelo que contiene la FunctionCall
        response_1.candidates[0].content,
        # el resultado de la Tool (FunctionResponse)
        genai.types.Content(
            role="tool",
            parts=[genai.types.Part.from_function_response(
                name=function_name,
                response=tool_output
            )]
        )
    ]
    # 3.2 Execute second call
    second_response = client.models.generate_content(
        model=LLM_MODEL,
        contents=contents_for_second_call
    )
    return second_response.text


def unified_query_gemini(prompt: str) -> str:
    """
    Consulta central: configura RAG y Tools. El LLM decide qué recurso usar.
    """
    client = get_gemini_client()

    # 1. Preparar el contexto RAG
    vector_store = get_vector_store()
    rag_context_text, _ = get_rag_context(prompt, vector_store)

    # 1.1. Inyectar el contexto RAG en el prompt
    context_prompt = (
        f"CONTEXTO DE NOTICIAS RECIENTES (RAG):\n---\n{rag_context_text}\n---\n"
        f"Basándote en el contexto anterior o en la Tool API disponible, responde a la siguiente pregunta: {prompt}"
    )
    st.markdown("---")
    st.info(f"🔎 Contexto RAG inyectado para la búsqueda de noticias.")

    # 2. Preparar la API Tool
    tools = _prepare_tools()

    # 3. Primera Llamada a Gemini (Decisión)
    response_1 = client.models.generate_content(
        model=LLM_MODEL,
        contents=[context_prompt],
        config=genai.types.GenerateContentConfig(
            tools=tools
        )
    )

    # 4. Manejo del Resultado
    if response_1.function_calls:
        # El LLM elige la Tool (Delegamos a la función auxiliar)
        return _handle_function_call(client, response_1, context_prompt)
    else:
        # El LLM usó el contexto RAG o su conocimiento interno
        st.success("🧠 El LLM respondió usando el **Contexto RAG** o su conocimiento interno.")
        return response_1.text
