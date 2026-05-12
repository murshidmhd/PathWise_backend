# scripts/ingest.py

import os
import sys

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from langchain_community.document_loaders import TextLoader
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from core.config import settings

DATA_DIR = os.path.join(os.path.dirname(__file__), "data")


def load_documents():
    documents = []
    for filename in os.listdir(DATA_DIR):
        if filename.endswith(".txt"):
            filepath = os.path.join(DATA_DIR, filename)
            loader = TextLoader(filepath)
            documents.extend(loader.load())
            print(f"Loaded: {filename}")
    return documents


def split_documents(documents):
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=500,
        chunk_overlap=50,
    )
    chunks = splitter.split_documents(documents)
    print(f"Total chunks: {len(chunks)}")
    return chunks


def ingest():
    print("Loading documents...")
    documents = load_documents()

    print("Splitting into chunks...")
    chunks = split_documents(documents)

    print("Initializing Gemini embeddings...")
    embeddings = GoogleGenerativeAIEmbeddings(
        model="gemini-embedding-2-preview", google_api_key=settings.GEMINI_API_KEY
    )

    print("Storing in ChromaDB...")
    Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory=settings.CHROMA_PERSIST_DIR,
    )

    print("Done. ChromaDB is ready.")


if __name__ == "__main__":
    ingest()
