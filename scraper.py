# scraper.py

from newspaper import Article, build
from datetime import datetime
import streamlit as st
from llm_client import get_gemini_client, LLM_MODEL

# --- Lista de URLs de ejemplo (debería ser tu lista de DB en el futuro) ---
F1_SOURCES = [
    {"driver": "F1 news", "source": "MotorSport F1", "url": "https://es.motorsport.com/f1/news/"},
]
# {"driver": "F1 news", "source": "Marca F1", "url": "https://www.marca.com/motor/formula1.html"},
# {"driver": "Ferrari", "source": "Sitio Oficial Ferrari F1", "url": "https://www.ferrari.com/es-ES/formula1"},
# {"driver": "Mercedes", "source": "Mercedes F1", "url": "https://www.mercedesamgf1.com/en/"}
# ---------------------------------------------------------------------------
F1_KEYWORDS = ['f1', 'fórmula 1', 'formula 1', 'verstappen', 'hamilton', 'alonso', 'sainz', 'wolff',
               'leclerc', 'red bull', 'mercedes', 'ferrari', 'gp', 'gran premio', 'aston martin'
               'mclaren', 'alpine', 'pit stop', 'parrilla', 'carrera', 'colapinto']
# ---------------------------------------------------------------------------


def summarize_with_gemini(text_content: str) -> str:
    """
    Usa el cliente de Gemini para resumir el texto con las restricciones requeridas.
    """
    if not text_content:
        return "Resumen fallido: Contenido vacío."

    # Prompt estricto para forzar el formato
    prompt = f"""
    Eres un experto en resumen de noticias de Fórmula 1. Tu tarea es resumir el siguiente artículo
    siguiendo estas reglas estrictas:
    1. El resumen debe tener un **máximo de 50 palabras**.
    2. El resumen debe estar estructurado en **no más de 2 párrafos**.
    3. Usa un tono informativo y en español.

    ARTÍCULO COMPLETO:
    ---
    {text_content[:5000]} # Limitamos el texto para no exceder el token limit - 8000
    ---
    """

    try:
        client = get_gemini_client()
        response = client.models.generate_content(
            model=LLM_MODEL,
            contents=[prompt]
        ).text
        return response
    except Exception as e:
        return f"Resumen fallido por error del LLM: {e}"


def scrape_and_process_article(url: str, source_data: dict, min_date: datetime) -> list:
    """
    Scrapea una URL, extrae el texto, lo resume y retorna los datos en el formato RAG.
    Devuelve una lista de un solo elemento (o vacía si falla/es viejo).
    """
    try:
        article = Article(url)
        article.download()
        article.parse()

        # 1. Validación de Contenido y Fecha
        if not article.text or len(article.text) <= 50:
            return None

        publish_date = article.publish_date
        if publish_date and publish_date.replace(tzinfo=None) < min_date.replace(tzinfo=None):
            return None  # Ignorar artículo viejo

        # 2. Resumen con Gemini LLM
        summary = summarize_with_gemini(article.text)

        # 3. Formato RAG (driver-source-content)
        # Intentamos adivinar el piloto basándonos en la fuente (esto se mejoraría en un sistema real)
        # driver_guess = next((src["driver"] for src in F1_SOURCES if src["url"] == url), "Unknown")
        return {
            "driver": source_data.get('driver', 'Unknown'),
            "source": source_data.get('source', 'Web Scraping'),
            "content": summary
        }

    except Exception as e:
        st.warning(f"Error al procesar la URL {url}: {e}")
        return []


def is_f1_relevant(article_title: str, article_url: str) -> bool:
    """
    Verifica si el título o la URL contienen palabras clave de F1.
    """
    title_lower = article_title.lower() if article_title else ""
    url_lower = article_url.lower() if article_url else ""
    # Si al menos una palabra clave está presente, se considera relevante
    for keyword in F1_KEYWORDS:
        if keyword in title_lower or keyword in url_lower:
            return True
    return False


def fetch_recent_news(start_date: datetime = datetime.today()) -> list:
    """
    Busca artículos recientes de las fuentes predefinidas y los procesa.
    """
    PAPER_ARTICLES_LIMIT = 100
    F1_PAPER_ARTICLES_LIMIT = 5
    f1_papers = 0
    processed_articles = []

    for source_data in F1_SOURCES:
        source_url = source_data['url']
        st.info(f"🕸️ Buscando artículos en el índice: **{source_data['source']}**")

        try:
            # 1. Construir el índice (descarga la página principal y busca enlaces a artículos)
            paper = build(source_url, memoize_articles=False, fetch_images=False)
            print(source_url)

            st.write(f"  Artículos potenciales encontrados: {len(paper.articles)}")

            # 2. Iterar sobre los artículos encontrados
            # Limitamos a los primeros X para evitar sobrecarga y llamadas costosas/lentas
            for article in paper.articles[:PAPER_ARTICLES_LIMIT]:
                if not is_f1_relevant(article.title, article.url):
                    continue

                # 3. Procesar, resumir e indexar si es relevante
                result = scrape_and_process_article(article.url, source_data, start_date)
                if result:
                    processed_articles.append(result)
                    st.success(f"  ✅ Resumen de artículo indexado: {article.title[:50]}...")
                    # chequea limite de articulos F1 a almacenar
                    f1_papers += 1
                    if f1_papers >= F1_PAPER_ARTICLES_LIMIT:
                        break

        except Exception as e:
            st.error(f"Fallo al construir el índice para {source_url}. Puede que el sitio web esté bloqueando el acceso. Error: {e}")

    # Añadimos un MOCK si no se encuentra nada para asegurar el flujo de la demo
    if not processed_articles:
        st.warning("⚠️ No se encontraron artículos reales. Añadiendo un artículo MOCK para la demostración.")
        summary = """La F1 planea un cambio radical en la aerodinámica para 2026, 
        buscando coches más ligeros y con menor resistencia, enfocándose en la sostenibilidad y carreras más cerradas. 
        Este cambio promete reordenar las fuerzas entre los equipos.
        """
        processed_articles.append({
            "driver": "Reglas 2026",
            "source": "F1 Mock Data",
            "content": summary
        })

    return processed_articles
