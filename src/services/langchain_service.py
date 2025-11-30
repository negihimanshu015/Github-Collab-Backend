from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain_google_genai import ChatGoogleGenerativeAI, GoogleGenerativeAIEmbeddings
from src.core.config import settings
from typing import List, Dict


class LangChainService:
    def __init__(self):
        self.embeddings = GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-005",
            google_api_key=settings.GEMINI_API_KEY
        )

        # Use new Gemini wrapper (ChatGoogleGenerativeAI)
        self.llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash",
            google_api_key=settings.GEMINI_API_KEY,
            temperature=0.1,
        )

        self.vector_store = None

    def process_code_documents(self, code_files: List[Dict]) -> List[Document]:
        documents = []
        for file in code_files:
            doc = Document(
                page_content=file.get("content", ""),
                metadata={
                    "file_name": file.get("name", ""),
                    "file_path": file.get("path", ""),
                    "language": file.get("language", ""),
                    "repo": file.get("repo", ""),
                },
            )
            documents.append(doc)

        text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200,
        )

        return text_splitter.split_documents(documents)

    def create_vector_store(self, documents: List[Document]):
        self.vector_store = FAISS.from_documents(documents, self.embeddings)
        return self.vector_store

    def query_codebase(self, question: str, k: int = 4) -> Dict:
        if not self.vector_store:
            return {"error": "No vector store initialized. Please process documents first."}

        qa_chain = RetrievalQA.from_chain_type(
            llm=self.llm,
            chain_type="stuff",
            retriever=self.vector_store.as_retriever(search_kwargs={"k": k}),
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

    def code_similarity_search(self, query_code: str, k: int = 3) -> List[Dict]:
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
