# Deep Research Backend

This is a FastAPI-based backend for a deep research product featuring a tree-like research graph and a chat interface. The chat interface interacts with the graph by deploying agents to expand nodes based on chat responses.

## Overview

- **Chat Interface:**  
  Accepts user messages, updates chat history, and invokes an LLM (OpenAI API) to process the message. The LLM may instruct actions such as:
  - Expanding the research graph with new nodes/edges.
  - Querying the user for additional info (via chat).
  - Triggering actions like RAG, email requests (simulated), Perplexity AI queries, or video analysis (logging steps).

- **Research Graph:**  
  Uses a ReactFlow-like schema where:
  - **Node:**  
    - `id`: UUID  
    - `node_class`: Enum (e.g., heading, tweet, report, video, etc.)  
    - `content`: Free JSON (with metadata like source and timestamp)
  - **Edge:**  
    - `id`: UUID  
    - `from_node_id`: Source node's UUID  
    - `to_node_id`: Destination node's UUID

- **Persistence:**  
  Chat history and the research graph are stored in SQLite.

## Backend Structure

The project is split into multiple modules:

- **`database.py`:**  
  Database configuration using SQLAlchemy and SQLite.

- **`models.py`:**  
  SQLAlchemy models for Nodes, Edges, and Chat Messages.

- **`schemas.py`:**  
  Pydantic schemas for API validation.

- **`engine.py`:**  
  Internal chat processing engine:
  - Uses the OpenAI API to generate responses.
  - Simulates actions such as node expansion, Perplexity AI calls, email sending, and video analysis logging.

- **`routes.py`:**  
  API endpoints:
  - **`/chat`:** Accepts user messages, processes them, updates chat history, and returns the updated research graph.
  - **`/nodes`:** Manual node addition.
  - **`/nodes/{node_id}`:** Manual node deletion.

- **`main.py`:**  
  Entry point that creates the database tables and starts the FastAPI app.

## How to Run

1. **Set Up Environment:**

   ```bash
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configure OpenAI API Key:**

   In `.env`, set the `OPENAI_API_KEY` environment variable to your OpenAI API key.

3. **Configure the RAG Environment:**
   
   `docker run -p 8080:8080 -p 50051:50051 cr.weaviate.io/semitechnologies/weaviate:1.28.4`

5. **Run the App:**

   ```bash
   cd src
   uvicorn main:app --reload
   ```

6. **Access Documentation:**

   Navigate to [http://localhost:8000/docs](http://localhost:8000/docs) for interactive API docs.

## How to Test

- **Swagger UI:**  
  Use the interactive docs at `/docs` to test the `/chat` and `/nodes` endpoints.
