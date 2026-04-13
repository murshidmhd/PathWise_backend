# chat/service.py

from langchain_groq import ChatGroq
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_classic.chains import (
    create_history_aware_retriever,
    create_retrieval_chain,
)
from langchain_classic.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.messages import HumanMessage, AIMessage
from core.config import settings
from chat.schemas import ChatRequest, ChatResponse


# ── Initialize once, reuse forever ──────────────────────────
embeddings = GoogleGenerativeAIEmbeddings(
    model="gemini-embedding-2-preview",
    google_api_key=settings.GEMINI_API_KEY
)

vectorstore = Chroma(
    persist_directory=settings.CHROMA_PERSIST_DIR,
    embedding_function=embeddings
)

retriever = vectorstore.as_retriever(search_kwargs={"k": 3})

llm = ChatGroq(
    model=settings.GROQ_MODEL,
    api_key=settings.GROQ_API_KEY
)

# ── Question rewriting prompt ────────────────────────────────
# This makes "what is the salary?" → "what is the salary of a data scientist?"
contextualize_prompt = ChatPromptTemplate.from_messages([
    ("system", """Given the chat history and latest user question, 
rewrite the question to be self-contained and clear.
If it's already clear, return it as is. Do NOT answer it."""),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])


# ── Main answer prompt ───────────────────────────────────────
answer_prompt = ChatPromptTemplate.from_messages([
    ("system", """You are PathWise, an AI career counselor for Indian students.

Student Profile:
- Primary Career Goal: {primary_career}
- Also Exploring: {recommended_careers}
- About them: {assessment_summary}

Use the following career knowledge to answer:
{context}

Guidelines:
- Be specific to Indian job market
- Give realistic salary figures in LPA
- Be encouraging but honest
- Keep answers concise and actionable
- If student asks about a career not in their profile, still help them
"""),
    MessagesPlaceholder("chat_history"),
    ("human", "{input}"),
])


def build_chat_history(conversation_history):
    """Convert React message format to LangChain format"""
    history = []
    for msg in conversation_history:
        if msg.role == "user":
            history.append(HumanMessage(content=msg.content))
        else:
            history.append(AIMessage(content=msg.content))
    return history


async def chat(request: ChatRequest) -> ChatResponse:
    # Build chat history for LangChain
    chat_history = build_chat_history(request.conversation_history)

    # If there's a summary, add it as context at the start
    if request.summary:
        chat_history.insert(0, AIMessage(content=f"Previous conversation summary: {request.summary}"))

    # Create the RAG chain
    history_aware_retriever = create_history_aware_retriever(
        llm, retriever, contextualize_prompt
    )

    question_answer_chain = create_stuff_documents_chain(llm, answer_prompt)

    rag_chain = create_retrieval_chain(
        history_aware_retriever,
        question_answer_chain
    )

    # Run the chain
    response = await rag_chain.ainvoke({
        "input": request.message,
        "chat_history": chat_history,
        "primary_career": request.user_context.primary_career or "Not specified",
        "recommended_careers": ", ".join(request.user_context.recommended_careers) or "Not specified",
        "assessment_summary": request.user_context.assessment_summary or "Not specified",
    })
    
    
    print(response["answer"])

    # Check if React should summarize
    should_summarize = len(request.conversation_history) >= 10

    return ChatResponse(
        reply=response["answer"],
        should_summarize=should_summarize,
    )

async def summarize(conversation_history: list) -> str:
    messages = build_chat_history(conversation_history)
    
    prompt = f"""Summarize this career counseling conversation in 2-3 sentences.
Focus on: what career the student is exploring, what they've already asked about, and any decisions made.
Be concise — this summary replaces the full history.

Conversation:
{chr(10).join([f"{m.type}: {m.content}" for m in messages])}
"""
    
    response = await llm.ainvoke(prompt)
    return response.content