import uuid
import logging
from datetime import datetime
from openai import OpenAI
from dotenv import load_dotenv
import os

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("Missing OpenAI API key in environment variables.")

client = OpenAI(api_key=api_key)
import logging


def query_perplexity(query: str) -> str:
    print(f"[Perplexity API] Query: {query}")
    return f"Simulated perplexity result for query: '{query}'"

def send_email(recipient: str, subject: str, body: str):
    print(f"[Email Simulation] To: {recipient}, Subject: {subject}\nBody: {body}")

def process_chat(user_message: str, chat_history: list) -> dict:
    """
    Process the chat message using the OpenAI API.
    The chat_history is expected to be a list of dicts with keys "role" and "message".
    The response may instruct additional actions like node expansion, querying the user,
    calling perplexity, sending emails, or performing video analysis.
    """
    messages = [{"role": msg["role"], "content": msg["message"]} for msg in chat_history]
    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(model="gpt-3.5-turbo",
    messages=messages,
    temperature=0.7)
    assistant_message = response.choices[0].message.content

    new_nodes = []
    new_edges = []

    if "expand" in assistant_message.lower():
        new_node = {
            "id": str(uuid.uuid4()),
            "node_class": "heading",
            "content": {
                "text": "LLM Expansion Node",
                "metadata": {"source": "LLM", "timestamp": datetime.utcnow().isoformat()}
            }
        }
        new_nodes.append(new_node)

    if "perplexity" in assistant_message.lower():
        perplexity_result = query_perplexity("Research query related to: " + user_message)
        new_node = {
            "id": str(uuid.uuid4()),
            "node_class": "report",
            "content": {
                "text": perplexity_result,
                "metadata": {"source": "Perplexity", "timestamp": datetime.utcnow().isoformat()}
            }
        }
        new_nodes.append(new_node)

    if "email" in assistant_message.lower():
        send_email("journalist@example.com", "Request for information",
                   "Please provide details on your source or proprietary info.")

    if "video" in assistant_message.lower():
        print("[Video Analysis Simulation] Steps: Download video, extract frames, analyze frames, summarize results.")

    # If the response needs to query the user (for proprietary info, etc.),
    # assume the LLM prepends a "QUERY:" keyword.
    if "QUERY:" in assistant_message:
        parts = assistant_message.split("QUERY:")
        assistant_text = parts[0].strip()
        query_text = parts[1].strip()
        # Append a clarifying question to the assistant message.
        assistant_message = assistant_text + "\nPlease provide additional info: " + query_text

    return {"assistant_message": assistant_message, "new_nodes": new_nodes, "new_edges": new_edges}
