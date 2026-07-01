import logging
import time
from pinecone import Pinecone, ServerlessSpec
import app.config as config
from app.services.embed import get_embeddings

logger = logging.getLogger(__name__)

pc = Pinecone(api_key=config.PINECONE_API_KEY)
index = None

def create_pinecone_index_if_not_exists():
    global index
    name = config.PINECONE_INDEX_NAME
    if name not in [idx.name for idx in pc.list_indexes()]:
        logger.info(f"Creating Pinecone index '{name}'...")
        pc.create_index(
            name=name, dimension=1536, metric='cosine', 
            spec=ServerlessSpec(cloud='aws', region='us-east-1')
        )
        while not pc.describe_index(name).status['ready']:
            time.sleep(5)
    index = pc.Index(name)
    logger.info("Pinecone index is ready")

async def upsert_documents(chunks: list[dict], batch_size: int = 100):
    global index
    if index is None:
        index = pc.Index(config.PINECONE_INDEX_NAME)
    for i in range(0, len(chunks), batch_size):
        batch = chunks[i:i + batch_size]
        embeddings = await get_embeddings([c["text"] for c in batch])
        index.upsert(vectors=[
            {
                "id": f"{c['source']}-chunk-{i+j}",
                "values": emb,
                "metadata": {"source": c["source"], "page": c["page"], "text": c["text"]}
            }
            for j, (c, emb) in enumerate(zip(batch, embeddings))
        ])

async def query_vector_store(query_text: str, top_k: int = 4) -> list[str]:
    global index
    if index is None:
        index = pc.Index(config.PINECONE_INDEX_NAME)
    embs = await get_embeddings([query_text])
    res = index.query(vector=embs[0], top_k=top_k, include_metadata=True)
    return [m.metadata["text"] for m in res.matches if m.metadata and "text" in m.metadata]
