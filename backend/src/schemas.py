from datetime import datetime
from pydantic import BaseModel
from typing import Any, Dict, List


class NodeMetadata(BaseModel):
    source: str
    timestamp: datetime


class NodeContent(BaseModel):
    text: str
    metadata: NodeMetadata


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


from enum import Enum


class RoleEnum(str, Enum):
    user = "user"
    assistant = "assistant"


class ChatMessageBase(BaseModel):
    role: RoleEnum
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
