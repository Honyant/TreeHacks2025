import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List

import models
import schemas
import engine as processing_engine
from database import SessionLocal

router = APIRouter()


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.post("/chat")
def chat_endpoint(payload: schemas.ChatMessageCreate, db: Session = Depends(get_db)):
    """
    Accepts a user message, updates the chat history,
    processes the message via the internal engine, and returns:
      - updated chat history
      - entire research graph (nodes and edges)
    """
    message_text = payload.get("message")
    if not message_text:
        raise HTTPException(status_code=400, detail="No message provided")

    # Append user message to chat history
    user_msg = models.ChatMessage(
        id=str(uuid.uuid4()),
        role="user",
        message=message_text,
        timestamp=datetime.utcnow(),
    )
    db.add(user_msg)
    db.commit()

    # Retrieve full chat history (ordered by timestamp)
    chat_history_rows = (
        db.query(models.ChatMessage).order_by(models.ChatMessage.timestamp).all()
    )
    chat_history = [
        {"role": msg.role, "message": msg.message} for msg in chat_history_rows
    ]

    # Process the chat with the engine (LLM, agent actions, etc.)
    result = processing_engine.process_chat(message_text, chat_history)

    # Append assistant response to chat history
    assistant_msg = models.ChatMessage(
        id=str(uuid.uuid4()),
        role="assistant",
        message=result["assistant_message"],
        timestamp=datetime.utcnow(),
    )
    db.add(assistant_msg)
    db.commit()

    # Process new nodes and edges
    for node_data in result.get("new_nodes", []):
        node = models.Node(
            id=node_data["id"],
            node_class=node_data["node_class"],
            content=node_data["content"],
        )
        db.add(node)
    for edge_data in result.get("new_edges", []):
        edge = models.Edge(
            id=edge_data["id"],
            from_node_id=edge_data["from"],
            to_node_id=edge_data["to"],
        )
        db.add(edge)
    db.commit()

    # Retrieve the full research graph
    nodes = db.query(models.Node).all()
    edges = db.query(models.Edge).all()
    nodes_out = [schemas.Node.from_orm(n) for n in nodes]
    edges_out = [schemas.Edge.from_orm(e) for e in edges]

    # Retrieve updated chat history
    chat_history_rows = (
        db.query(models.ChatMessage).order_by(models.ChatMessage.timestamp).all()
    )
    chat_history_out = [schemas.ChatMessage.from_orm(msg) for msg in chat_history_rows]

    return {
        "chat_history": chat_history_out,
        "graph": {"nodes": nodes_out, "edges": edges_out},
    }


@router.post("/nodes", response_model=schemas.Node)
def add_node(node: schemas.NodeCreate, db: Session = Depends(get_db)):
    """
    Manually add a node to the research graph.
    """
    new_node = models.Node(
        id=str(uuid.uuid4()), node_class=node.node_class, content=node.content
    )
    db.add(new_node)
    db.commit()
    db.refresh(new_node)
    return new_node


@router.delete("/nodes/{node_id}")
def delete_node(node_id: str, db: Session = Depends(get_db)):
    """
    Manually delete a node (and any associated edges) from the research graph.
    """
    node = db.query(models.Node).filter(models.Node.id == node_id).first()
    if not node:
        raise HTTPException(status_code=404, detail="Node not found")
    db.delete(node)
    # Delete edges connected to this node using SQLAlchemy's or_ helper
    edges = (
        db.query(models.Edge)
        .filter(
            or_(models.Edge.from_node_id == node_id, models.Edge.to_node_id == node_id)
        )
        .all()
    )
    for edge in edges:
        db.delete(edge)
    db.commit()
    return {"detail": "Node and associated edges deleted"}
