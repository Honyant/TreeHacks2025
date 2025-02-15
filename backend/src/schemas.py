from datetime import datetime
from pydantic import BaseModel
from typing import Any, Dict, List


class NodeContent(BaseModel):
    text: str
    metadata: Dict[str, Any]


class NodeBase(BaseModel):
    node_class: str
    content: NodeContent


class NodeCreate(NodeBase):
    pass


class Node(NodeBase):
    id: str

    model_config = {"from_attributes": True}


class EdgeBase(BaseModel):
    from_node_id: str
    to_node_id: str


class EdgeCreate(EdgeBase):
    pass


class Edge(EdgeBase):
    id: str

    model_config = {"from_attributes": True}


class ChatMessageBase(BaseModel):
    message: str


class ChatMessageCreate(ChatMessageBase):
    pass


class ChatMessage(ChatMessageBase):
    id: str
    timestamp: datetime

    model_config = {"from_attributes": True}


class Graph(BaseModel):
    nodes: List[Node]
    edges: List[Edge]


class ChatMessageOut(BaseModel):
    chat_history: List[ChatMessage]
    graph: Graph
