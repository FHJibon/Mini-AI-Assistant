from openai import AsyncOpenAI
import app.config as config

openai = AsyncOpenAI(api_key=config.OPENAI_API_KEY)

async def get_embeddings(texts: list[str]) -> list[list[float]]:
    res = await openai.embeddings.create(input=texts, model=config.OPENAI_EMBEDDING_MODEL)
    return [item.embedding for item in res.data]
