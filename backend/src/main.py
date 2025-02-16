from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import models
from database import engine
from routes import router
import asyncio
import threading
from engine import check_for_replies
from routes import nodes, RAG_client, RAG_collection
from RAG import init_rag
from utils import get_node_by_id
from engine import init_agent

models.Base.metadata.create_all(bind=engine)

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(router)


@app.on_event("startup")
async def init_rag_at_startup():
    global nodes, RAG_client, RAG_collection
    
    """
    Initialize the RAG client, collection, and the root graph node at server startup.
    This will run only once when the FastAPI application starts.
    """
    if not nodes:  # Only initialize if nodes isn't already populated
        # RAG_client, RAG_collection = init_rag()
        root_node = init_agent(nodes, None)
        found_node = get_node_by_id(nodes, root_node)
        found_node.id = "0"
        found_node.type = "root"

# @app.on_event("startup")
# async def startup_event():
#     """Start the email checker in a separate thread when the FastAPI app starts"""

#     def run_email_checker():
#         check_for_replies()

#     # Start the email checker in a separate thread
#     email_thread = threading.Thread(target=run_email_checker, daemon=True)
#     email_thread.start()
