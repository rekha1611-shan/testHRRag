import os

import streamlit as st
from dotenv import load_dotenv
from langchain_classic.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from gcp_secrets import ensure_gemini_api_key
from rag_store import load_or_build_vectorstore

load_dotenv()

st.set_page_config(page_title="HR Support Chatbot", page_icon="💼", layout="centered")

try:
    ensure_gemini_api_key()
except Exception as exc:
    st.error(f"Application configuration error: {exc}")
    st.stop()

CHAT_MODEL = os.getenv("GEMINI_CHAT_MODEL", "gemini-2.5-flash")


@st.cache_resource
def load_vectorstore():
    return load_or_build_vectorstore()


@st.cache_resource
def load_llm():
    return ChatGoogleGenerativeAI(
        model=CHAT_MODEL,
        temperature=0,
        api_key=os.environ["GEMINI_API_KEY"],
        vertexai=False,
    )


try:
    vectorstore = load_vectorstore()
except Exception as exc:
    st.error(f"Knowledge-base initialization error: {exc}")
    st.stop()

retriever = vectorstore.as_retriever(search_kwargs={"k": 4})
llm = load_llm()

prompt = ChatPromptTemplate.from_template("""
You are an HR Support Assistant for company employees.

Answer questions using ONLY the information provided in the HR documents.
If the answer is not present, say:
"I’m not sure based on current HR policies."

Be clear, professional, and concise.

HR Context:
{context}

Employee Question:
{question}
""")

if "messages" not in st.session_state:
    st.session_state.messages = []

st.title("HR Support Chatbot")
st.markdown(
    "Ask questions about onboarding, leave policy, compensation, IT usage, "
    "security guidelines, and workplace safety."
)

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

user_question = st.chat_input("Ask an HR-related question...")

if user_question:
    st.session_state.messages.append({"role": "user", "content": user_question})

    with st.chat_message("user"):
        st.markdown(user_question)

    with st.spinner("Searching HR policies..."):
        docs = retriever.invoke(user_question)
        context = "\n\n".join(doc.page_content for doc in docs)
        response = llm.invoke(
            prompt.format_messages(context=context, question=user_question)
        )

    answer = response.content if isinstance(response.content, str) else str(response.content)
    with st.chat_message("assistant"):
        st.markdown(answer)

    st.session_state.messages.append({"role": "assistant", "content": answer})
