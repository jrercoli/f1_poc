# pages/f1_unified_query.py

import requests
import streamlit as st
from llm_client import unified_query_gemini, CALENDAR_API_URL

st.set_page_config(
    page_title="🤖 Universal Query (RAG + Tools)"
)

st.title("🤖 F1 Universal Query (RAG + Tools)")
st.caption("Submit any questions about the schedule or driver news. The LLM will decide which resource to use.")
st.markdown("---")

st.header("Ask to Gemini:")

# --- API run status check ---
api_is_running = False
try:
    requests.get(CALENDAR_API_URL, timeout=1)
    api_is_running = True
    st.success("Calendar API Tool **ACTIVE**.")
except requests.exceptions.RequestException:
    st.warning("❌ The Calendar API Tool is not running. Date/GP queries will fail.")
    st.caption("Run **`python api_tool.py`** in a separate terminal.")
# ------------------------------------------
user_query = st.text_input(
    "Enter your question:",
    placeholder="What GPs are on in June? Or what has Leclerc said about the car?"
)

if st.button("🚀 Query", type="primary", use_container_width=True) and user_query:
    st.subheader("Query result:")
    with st.spinner("Thinking... Gemini is orchestrating RAG and Tools..."):
        gemini_answer = unified_query_gemini(user_query)
    st.markdown("## Final LLM response")
    st.markdown(gemini_answer)

st.markdown("---")
