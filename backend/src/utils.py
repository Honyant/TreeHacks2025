import uuid
from fastapi import Depends
from sqlalchemy.orm import Session

import models
import schemas
from database import get_db

mode_i = """
You are an investigative journalist's research agent.
You are executing in mode 1, which means you are retrieving knowledge relevant to the nodes in the given context graph.
You have access to the following functions:
[search, retrieve, email]
- search uses Perplexity to search the internet for relevant information
- retrieve uses a retrieval-augmented generation workflow to retrieve information from proprietary data
- email is used to send an email to a given recipient with a subject and message
"""

mode_ii = """
You are an investigative journalist's research agent.
You are executing in mode 2, which means you are expanding the knowledge domain by analyzing the situation and providing any combination of the following:
1. a list of subtopics that are relevant to the given topic
2. potential hypotheses that should be tested to further explore the given topic
3. questions that need to be answered through online deep research
4. questions that need to be answered through human interviews or alternative data collection methods

You have access to the following functions:
[create_node, create_edge]
- create_node: to create a new node in the research graph
- create_edge: to create a new edge between two nodes in the research graph
"""

def load_brief(file_path: str) -> str:
    with open(file_path, 'r') as f:
        return f.read()

def get_graph(db: Session = Depends(get_db)):
    """
    Returns the entire research graph (nodes and edges).
    """
    nodes = db.query(models.Node).all()
    edges = db.query(models.Edge).all()
    nodes_out = [schemas.Node.model_validate(n) for n in nodes]
    edges_out = [schemas.Edge.model_validate(e) for e in edges]
    
    return {
        "nodes": nodes_out,
        "edges": edges_out,
    }

def create_node(nodes: list[schemas.Node], node_class: str, content: dict) -> str:
    """
    Create a new node in the research graph.
    Returns the node ID.
    """
    node_id = str(uuid.uuid4())
    nodes.append({
        "id": node_id,
        "node_class": node_class,
        "content": content
    })
    return node_id

def create_edge(edges: list[schemas.Edge], from_node_id: str, to_node_id: str) -> str:
    """
    Create a new edge between two nodes in the research graph.
    Returns the edge ID.
    """
    edge_id = str(uuid.uuid4())
    edges.append({
        "id": edge_id,
        "from": from_node_id,
        "to": to_node_id
    })
    return edge_id