import uuid
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
import os

from openai import OpenAI

load_dotenv()

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("Missing OpenAI API key in environment variables.")

client = OpenAI(api_key=api_key)

# External functions

def query_perplexity(query: str) -> str:
    print(f"[Perplexity API] Query: {query}")
    return f"Simulated perplexity result for query: '{query}'"


def send_email(to: str, subject: str, body: str) -> str:
    print(f"[Email Simulation] To: {to}, Subject: {subject}\nBody: {body}")
    return "Email sent."


def video_analysis(video_url: str) -> str:
    print(
        "[Video Analysis Simulation] Steps: Download video, extract frames, analyze frames, summarize results."
    )
    return "Video analysis simulated."

# Engine using function calling

def process_chat(user_message: str, chat_history: list) -> dict:
    """
    Process the chat message using the OpenAI API with function calling.
    The chat_history is a list of dicts with keys "role" and "message".
    This function returns a dict with the assistant's final message,
    along with any new nodes/edges generated.
    """
    messages = [
        {"role": msg["role"], "content": msg["message"]} for msg in chat_history
    ]
    messages.append({"role": "user", "content": user_message})

    tools = [
        {
            "type": "function",
            "function": {
                "name": "send_email",
                "description": "Send an email to a given recipient with a subject and message.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "to": {
                            "type": "string",
                            "description": "The recipient email address.",
                        },
                        "subject": {
                            "type": "string",
                            "description": "The email subject line.",
                        },
                        "body": {
                            "type": "string",
                            "description": "The body of the email.",
                        },
                    },
                    "required": ["to", "subject", "body"],
                    "additionalProperties": False,
                },
                "strict": True,
            },
        },
        {
            "type": "function",
            "function": {
                "name": "query_perplexity",
                "description": "Query the Perplexity API with a research query.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "query": {
                            "type": "string",
                            "description": "The research query.",
                        }
                    },
                    "required": ["query"],
                    "additionalProperties": False,
                },
                "strict": True,
            },
        },
        {
            "type": "function",
            "function": {
                "name": "video_analysis",
                "description": "Simulate video analysis steps for a provided video URL.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "video_url": {
                            "type": "string",
                            "description": "The URL of the video to analyze.",
                        }
                    },
                    "required": ["video_url"],
                    "additionalProperties": False,
                },
                "strict": True,
            },
        },
        {
            "type": "function",
            "function": {
                "name": "create_node",
                "description": "Create a new research node in the graph.",
                "parameters": {
                    "type": "object",
                    "properties": {
                        "node_class": {
                            "type": "string",
                            "description": "The class of the node (e.g., heading, tweet, report, video).",
                        },
                        "text": {
                            "type": "string",
                            "description": "The content text for the node.",
                        },
                    },
                    "required": ["node_class", "text"],
                    "additionalProperties": False,
                },
                "strict": True,
            },
        },
    ]

    response = client.chat.completions.create(
        model="gpt-4o", messages=messages, tools=tools, temperature=0.7
    )
    message = response.choices[0].message

    assistant_message = ""
    new_nodes = []
    new_edges = []

    if hasattr(message, "tool_calls") and message.tool_calls:
        for tool_call in message.tool_calls:
            function_name = tool_call.function.name
            arguments_str = tool_call.function.arguments
            try:
                args = json.loads(arguments_str)
            except Exception as e:
                logging.error(f"Error parsing function arguments: {e}")
                args = {}

            if function_name == "send_email":
                result = send_email(**args)
                node = {
                    "id": str(uuid.uuid4()),
                    "node_class": "email",
                    "content": {
                        "text": f"Email sent to: {args.get('to')}\nSubject: {args.get('subject')}\nBody: {args.get('body')}",
                        "metadata": {
                            "source": "Email",
                            "recipient": args.get("to"),
                            "timestamp": datetime.utcnow().isoformat(),
                        },
                    },
                }
                new_nodes.append(node)
            elif function_name == "query_perplexity":
                result_text = query_perplexity(args.get("query", ""))
                node = {
                    "id": str(uuid.uuid4()),
                    "node_class": "report",
                    "content": {
                        "text": result_text,
                        "metadata": {
                            "source": "Perplexity",
                            "timestamp": datetime.utcnow().isoformat(),
                        },
                    },
                }
                new_nodes.append(node)
                result = result_text
            elif function_name == "video_analysis":
                result = video_analysis(args.get("video_url", ""))
            elif function_name == "create_node":
                node_class = args.get("node_class")
                text = args.get("text")
                node = {
                    "id": str(uuid.uuid4()),
                    "node_class": node_class,
                    "content": {
                        "text": text,
                        "metadata": {
                            "source": "LLM",
                            "timestamp": datetime.utcnow().isoformat(),
                        },
                    },
                }
                new_nodes.append(node)
                result = "Node created."
            else:
                result = "Function not recognized."

            messages.append(message)
            messages.append(
                {"role": "tool", "tool_call_id": tool_call.id, "content": result}
            )

        final_response = client.chat.completions.create(
            model="gpt-4o", messages=messages, tools=tools, temperature=0.7
        )
        assistant_message = final_response.choices[0].message.content
    else:
        assistant_message = message.content

    # If the assistant asks a query (using "QUERY:"), append a clarifying request.
    if "QUERY:" in assistant_message:
        parts = assistant_message.split("QUERY:")
        assistant_text = parts[0].strip()
        query_text = parts[1].strip()
        assistant_message = (
            assistant_text + "\nPlease provide additional info: " + query_text
        )

    return {
        "assistant_message": assistant_message,
        "new_nodes": new_nodes,
        "new_edges": new_edges,
    }
