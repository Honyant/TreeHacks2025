from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import models
from database import engine
from routes import router
import asyncio
import threading
from engine import check_for_replies

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
async def startup_event():
    """Start the email checker in a separate thread when the FastAPI app starts"""

    def run_email_checker():
        check_for_replies()

    # Start the email checker in a separate thread
    email_thread = threading.Thread(target=run_email_checker, daemon=True)
    email_thread.start()
