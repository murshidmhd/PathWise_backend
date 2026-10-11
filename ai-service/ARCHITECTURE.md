# PathWise AI Service Architecture

The AI Service is a **FastAPI** application that provides career guidance using **LangChain**, **Groq (Llama 3)**, and **Google Gemini Embeddings**.

## 🚀 The Flow: Step-by-Step

1.  **Incoming Request**:
    *   The client sends a `POST` request to `http://localhost:8002/chat/`.
    *   The request body must follow the `ChatRequest` schema (message, history, user context).

2.  **Authentication (shared with Django)**:
    *   The `verify_token` dependency (`auth/dependencies.py`) intercepts the request.
    *   It decodes the JWT from the `Authorization` header using the `DJANGO_SECRET_KEY`.
    *   If the token is invalid or expired, it returns a `401 Unauthorized` error.

3.  **Routing (`chat/router.py`)**:
    *   The `chat_endpoint` receives the validated `ChatRequest`.
    *   It hands off the heavy lifting to the `chat` service.

4.  **AI Logic (`chat/service.py`)**:
    *   **Contextualization**: First, it uses an LLM to "rewrite" the user's question if it refers to previous messages (e.g., "what about salary?" → "what is the salary for a Data Scientist?").
    *   **Retrieval (RAG)**: It queries a **ChromaDB** vector store to find relevant career information from the ingested documents.
    *   **Generation**: It combines the retrieved context, the student's profile (from `user_context`), and the chat history into a final prompt for the **Groq Llama 3** model.
    *   **Response Construction**: It creates a `ChatResponse` with the AI's answer and a flag (`should_summarize`) if the history is getting long.

## 📁 Project Structure

*   `main.py`: The entry point. Configures FastAPI, CORS, and includes routers.
*   `chat/router.py`: Defines the API endpoints and connects them to services.
*   `chat/service.py`: Contains the LangChain logic, prompts, and RAG configuration.
*   `chat/schemas.py`: Uses **Pydantic** to define the exact shape of data coming in and out.
*   `auth/dependencies.py`: Handles JWT verification using the shared Secret Key.
*   `core/config.py`: Centralized settings using `pydantic-settings` to load from `.env`.

## 🛠 Tech Stack

*   **FastAPI**: The web framework (fast, type-safe, auto-generated docs).
*   **LangChain**: The framework for building LLM applications (chains, retrievers).
*   **Groq**: Extremely fast inference for Llama 3 models.
*   **Google Gemini**: Used for generating high-quality vector embeddings.
*   **ChromaDB**: The vector database used for local storage of career knowledge.
