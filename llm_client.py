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
    Initializes and returns the direct Gemini client (google.genai).
    The GEMINI_API_KEY is automatically retrieved from the environment.
    """
    try:
        if not os.getenv("GEMINI_API_KEY"):
            raise ValueError("GEMINI_API_KEY it is not configured.")
        return genai.Client()
    except Exception as e:
        # Re-lanzamos la excepción para que Streamlit la muestre
        raise Exception(f"Error initializing Gemini client: {e}")


def get_local_embedding_function():
    """
    Initializes and returns the Sentence Transformers embeddings function (local).
    """
    return SentenceTransformerEmbeddings(model_name=EMBEDDING_MODEL_LOCAL)


def _prepare_tools() -> list[genai.types.Tool]:
    """
    Download the OpenAPI schema from the API Tool and use it to configure the Tool.
    """
    tools = []
    api_uri = f"{CALENDAR_API_URL}/openapi.json"

    try:
        st.info(f"Attempting to download OpenAPI schema from⬇️ : {api_uri}")

        response = requests.get(api_uri)
        response.raise_for_status()
        openapi_spec = response.json()

        # 1. Define the parameter scheme dictionary
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
        # 2. Build FunctionDeclaration to genai
        function_declaration = genai.types.FunctionDeclaration(
            name='query_f1_calendar',
            description=openapi_spec['paths']['/calendar/query']['get']['summary'],
            parameters=parameters_dict
        )

        calendar_tool = genai.types.Tool(function_declarations=[function_declaration])
        tools.append(calendar_tool)

        st.success(f"✅ Configured Tool: **{function_declaration.name}** (Calendar)")

    except requests.exceptions.RequestException as e:
        st.error(f"❌ Network/HTTP error loading the Tool from {api_uri}. The API must be running. Error:**{e}**")
    except Exception as e:
        st.error(f"❌ Error parsing OpenAPI schema. Details: **{e}**")

    return tools


def _handle_function_call(client: genai.Client,
                          response_1: genai.types.GenerateContentResponse,                          
                          context_prompt: str) -> str:
    """
    Execute the function call (API Tool) and pass the result to the LLM.   
    """
    function_call = response_1.function_calls[0]
    function_name = function_call.name
    st.warning(f"🤖 The LLM has decided to ignore the RAG and call the Tool**: {function_name}")

    # 1. Construir URL de la API
    url_endpoint = "/calendar/query"
    params = function_call.args
    query_string = "&".join(f"{key}={value}" for key, value in params.items())
    full_url = f"{CALENDAR_API_URL}{url_endpoint}?{query_string}"

    st.code(f"🔨 Generated API URL:\n{full_url}", language="http")

    # 2. Ejecutar la llamada HTTP
    tool_output = None
    try:
        api_response = requests.get(full_url)
        api_response.raise_for_status()
        tool_output = api_response.json()
        # if tool output result is a list convert to dict
        if isinstance(tool_output, list):
            tool_output = {"calendar_entries": tool_output}
        st.success("✅ Tool executed successfully. Data obtained.")

    except requests.exceptions.RequestException as e:
        st.error(f"❌ Error calling the API Tool: {e}")        
        tool_output = {"error": f"Connection/API failure: {e}"}

    # 3. Second Call to Gemini (Final Generation of the Answer)
    # 3.1 Build content history for the second call
    contents_for_second_call = [
        # original user prompt (context_prompt)
        genai.types.Content(
            role="user",
            parts=[genai.types.Part(text=context_prompt)]
        ),
        # We reuse the original Content object from the model that contains the FunctionCall
        response_1.candidates[0].content,
        # Tool result (FunctionResponse)
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


def unified_query_gemini(prompt: str, vector_store) -> str:
    """
    Central query: configures RAG and Tools. The LLM decides which resource to use.
    """
    from rag import get_rag_context

    client = get_gemini_client()

    # 1. Prepare the RAG context
    rag_context_text, _ = get_rag_context(prompt, vector_store)

    # 1.1. Inject the RAG context into the prompt
    context_prompt = (
        f"CONTEXT OF RECENT NEWS (RAG):\n---\n{rag_context_text}\n---\n"
        f"Based on the context above or the available Tool API, answer the following question: {prompt}"
    )
    st.markdown("---")
    st.info(f"🔎 RAG context injected for news search.")

    # 2. Prepare API Tool
    tools = _prepare_tools()

    # 3. First call to LLM (Decision)
    response_1 = client.models.generate_content(
        model=LLM_MODEL,
        contents=[context_prompt],
        config=genai.types.GenerateContentConfig(
            tools=tools
        )
    )

    # 4. Result manage
    if response_1.function_calls:        
        return _handle_function_call(client, response_1, context_prompt)
    else:        
        st.success("🧠 The LLM responded using the **RAG Context** or their internal knowledge.")
        return response_1.text
