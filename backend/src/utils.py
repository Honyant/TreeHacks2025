import uuid
import json
from fastapi import Depends
from sqlalchemy.orm import Session

import models
import schemas
from datetime import datetime
from database import SessionLocal

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def load_brief(file_path: str) -> str:
    with open(file_path, 'r') as f:
        return f.read()

# def get_graph(db: Session = Depends(get_db)):
#     """
#     Returns the entire research graph (nodes and edges).
#     """
#     nodes = db.query(models.NodeV2).all()
#     nodes_out = [schemas.NodeV2.model_validate(n) for n in nodes]
#     return nodes_out

def create_node(nodes: list[schemas.NodeV2], name: str, type: str, content: str, source: str, timestamp: datetime) -> str:
    """
    Create a new node in the research graph using NodeV2 schema.
    Returns the node ID.
    """
    node_id = str(uuid.uuid4())
    nodes.append(schemas.NodeV2(
        id=node_id,
        name=name,
        type=schemas.NodeType(type),
        content=content,
        metadata=schemas.NodeMetadata(
            source=source,
            timestamp=timestamp.strftime("%Y-%m-%d %H:%M:%S")
        ),
        children=[]
    ))
    return node_id

def update_node_children(nodes: list[schemas.NodeV2], parent_id: str, child_id: str) -> None:
    for node in nodes:
        if node.id == parent_id:
            node.children.append(child_id)
            break

def get_node_by_id(nodes: list[schemas.NodeV2], node_id: str) -> schemas.NodeV2:
    for node in nodes:
        print(node.id, node_id)
        if node.id == node_id:
            return node
    return None

def nodes_to_string(nodes: list[schemas.NodeV2]) -> str:
    return "\n".join([f"Title: {node.name}\nContent: {node.content}\n" for node in nodes])

def print_nodes(nodes: list[schemas.NodeV2]) -> None:
    for node in nodes:
        print(f"\nTitle: {node.name}")
        print(f"Content: {node.content}")

def export_nodes(nodes: list[schemas.NodeV2], file_path: str) -> None:
    with open(file_path, 'w') as f:
        json.dump({node.id: node.model_dump() for node in nodes}, f, indent=2)


mode_i = """
You are an investigative journalist's research agent.
You are executing in mode 1, which means you are retrieving knowledge relevant to the active node in the given context graph.

Please only output tool uses and nothing else.
Include at least three different types of tool uses in your output.

You have access to the following tools:
[ask, search, email, phone]
- ask is used to ask a question to the user.
- search uses Perplexity to search the internet for relevant information.
- email is used to send an email to a given recipient with a subject and message.
- phone is used to call a given individual using a separate phone AI agent.

DO NOT ONLY USE THE PHONE TOOL.
DO NOT CALL MORE THAN ONE PERSON BECAUSE PEOPLE ARE BUSY.
CREATE AT LEAST FIVE TOOL CALLS IN YOUR OUTPUT.
"""
# You have access to the following tools:
# [ask, search, retrieve, email, phone]
# - ask is used to ask a question to the user.
# - search uses Perplexity to search the internet for relevant information.
# - retrieve uses a retrieval-augmented generation workflow to retrieve information from proprietary data.
# - email is used to send an email to a given recipient with a subject and message.
# - phone is used to call a given individual using a separate phone AI agent.

mode_ii = """
You are an investigative journalist's research agent.
Your job is to expand the knowledge domain by analyzing the situation at the current node and generating new insights.
Some potential insights you can generate are:
1. a list of subtopics that are relevant to the given topic
2. potential hypotheses that should be tested to further explore the given topic
3. questions that need to be answered through online deep research
4. questions that need to be answered through human interviews or alternative data collection methods

Each node should be an individual topic without subtopics.
Please separate subtopics into distinct nodes.
Do not create frivolous nodes that are similar to other existing nodes.
Output the list of nodes in the order of priority and importance.
Limit the number of nodes you create to 4.
Only the first 4 nodes will be considered.
Please keep the titles concise (around 5 words) and unique to the given node.
Do not repeat general information in the titles that relate to other nodes.
Do not mention the word node in the content.

You have access to the following functions:
[create_node]
- create_node: to create a new node in the research graph
"""

mode_i_tools = [
    {
        "type": "function",
        "function": {
            "name": "ask",
            "description": "Ask a question to the user.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "5-word summary of the question topic"
                    },
                    "question": {
                        "type": "string",
                        "description": "The question to ask the user"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "phone",
            "description": "Call a given individual using a separate phone AI agent.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "5-word summary of the call topic"
                    },
                    "topic": {
                        "type": "string",
                        "description": "The topic of the call"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search",
            "description": "Search the internet for relevant information.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "5-word summary of the search topic"
                    },
                    "query": {
                        "type": "string",
                        "description": "The query to search the internet for"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "retrieve",
            "description": "Retrieve a file from proprietary database.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "5-word summary of the retrieval topic"
                    },
                    "query": {
                        "type": "string",
                        "description": "The query to retrieve information from RAG database"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "email",
            "description": "Send an email to a given recipient with a subject and message.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "5-word summary of the email topic"
                    },
                    "recipient": {
                        "type": "string",
                        "description": "The email address of the recipient"
                    },
                    "subject": {
                        "type": "string",
                        "description": "The subject of the email"
                    },
                    "message": {
                        "type": "string",
                        "description": "The message to send in the email"
                    }
                }
            }
        }
    }
]


mode_ii_tools = [
    {
        "type": "function",
        "function": {
            "name": "create_node",
            "description": "Create a new node in the research graph.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Title of the node"
                    },
                    "type": {
                        "type": "string",
                        "enum": ["text", "image", "audio", "link"],
                        "description": "Type of the node content"
                    },
                    "content": {
                        "type": "string",
                        "description": "The main content of the node"
                    },
                    "metadata": {
                        "type": "object",
                        "properties": {
                            "source": {
                                "type": "string",
                                "description": "Source of the node content"
                            },
                            "timestamp": {
                                "type": "string",
                                "format": "date-time",
                                "description": "Timestamp of when the node was created"
                            }
                        },
                        "required": ["source", "timestamp"]
                    },
                    "children": {
                        "type": "array",
                        "items": {
                            "type": "string"
                        },
                        "description": "List of IDs of child nodes"
                    }
                },
                "required": ["name", "type", "content", "metadata"],
                "additionalProperties": False
            }
        }
    }
]