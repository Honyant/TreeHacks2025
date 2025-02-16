from datetime import datetime
from pydantic import BaseModel
from typing import Any, Dict, List
from enum import Enum



class ModelOutput(BaseModel):
    title: str
    content: str


class NodeType(str, Enum):  # to be displayed differently in the UI
    text = "text"
    image = "image"
    audio = "audio"
    link = "link"


class NodeMetadata(BaseModel):
    source: str
    timestamp: datetime


class NodeV2(BaseModel):
    id: str
    name: str  # title of the node
    type: NodeType  # type of the node
    content: str
    metadata: NodeMetadata
    children: List[str]  # ids of the children nodes

    model_config = {"from_attributes": True}


# deprecate below.
class NodeContent(BaseModel):
    text: str
    metadata: NodeMetadata


class NodeBase(BaseModel):
    node_class: str
    title: str
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
    nodes: List[NodeV2]
    edges: List[Edge]


class ChatMessageOut(BaseModel):
    chat_history: List[ChatMessage]
    graph: Graph
