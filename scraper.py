# scraper.py

from newspaper import Article, build
from datetime import datetime
import streamlit as st
from llm_client import get_gemini_client, LLM_MODEL
import random
from bs4 import BeautifulSoup


from news_source_config import (
    F1_SOURCES,
    F1_KEYWORDS,
    USER_AGENTS,
    UTC
)


def extract_date_from_html(article_html: str, config: dict) -> datetime | None:
    """
    Busca el metadato de fecha usando el selector y formato especificado en la config.
    Retorna un objeto datetime 'aware' (con timezone) o None si falla.
    """    
    if not article_html:
        return None

    soup = BeautifulSoup(article_html, 'html.parser')
    date_tag = None
    date_str = None

    date_tag = soup.select_one(config["date_selector"])
    if date_tag is None and config["date_selector"].startswith('time.'):
        class_name = config["date_selector"].split('.')[-1]
        date_tag = soup.find('time', class_=class_name) 

    if date_tag:
        date_str = date_tag.get(config["date_attribute"])
        date_format = config["date_format"]

    # Si no se encontró el tag o el atributo, activamos el debug de fallo
    if date_tag is None or date_str is None:
        st.warning(f"🚨 DEBUG FALLO (CSS): No se encontró el tag/atributo de fecha para '{config['source']}'.")
        body_tag = soup.find('body')
        html_excerpt = str(body_tag)[:1000] if body_tag else article_html[:1000]
        st.code(html_excerpt, language="html")
        return None

    # Si se encontró con selector, procedemos a parsear con formato
    try:
        dt_object = datetime.strptime(date_str, date_format)
        if dt_object.tzinfo is None or dt_object.tzinfo.utcoffset(dt_object) is None:
            return UTC.localize(dt_object)
        else:
            return dt_object
    except ValueError:
        return None


# Construye la fuente de newspaper con un User-Agent aleatorio
def build_newspaper_source(url):
    """
    Intenta construir y descargar el índice del sitio web usando un User-Agent rotativo.
    Esto ayuda a mitigar los bloqueos.
    """
    try:
        # 1. Selecciona un User-Agent aleatorio
        user_agent = random.choice(USER_AGENTS)
        # 2. Construye el objeto 'source' con el User-Agent específico
        paper = build(
            url,
            memoize_articles=False,
            fetch_images=False,
            browser_user_agent=user_agent
        )
        return paper
    except Exception as e:
        print(f"Error al construir la fuente {url}: {e}")
        return None


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
    {text_content[:1000]} # Limitamos el texto para no exceder el token limit - 8000
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


def scrape_and_process_article(url: str, source_data: dict, min_date: datetime) -> dict | None:
    """
    Scrapea una URL, extrae el texto, lo resume y retorna los datos en el formato RAG.
    Devuelve una lista de un solo elemento (o vacía si falla/es viejo).
    """
    if "/video/" in url:
        return None

    try:
        user_agent = random.choice(USER_AGENTS)
        article = Article(url, headers={'User-Agent': user_agent})
        article.download()

        # obtener pub_date
        if source_data.get('is_blocked'):
            # Si está bloqueado (como MotorSport F1), confiamos en el parser interno de newspaper
            pub_date = None
        else:
            # Si no está bloqueado, intentamos la extracción customizada (CSS o JSON-LD)
            pub_date = extract_date_from_html(article.html, source_data)
    
        article.parse()

        # 1. Validación de Contenido y Fecha
        if not article.text or len(article.text) <= 50:
            return None
        #
        final_pub_date = pub_date if pub_date else article.publish_date
        print(f'final pub_date:{final_pub_date}')
        # FILTRO DE FECHA: min_date debe ser un objeto 'aware' (ya lo aseguramos en fetch_recent_news)
        if final_pub_date:
            # Aseguramos que min_date también sea 'aware' si el usuario lo pasa sin TZ
            if min_date.tzinfo is None or min_date.tzinfo.utcoffset(min_date) is None:
                min_date = UTC.localize(min_date)
            # Compara si la fecha de publicación es anterior a la fecha mínima
            if final_pub_date < min_date:
                st.info(f"  -> Descartando artículo por antigüedad: '{source_data['source']}' - {url} (Fecha: {pub_date.strftime('%Y-%m-%d')})")
                return None
        else:
            if source_data.get('is_blocked'):
                st.info(f"Skipping date filter for blocked source: {source_data['source']}.")
            else:
                st.warning(f"No se pudo extraer la fecha para {url} de {source_data['source']}. Se indexará sin filtro de antigüedad.")

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
        return None


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
    F1_PAPER_ARTICLES_LIMIT = 2
    f1_papers = 0
    processed_articles = []
    # Aseguramos que la fecha de inicio sea 'aware' (con TZ) para la comparación
    if start_date.tzinfo is None or start_date.tzinfo.utcoffset(start_date) is None:
        start_date = UTC.localize(start_date)

    for source_data in F1_SOURCES:
        source_url = source_data['url']
        st.info(f"🕸️ Buscando artículos en el índice: **{source_data['source']}**")

        try:
            # 1. Construir el índice (descarga la página principal y busca enlaces a artículos)
            paper = build_newspaper_source(source_url)
            if paper is None:
                st.error(f"❌ Fallo de conexión o bloqueo para {source_url}. Saltando fuente.")
                continue
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
            st.error(f"Fallo durante la iteración de artículos de {source_url}. Error: {e}")

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
