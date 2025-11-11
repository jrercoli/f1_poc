# scraper.py

from newspaper import Article, build
from datetime import datetime
from llm_client import get_gemini_client, LLM_MODEL
import random
from bs4 import BeautifulSoup


from news_source_config import (
    F1_SOURCES,
    F1_KEYWORDS,
    USER_AGENTS,
    UTC
)


def extract_date_from_html(article_html: str, config: dict, messages: list) -> datetime | None:
    """
    Searches for date metadata using the selector and format specified in the configuration.
    Returns a datetime 'aware' object (with timezone) or None if it fails.
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

    # If the tag or attribute was not found, we activate failure debugging.
    if date_tag is None or date_str is None:
        messages.append(('info', f"🚨 DEBUG FAILURE (CSS): Date tag/attribute not found for'{config['source']}'."))
        body_tag = soup.find('body')
        html_excerpt = str(body_tag)[:1000] if body_tag else article_html[:1000]
        messages.append(('code', html_excerpt))
        return None

    # If a selector was encountered, we proceed to parse with format
    try:
        dt_object = datetime.strptime(date_str, date_format)
        if dt_object.tzinfo is None or dt_object.tzinfo.utcoffset(dt_object) is None:
            return UTC.localize(dt_object)
        else:
            return dt_object
    except ValueError:
        return None


# Build the newspaper font with a random User-Agent
def build_newspaper_source(url):
    """
    Try building and downloading the website index using a rotating user agent.
    This helps mitigate crashes.
    """
    try:        
        user_agent = random.choice(USER_AGENTS)
        
        paper = build(
            url,
            memoize_articles=False,
            fetch_images=False,
            browser_user_agent=user_agent
        )
        return paper
    except Exception as e:
        print(f" Error building the source{url}: {e}")
        return None


def summarize_with_gemini(text_content: str) -> str:
    """
    Use the Gemini client to summarize the text with the required restrictions.
    """
    if not text_content:
        return "Summary failed: Empty content."
    
    prompt = f"""
    You are an expert in summarizing Formula 1 news. Your task is to summarize the following article
    following these strict rules:

    1. The summary must have a **maximum of 50 words**.
    2. The summary must be structured in **no more than 2 paragraphs**.
    3. Use an informative tone and write in Spanish.

    FULL ARTICLE:
    ---
    {text_content[:1000]}
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
        return f"Summary failed due to LLM error: {e}"


def scrape_and_process_article(url: str, source_data: dict, min_date: datetime, messages: list) -> dict | None:
    """
    Scrapes a URL, extracts the text, summarizes it, and returns the data in RAG format.
    Returns a single-item list (or empty if it fails/is old).
    """    
    try:
        user_agent = random.choice(USER_AGENTS)
        article = Article(url, headers={'User-Agent': user_agent})
        article.download()

        # get pub_date
        if source_data.get('is_blocked'):
            # If it's locked, we rely on newspaper's internal parser
            pub_date = None
        else:            
            pub_date = extract_date_from_html(article.html, source_data, messages)

        article.parse()

        # Content and Date Validation
        if not article.text or len(article.text) <= 50:
            return None
        #
        final_pub_date = pub_date if pub_date else article.publish_date

        # DATE FILTER: min_date must be an 'aware' object (we already ensured this in fetch_recent_news)
        if final_pub_date:
            # We ensure that min_date is also 'aware' if the user passes it without TZ
            if min_date.tzinfo is None or min_date.tzinfo.utcoffset(min_date) is None:
                min_date = UTC.localize(min_date)

            if final_pub_date < min_date:
                messages.append(('info', f"Discarding article due to age -> : '{source_data['source']}' - {url} (Date: {final_pub_date.strftime('%Y-%m-%d')})"))
                return None
        else:
            if source_data.get('is_blocked'):
                messages.append(('info', f"Skipping date filter for blocked source: {source_data['source']}."))
            else:
                messages.append(('warning', f" The date could not be extracted for {url} of {source_data['source']}"))
        
        summary = summarize_with_gemini(article.text)
        
        return {
            "driver": source_data.get('driver', 'Unknown'),
            "source": source_data.get('source', 'Web Scraping'),
            "content": summary
        }

    except Exception as e:
        messages.append(('error', f"Error processing URL {url}: {e}"))
        return None


def is_f1_relevant(article_title: str, article_url: str) -> bool:
    """
    Check if the title or URL contains F1 keywords.
    """
    title_lower = article_title.lower() if article_title else ""
    url_lower = article_url.lower() if article_url else ""
    
    for keyword in F1_KEYWORDS:
        if keyword in title_lower or keyword in url_lower:
            return True
    return False


def fetch_recent_news(start_date: datetime = datetime.today()) -> tuple[list, list]:
    """
    It searches for recent articles from predefined sources and processes them.
    """
    PAPER_ARTICLES_LIMIT = 100
    F1_PAPER_ARTICLES_LIMIT = 2
    f1_papers = 0
    processed_articles = []
    messages = []

    # We ensure that the start date is 'aware' (with TZ) for comparison
    if start_date.tzinfo is None or start_date.tzinfo.utcoffset(start_date) is None:
        start_date = UTC.localize(start_date)

    for source_data in F1_SOURCES:
        source_url = source_data['url']
        messages.append(('info', f"🕸️ : **{source_data['source']}**"))

        try:
            # Build the index (download the main page and look for links to articles)
            paper = build_newspaper_source(source_url)
            if paper is None:
                messages.append(('error', f"❌ Connection failure or lock for {source_url}. Skipping source."))
                continue

            messages.append(('info', f"Potential articles found : {len(paper.articles)}"))
            
            # We limit it to the first X articles to avoid overload and costly/slow calls
            for article in paper.articles[:PAPER_ARTICLES_LIMIT]:
                if not is_f1_relevant(article.title, article.url):
                    continue

                # Process, summarize, and index if relevant.
                # We pass the message list to the scraper to centralize the reports.
                result = scrape_and_process_article(article.url, source_data, start_date, messages)
                if result:
                    processed_articles.append(result)
                    
                    f1_papers += 1
                    if f1_papers >= F1_PAPER_ARTICLES_LIMIT:
                        messages.append(('info', f"Límit of {F1_PAPER_ARTICLES_LIMIT} articles reached."))
                        break

        except Exception as e:
            messages.append(('error', f"Failure during article iteration {source_url}. Error: {e}"))

    # We add a MOCK if nothing is found to ensure the demo flows smoothly
    if not processed_articles:
        messages.append(('warning', "⚠️ No real items were found. Adding a mock item for demonstration purposes."))
        summary = """Formula 1 is planning a radical change in aerodynamics for 2026,
        seeking lighter cars with less drag, focusing on sustainability and closer racing.
        This change promises to reshape the balance of power between the teams.
        """
        processed_articles.append({
            "driver": "Rules for 2026",
            "source": "F1 Mock Data",
            "content": summary
        })

    return processed_articles, messages
