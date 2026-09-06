import os

from dotenv import load_dotenv
from langchain_classic.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI

from gcp_secrets import ensure_gemini_api_key
from rag_store import load_or_build_vectorstore

load_dotenv()
ensure_gemini_api_key()

CHAT_MODEL = os.getenv("GEMINI_CHAT_MODEL", "gemini-2.5-flash")
vectorstore = load_or_build_vectorstore()
retriever = vectorstore.as_retriever(search_kwargs={"k": 4})

llm = ChatGoogleGenerativeAI(
    model=CHAT_MODEL,
    temperature=0,
    api_key=os.environ["GEMINI_API_KEY"],
    vertexai=False,
)

prompt = ChatPromptTemplate.from_template("""
You are an HR Support Assistant.

Answer employee questions using ONLY the provided company documents.
If the answer is not found in the documents, say:
"I’m not sure based on current HR policies."

Be clear, professional, and policy-aligned.

HR Context:
{context}

Employee Question:
{question}
""")


def chat():
    print("\nHR Support Chatbot (type 'exit' to quit)\n")

    while True:
        question = input("Employee: ")
        if question.lower() == "exit":
            break

        docs = retriever.invoke(question)
        context = "\n\n".join(doc.page_content for doc in docs)
        response = llm.invoke(prompt.format_messages(context=context, question=question))
        answer = response.content if isinstance(response.content, str) else str(response.content)

        print("\nHR Bot:", answer)
        print("-" * 60)


if __name__ == "__main__":
    chat()
