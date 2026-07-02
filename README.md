# Mini AI Assistant

**Mini AI Assistant** built with **FastAPI**, **OpenAI**, and **Pinecone** that combines **Retrieval-Augmented Generation**, **conversation memory**, and **AI tool calling** into a single modular pipeline.

---

# Features

1. Accept PDF, TXT, and Markdown files for knowledge ingestion
2. Automatically split documents into small, manageable pieces
3. Create smart semantic representations (embeddings) of the content
4. Store and quickly search these representations with Pinecone vector database
5. Remembers conversation context within the current session
6. Understands follow‑up questions
7. Built‑in tools for product search and order status look‑up
8. FastAPI server with Docker deployment

---

# System Architecture

<p align="center">
  <img src="app/data/Architecture.png" alt="System Architecture">
</p>

---

# Implementation Details

## Ingestion Pipeline

The ingestion pipeline performs the following steps:

1. Load supported documents
2. Extract raw text
3. Split text into overlapping chunks using tiktoken
4. Generate vector embeddings using OpenAI
5. Store vectors in Pinecone

---

## Retrieval Approach

For every retrieval request:

1. Generate embedding for the user query
2. Perform semantic similarity search in Pinecone
3. Retrieve the most relevant document chunks
4. Inject retrieved context into the final prompt

This Retrieval-Augmented Generation (RAG) approach significantly reduces hallucinations and ensures responses remain grounded in uploaded documents.

---

## Memory Implementation

Conversation history is stored per user session using local JSON files.

Before executing retrieval or tool calling, the latest user query is rewritten into a standalone question using previous conversation history.

This enables the assistant to resolve:

1. Pronouns
2. Follow-up questions
3. Topic continuity
4. User-specific references

without requiring the user to repeat context.

---

## Tool-Calling Strategy

The assistant uses OpenAI Native Function Calling.

The intent router determines whether a user request requires:

1. Knowledge Retrieval
2. Order Status Tool
3. Product Search Tool
4. Direct LLM Response

If a tool is required:

1. OpenAI selects the appropriate function
2. The function executes against local JSON data
3. Results are returned to the model
4. The LLM generates the final natural-language response

---

## Prompt Design

Different system prompts are used depending on the detected intent.

### Retrieval Prompt

The assistant is instructed to answer only using retrieved document context.

If the answer cannot be found, it must respond exactly:

> "I couldn't find that information in the uploaded documents."

---

### Tool Prompt

The assistant is instructed to invoke predefined functions whenever structured information is requested.

---

### Direct Prompt

Used for:

1. Greetings
2. General conversation
3. Context memory
4. Small talk

---

# Tech Stack

<div align="center">
  <table width="70%" style="border-collapse: collapse; border: 1px solid #ccc;">
    <thead>
      <tr style="border-bottom: 2px solid #ccc;">
        <th align="left" style="padding: 8px; border-right: 1px solid #ccc;">Component</th>
        <th align="left" style="padding: 8px;">Technology</th>
      </tr>
    </thead>
    <tbody>
      <tr style="border-bottom: 1px solid #eee;">
        <td align="left" style="padding: 8px; border-right: 1px solid #ccc;"><strong>Backend</strong></td>
        <td align="left" style="padding: 8px;">FastAPI</td>
      </tr>
      <tr style="border-bottom: 1px solid #eee;">
        <td align="left" style="padding: 8px; border-right: 1px solid #ccc;"><strong>Language</strong></td>
        <td align="left" style="padding: 8px;">Python</td>
      </tr>
      <tr style="border-bottom: 1px solid #eee;">
        <td align="left" style="padding: 8px; border-right: 1px solid #ccc;"><strong>LLM</strong></td>
        <td align="left" style="padding: 8px;">OpenAI</td>
      </tr>
      <tr style="border-bottom: 1px solid #eee;">
        <td align="left" style="padding: 8px; border-right: 1px solid #ccc;"><strong>Embeddings</strong></td>
        <td align="left" style="padding: 8px;">OpenAI Embeddings</td>
      </tr>
      <tr style="border-bottom: 1px solid #eee;">
        <td align="left" style="padding: 8px; border-right: 1px solid #ccc;"><strong>Vector Database</strong></td>
        <td align="left" style="padding: 8px;">Pinecone</td>
      </tr>
      <tr style="border-bottom: 1px solid #eee;">
        <td align="left" style="padding: 8px; border-right: 1px solid #ccc;"><strong>Tokenization</strong></td>
        <td align="left" style="padding: 8px;">tiktoken</td>
      </tr>
      <tr style="border-bottom: 1px solid #eee;">
        <td align="left" style="padding: 8px; border-right: 1px solid #ccc;"><strong>PDF Parsing</strong></td>
        <td align="left" style="padding: 8px;">pypdf</td>
      </tr>
      <tr>
        <td align="left" style="padding: 8px; border-right: 1px solid #ccc;"><strong>Containerization</strong></td>
        <td align="left" style="padding: 8px;">Docker</td>
      </tr>
    </tbody>
  </table>
</div>

---

# Setup Guide

## Prerequisites

1. Docker
2. OpenAI API Key
3. Pinecone API Key

---

## Clone Repository

```
git clone https://github.com/FHJibon/Mini-AI-Assistant.git
```
```
cd Mini-AI-Assistant
```

---

## Environment Variables

Create a `.env` file inside the `app/` directory.

```env
OPENAI_API_KEY=your_openai_api_key

PINECONE_API_KEY=your_pinecone_api_key
```

---

## Run with Docker

```bash
docker compose up --build
```

---

## API Documentation

Once the server is running, the interactive Swagger API documentation is available at:

- **Swagger UI:** [http://localhost:9000/docs](http://localhost:9000/docs)

---

# API Endpoints

## Knowledge Ingestion

### Upload Document

`POST /api/ingest/upload`

Supported formats

1. PDF
2. TXT
3. Markdown

---

### Generate Embeddings

`POST /api/ingest/ingest`

This endpoint:

1. Loads uploaded files
2. Splits documents
3. Generates embeddings
4. Uploads vectors to Pinecone

---

> **Important:** Upload and ingest your documents before testing the chat. Please note that the ingestion process may take some time depending on document size.

---

## Chat

`POST /api/chat/`

> **Note:** The following are tested conversations.

#### Example Request:

```json
{
  "user_id": "01",
  "session_id": "01",
  "message": "Hi, my name is jibon"
}
```

#### Example Response:
```json
{
  "answer": "Nice to meet you, Jibon! How can I help you today?"
}
```


#### Knowledge Retrieval:

User:
```
what does the Reddit Lead do?
```

Assistant:
```
The Reddit lead system constantly scans specific UK business and finance subreddits for people asking about UK tax, bookkeeping, or accounting, then uses AI to score how likely they are to need a paid accountant. High-quality leads (score 50–100) are saved into a Google Sheet with the post link, reasoning, and a suggested reply so you can follow up.
```


#### Knowledge Retrieval (Not in Documents):

User:
```
what is Acne?
```

Assistant:
```
I couldn't find that information in the uploaded documents.
```


#### Order Status Inquiry:

User:
```
What is update about ORD003??
```

Assistant:
```
Order ORD003 has been delivered, with an estimated delivery date of 2026-06-28.
```


#### Product Search:

User:
```
Do you have a power supply?
```

Assistant:
```
Yes, we have a Power Supply available for 11,500, and there are 7 units in stock.
```


#### Identity & Recall:

User:
```
Hi, my name is jibon
```

Assistant:
```
Nice to meet you, Jibon! How can I help you today?
```

User:
```
okay, tell me what is my name?
```

Assistant:
```
Your name is Jibon.
```

---

#### Follow-up Query & Price Comparison:

User:
```
Do you have SATA HDD?
```

Assistant:
```
Yes, we have SATA HDDs available for 6,200, and there are 18 units in stock.
```

User:
```
What is the cheapest Item do you have?
```

Assistant:
```
The cheapest item we have is Thermal Paste for 1,200.
```

---

# Error Handling

The application gracefully handles:

1. Unsupported file formats
2. Empty documents
3. Invalid upload requests
4. Missing API keys
5. Invalid Order IDs
6. Unknown products
7. Empty retrieval results
8. Pinecone connection failures
9. OpenAI API failures
10. Malformed LLM outputs/arguments

Appropriate HTTP status codes and descriptive error messages are returned to the client.

---

# About Me

**Author**: Ferdous Hasan  
**Date**: July 01, 2026