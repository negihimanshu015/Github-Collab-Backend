from typing import List, Dict
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain_google_genai import ChatGoogleGenerativeAI
from src.core.config import settings

from sklearn.feature_extraction.text import TfidfVectorizer


# ---------------------------------------------------
# Custom lightweight TF-IDF embedding class
# ---------------------------------------------------
class LocalTFIDFEmbeddings:
    def __init__(self):
        self.vectorizer = TfidfVectorizer()

    def embed_documents(self, texts: List[str]):
        """
        Fit TF-IDF on all documents.
        """
        matrix = self.vectorizer.fit_transform(texts)
        return matrix.toarray()

    def embed_query(self, text: str):
        """
        Embed a single query using the fitted vocabulary.
        """
        vector = self.vectorizer.transform([text])
        return vector.toarray()[0]


# ---------------------------------------------------
# Main LangChain Service
# ---------------------------------------------------
class LangChainService:
    def __init__(self):
        # Tiny, fast, render-friendly embeddings
        self.embeddings = LocalTFIDFEmbeddings()

        # Gemini LLM
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.1,
        )

        self.vector_store = None

    # ----------------------------------------------
    # Convert code files into LangChain Documents
    # ----------------------------------------------
    def process_code_documents(self, code_files: List[Dict]) -> List[Document]:
        documents = []

        for file in code_files:
            documents.append(
                Document(
                    page_content=file.get("content", ""),
                    metadata={
                        "file_name": file.get("name", ""),
                        "file_path": file.get("path", ""),
                        "language": file.get("language", ""),
                        "repo": file.get("repo", ""),
                    },
                )
            )

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
        )

        return splitter.split_documents(documents)

    # ----------------------------------------------
    # Build FAISS Vector Store
    # ----------------------------------------------
    def create_vector_store(self, documents: List[Document]):
        texts = [doc.page_content for doc in documents]
        metadatas = [doc.metadata for doc in documents]

        # FAISS computes embeddings automatically using embed_documents()
        self.vector_store = FAISS.from_texts(
            texts=texts,
            embedding=self.embeddings,
            metadatas=metadatas,
        )

        return self.vector_store

    # ----------------------------------------------
    # Query FAISS + Gemini
    # ----------------------------------------------
    def query_codebase(self, question: str, k: int = 4) -> Dict:
        if not self.vector_store:
            return {"error": "Vector store not initialized. Please process documents first."}

        retriever = self.vector_store.as_retriever(search_kwargs={"k": k})

        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=retriever,
            return_source_documents=True,
        )

        result = qa_chain.invoke({"query": question})

        return {
            "answer": result["result"],
            "sources": [
                {
                    "file": doc.metadata.get("file_name"),
                    "path": doc.metadata.get("file_path"),
                    "content": doc.page_content[:200] + "...",
                }
                for doc in result["source_documents"]
            ],
        }

    # ----------------------------------------------
    # Raw Similarity Search
    # ----------------------------------------------
    def code_similarity_search(self, query_code: str, k: int = 3):
        if not self.vector_store:
            return []

        similar_docs = self.vector_store.similarity_search(query_code, k=k)

        return [
            {
                "file": doc.metadata.get("file_name"),
                "path": doc.metadata.get("file_path"),
                "content": doc.page_content,
                "language": doc.metadata.get("language"),
            }
            for doc in similar_docs
        ]
