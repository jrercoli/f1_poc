# 🏎️ F1 News PoC using Generative AI + RAG + Tools

## 🎯 Project Objective

This project is a **Proof of Concept (PoC)** demonstrating how to integrate **Generative AI** (Gemini LLM) with different data architectures to create an advanced query assistant for Formula 1 information.

The main goal is for the **LLM to autonomously decide which resource to use** to answer a user's question:

1.  **Recent Data:** Use **RAG (Retrieval-Augmented Generation)** with a local vector database (FAISS) to answer questions about the latest news, drivers, and statements.
2.  **Structured Data:** Use **Function Calling (Tools)** to query an external API (FastAPI + SQLite) for precise, structured information, such such as race calendar dates.

***

## 💻 Key Technologies

| Category | Technology | Specific Use |
| :--- | :--- | :--- |
| **Models/AI** | Google Gemini (SDK `google-genai`) | **Large Language Model (LLM)** for generation, Function Calling, and reasoning. |
| **RAG/Vectorization** | FAISS, Sentence Transformers | Efficient vector storage and local embedding generation. |
| **Backend/API Tool** | FastAPI | Creation of an **external** API Tool for calendar queries. |
| **Database** | SQLite | Local storage for structured calendar data. |
| **User Interface** | Streamlit | Interactive web interface for the PoC application. |

***

## 🚀 Application Options (Streamlit Pages)

The application is organized into several Streamlit pages (`pages/`), each focused on a specific AI functionality.

### 🧠 1. Universal Query (`pages/f1_unified_query.py`)

This is the main feature. The LLM receives the user query and executes the **(RAG + Tools) orchestration logic** to decide which resource to use:

* **Calendar Questions (Dates, Circuits, GPs):** The LLM executes the **Calendar API Tool** (FastAPI) to fetch structured data.
* **News Questions (Drivers, Statements, Updates):** The LLM uses the **RAG Context** (FAISS data) to ground the answer.

### 📰 2. RAG Query (News-Based) (`pages/f1_drive_query.py`)

Allows direct interaction with the RAG system. Users can query the vectorized knowledge base about previously scraped news. **Does not use API Tools.**

### ⚙️ 3. Configuration & Update (`pages/f1_news_scraper.py`)

Interface for managing the knowledge base:

* **Web Scraper:** Allows running a **Web Scraping** tool (potentially LLM-assisted) to retrieve new articles.
* **Update FAISS:** Processes the scraped content and inserts it into the **FAISS** vector database to update the RAG context.

***

## ⚙️ Setup and Execution

To get the project running, you need to execute the API Tool and the Streamlit interface in separate terminals.

### 1. Preparation

1.  **Clone Repository and Install Dependencies (using virtual env):**
    ```bash
    git clone [REPO_URL]
    cd f1_poc
    python -m venv venv
    source venv/bin/activate  # for Linux/macOS
    # venv\Scripts\activate   # for Windows
    pip install -r requirements.txt
    ```

2.  **Configure Environment Variables:**
    Create a `.env` file in the root directory with your Gemini key and the API Tool URL:
    ```ini
    # .env
    GEMINI_API_KEY="YOUR_KEY_HERE"
    CALENDAR_API_URL="[http://127.0.0.1:8000](http://127.0.0.1:8000)"
    ```

### 2. Execution

1.  **Run the API Tool (Terminal 1):**
    Your FastAPI API must be running for Function Calling to work:
    ```bash
    python api_tool.py
    ```

2.  **Run the Streamlit Interface (Terminal 2):**
    ```bash
    streamlit run app.py
    ```

Navigate to the **Universal Query** page to test the RAG and Tools orchestration.