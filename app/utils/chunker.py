import logging
import tiktoken

logger = logging.getLogger(__name__)

def chunk_text(text: str, filename: str, page_idx: int = 1, chunk_size: int = 600, chunk_overlap: int = 150) -> list[dict]:
    chunks = []
    if not text or not text.strip():
        return chunks
        
    tokenizer = tiktoken.get_encoding("cl100k_base")
    tokens = tokenizer.encode(text)
    
    if len(tokens) <= chunk_size:
        chunks.append({
            "text": text.strip(),
            "source": filename,
            "page": page_idx
        })
    else:
        i = 0
        while i < len(tokens):
            chunk_tokens = tokens[i:i + chunk_size]
            chunk_text_decoded = tokenizer.decode(chunk_tokens).strip()
            if chunk_text_decoded:
                chunks.append({
                    "text": chunk_text_decoded,
                    "source": filename,
                    "page": page_idx
                })
            i += chunk_size - chunk_overlap
            
    return chunks

def chunk_documents(loaded_pages: list[dict], chunk_size: int = 600, chunk_overlap: int = 150) -> list[dict]:
    all_chunks = []
    for page in loaded_pages:
        chunks = chunk_text(
            page["text"], 
            page["source"], 
            page["page"], 
            chunk_size, 
            chunk_overlap
        )
        all_chunks.extend(chunks)
    logger.info(f"Generated {len(all_chunks)} chunks from {len(loaded_pages)} loaded pages")
    return all_chunks
