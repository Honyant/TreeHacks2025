import uuid
from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from sqlalchemy import or_
from typing import List

import models
import schemas
import engine as processing_engine
from engine import init_agent, execute_mode_ii
from database import SessionLocal
from utils import get_db, get_node_by_id
from RAG import init_rag
from external_functions import call_phone_number

router = APIRouter()

nodes = []
chat_messages = []
RAG_client = None
RAG_collection = None

@router.post("/start", response_model=schemas.ChatMessageOut)
def start():
    global nodes
    global chat_messages
    global RAG_client
    global RAG_collection
    
    if not RAG_client or not RAG_collection:
        RAG_client, RAG_collection = init_rag()

    root_node = init_agent(nodes, None)
    # set found node id to 0
    found_node = get_node_by_id(nodes, root_node)
    found_node.id = "0"
    found_node.type = "root"

    # create output object:
    chat_history = [schemas.ChatMessage.model_validate(msg) for msg in chat_messages]
    nodes_dict = {node.id: schemas.NodeV2.model_validate(node) for node in nodes}
    output = schemas.ChatMessageOut(chat_history=chat_history, graph=nodes_dict)
    return output


@router.post("/generate", response_model=schemas.ChatMessageOut)
def generate(payload: schemas.GeneratePayload):
    global nodes
    global chat_messages
    print(nodes)
    active_node = payload.active_node_uuid
    found_node = get_node_by_id(nodes, active_node)
    if found_node.id == "0":
        print("Executing mode ii")
        execute_mode_ii(nodes, active_node)
    elif found_node and found_node.metadata.source == "mode_ii":
        print("Executing mode i")
        # execute_mode_i(nodes, active_node)
    elif found_node and found_node.metadata.source == "mode_i":
        if found_node.type == "question":
            pass
        elif found_node.type == "email":
            print("Executing email")
        elif found_node.type == "call":
            print("Executing call")
    else:
        execute_mode_ii(nodes, active_node)

    # create output object:
    chat_history = [schemas.ChatMessage.model_validate(msg) for msg in chat_messages]
    nodes_dict = {node.id: schemas.NodeV2.model_validate(node) for node in nodes}
    output = schemas.ChatMessageOut(chat_history=chat_history, graph=nodes_dict)
    return output


@router.post("/chat", response_model=schemas.ChatMessageOut)
def chat_endpoint(payload: schemas.ChatMessageCreate):
    global nodes
    global chat_messages
    message = payload.message
    role = payload.role
    id = payload.node_id

    # if the node is a question, we modify the question node and add on the response from the user:
    chat_messages.append(
        schemas.ChatMessage(
            id=str(uuid.uuid4()),
            role=role,
            node_id=id,
            message=message,
            timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        )
    )
    found_node = get_node_by_id(nodes, id)
    if found_node and found_node.type == "question":
        found_node.content = message

    # create output object:
    chat_history = [schemas.ChatMessage.model_validate(msg) for msg in chat_messages]
    nodes_dict = {node.id: schemas.NodeV2.model_validate(node) for node in nodes}
    output = schemas.ChatMessageOut(chat_history=chat_history, graph=nodes_dict)
    return output


@router.post("/upload", response_model=schemas.ChatMessageOut)
def upload_endpoint(payload: schemas.FileUpload):
    global nodes
    global chat_messages
    message = payload.message
    active_node_uuid = payload.active_node_uuid
    filename = payload.filename
    content = payload.content
    mime_type = payload.mime_type
    size = payload.size

    # create file node (need to add to rag db)
    file_node = schemas.NodeV2(
        id=str(uuid.uuid4()),
        name=filename,
        type="file",
        content=content,
        metadata=schemas.NodeMetadata(
            source="upload",
            timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
        ),
        children=[],
    )
    # add file to be a child of the active node
    active_node = get_node_by_id(nodes, active_node_uuid)
    if active_node:
        active_node.children.append(file_node)
    else:
        raise HTTPException(status_code=404, detail="Active node not found")

    # create output object:
    chat_history = [schemas.ChatMessage.model_validate(msg) for msg in chat_messages]
    nodes_dict = {node.id: schemas.NodeV2.model_validate(node) for node in nodes}
    output = schemas.ChatMessageOut(chat_history=chat_history, graph=nodes_dict)
    return output


@router.get("/phonecall/{phone_number}")
def phonecall_endpoint(phone_number: str, background_tasks: BackgroundTasks):
    # Start the phone call in a non-blocking way
    id_to_update = str(uuid.uuid4())

    # Create a background task to handle the call result and update nodes
    def process_call_result(phone_number: str):
        global nodes
        print(f"[Phone Call] Processing call result for {phone_number}")
        call_result = call_phone_number(phone_number)
        print(f"[Phone Call] Call result: {call_result}")
        # Create a new node for the phone call
        call_node = schemas.NodeV2(
            id=id_to_update,
            name=f"Phone call to {phone_number}",
            type="call",
            content=call_result,
            metadata=schemas.NodeMetadata(
                source="phone_call",
                timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
            ),
            children=[],
        )
        nodes.append(call_node)
        print(f"[Phone Call] Added call node to nodes: {id_to_update}")

    # Add the task to background_tasks
    background_tasks.add_task(process_call_result, phone_number)

    return {
        "status": "Call initiated",
        "message": f"Calling {phone_number}",
        "node_id": id_to_update,
    }


# @router.post("/chat", response_model=schemas.ChatMessageOut)
# def chat_endpoint(payload: schemas.ChatMessageCreate, db: Session = Depends(get_db)):
#     """
#     Accepts a user message, updates the chat history,
#     processes the message via the internal engine, and returns:
#       - updated chat history
#       - entire research graph (nodes and edges)
#     """
#     message_text = payload.message
#     if not message_text:
#         raise HTTPException(status_code=400, detail="No message provided")

#     # Append user message to chat history
#     user_msg = models.ChatMessage(
#         id=str(uuid.uuid4()),
#         role="user",
#         message=message_text,
#         timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
#     )
#     db.add(user_msg)
#     db.commit()

#     # Retrieve full chat history (ordered by timestamp)
#     chat_history_rows = (
#         db.query(models.ChatMessage).order_by(models.ChatMessage.timestamp).all()
#     )
#     chat_history = [
#         {"role": msg.role, "message": msg.message} for msg in chat_history_rows
#     ]

#     # Process the chat with the engine (LLM, agent actions, etc.)
#     result = processing_engine.process_chat(message_text, chat_history)

#     # Append assistant response to chat history
#     assistant_msg = models.ChatMessage(
#         id=str(uuid.uuid4()),
#         role="assistant",
#         message=result["assistant_message"],
#         timestamp=datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S"),
#     )
#     db.add(assistant_msg)
#     db.commit()

#     # Process new nodes and edges
#     for node_data in result.get("new_nodes", []):
#         node = models.Node(
#             id=node_data["id"],
#             node_class=node_data["node_class"],
#             content=node_data["content"],
#         )
#         db.add(node)
#     for edge_data in result.get("new_edges", []):
#         edge = models.Edge(
#             id=edge_data["id"],
#             from_node_id=edge_data["from"],
#             to_node_id=edge_data["to"],
#         )
#         db.add(edge)
#     db.commit()

#     # Retrieve the full research graph
#     nodes = db.query(models.Node).all()
#     edges = db.query(models.Edge).all()
#     nodes_out = [schemas.Node.from_orm(n) for n in nodes]
#     edges_out = [schemas.Edge.from_orm(e) for e in edges]

#     # Retrieve updated chat history
#     chat_history_rows = (
#         db.query(models.ChatMessage).order_by(models.ChatMessage.timestamp).all()
#     )
#     chat_history_out = [schemas.ChatMessage.from_orm(msg) for msg in chat_history_rows]

#     return {
#         "chat_history": chat_history_out,
#         "graph": {"nodes": nodes_out, "edges": edges_out},
#     }


# @router.post("/nodes", response_model=schemas.Node)
# def add_node(node: schemas.NodeV2, db: Session = Depends(get_db)):
#     """
#     Manually add a node to the research graph.
#     """
#     new_node = models.Node(
#         id=str(uuid.uuid4()), node_class=node.node_class, content=node.content
#     )
#     db.add(new_node)
#     db.commit()
#     db.refresh(new_node)
#     return new_node


# @router.delete("/nodes/{node_id}")
# def delete_node(node_id: str, db: Session = Depends(get_db)):
#     """
#     Manually delete a node (and any associated edges) from the research graph.
#     """
#     node = db.query(models.Node).filter(models.Node.id == node_id).first()
#     if not node:
#         raise HTTPException(status_code=404, detail="Node not found")
#     db.delete(node)
#     # Delete edges connected to this node using SQLAlchemy's or_ helper
#     edges = (
#         db.query(models.Edge)
#         .filter(
#             or_(models.Edge.from_node_id == node_id, models.Edge.to_node_id == node_id)
#         )
#         .all()
#     )
#     for edge in edges:
#         db.delete(edge)
#     db.commit()
#     return {"detail": "Node and associated edges deleted"}
