import os

import streamlit as st
from dotenv import load_dotenv
from langchain_classic.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from gcp_secrets import ensure_gemini_api_key
from rag_store import load_or_build_vectorstore

# -----------------------------------------
# ENV
# -----------------------------------------
load_dotenv()

st.set_page_config(
    page_title="HR Support Chatbot",
    page_icon="💼",
    layout="centered",
)

try:
    ensure_gemini_api_key()
except Exception as exc:
    st.error(f"Application configuration error: {exc}")
    st.stop()

# -----------------------------------------
# CONSTANTS
# -----------------------------------------
CHAT_MODEL = os.getenv("GEMINI_CHAT_MODEL", "gemini-2.5-flash")

# -----------------------------------------
# LOAD VECTOR STORE
# -----------------------------------------
@st.cache_resource
def load_vectorstore():
    return load_or_build_vectorstore()


try:
    vectorstore = load_vectorstore()
except Exception as exc:
    st.error(f"Knowledge-base initialization error: {exc}")
    st.stop()

retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

# -----------------------------------------
# LOAD LLM
# -----------------------------------------
@st.cache_resource
def load_llm():
    return ChatGoogleGenerativeAI(
        model=CHAT_MODEL,
        temperature=0,
        api_key=os.environ["GEMINI_API_KEY"],
        vertexai=False,
    )


llm = load_llm()

# -----------------------------------------
# PROMPT (MEMORY-AWARE)
# -----------------------------------------
prompt = ChatPromptTemplate.from_template("""
You are an HR Support Assistant.

Use:
1. HR policy context to answer factually
2. Conversation history to understand follow-up questions

Rules:
- Answer ONLY using HR policy context
- If unsure, say: "I’m not sure based on current HR policies."
- Do NOT invent information

Conversation History:
{chat_history}

HR Policy Context:
{context}

Employee Question:
{question}
""")

# -----------------------------------------
# SESSION STATE
# -----------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# -----------------------------------------
# UI
# -----------------------------------------
st.title("💼 HR Support Chatbot (Memory Enabled)")
st.markdown("Ask HR-related questions. Follow-up questions are supported.")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# -----------------------------------------
# CHAT INPUT
# -----------------------------------------
user_question = st.chat_input("Ask an HR-related question...")

if user_question:
    st.session_state.messages.append({"role": "user", "content": user_question})

    with st.chat_message("user"):
        st.markdown(user_question)

    with st.spinner("Thinking..."):
        history = st.session_state.messages[-6:]
        chat_history = "\n".join(
            f"{m['role'].upper()}: {m['content']}" for m in history
        )

        docs = retriever.invoke(user_question)
        context = "\n\n".join(doc.page_content for doc in docs)

        response = llm.invoke(
            prompt.format_messages(
                chat_history=chat_history,
                context=context,
                question=user_question,
            )
        )

    answer = response.content if isinstance(response.content, str) else str(response.content)

    with st.chat_message("assistant"):
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
