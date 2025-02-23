import chromadb
from app.config import settings
import asyncio
from functools import partial

class VectorStore:
    def __init__(self):
        self.client = chromadb.PersistentClient(path=settings.CHROMA_PERSIST_DIRECTORY)
        
    async def create_collection(self, collection_name: str):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None, 
            partial(self.client.create_collection, name=collection_name)
        )
    
    async def get_collection(self, collection_name: str):
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(
            None,
            partial(self.client.get_collection, name=collection_name)
        )
    
    async def add_documents(self, collection_name: str, documents: list, metadatas: list = None, ids: list = None):
        collection = await self.get_collection(collection_name)
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(
            None,
            partial(
                collection.add,
                documents=documents,
                metadatas=metadatas,
                ids=ids
            )
        )
    
    async def query_similar(self, collection_name: str, query_text: str, n_results: int = 5):
        collection = await self.get_collection(collection_name)
        loop = asyncio.get_event_loop()
        results = await loop.run_in_executor(
            None,
            partial(
                collection.query,
                query_texts=[query_text],
                n_results=n_results
            )
        )
        return results

vector_store = VectorStore() 