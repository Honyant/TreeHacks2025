from datetime import datetime
from pydantic import BaseModel
from typing import Any, Dict, List
from enum import Enum


class ModelOutput(BaseModel):
    title: str
    content: str

class NodeType(str, Enum):  # to be displayed differently in the UI
    root = "root"
    text = "text"  # mode ii
    question = "question"  # mode i
    email = "email"  # mode i
    call = "call"  # mode i
    file = "file"  # mode i
    search = "search"  # mode i


class NodeMetadata(BaseModel):
    source: str
    timestamp: str  # Changed from datetime to str


class NodeV2(BaseModel):
    id: str
    name: str  # title of the node
    type: NodeType  # type of the node
    content: str
    metadata: NodeMetadata
    children: List[str]  # ids of the children nodes

    model_config = {"from_attributes": True}


class RoleEnum(str, Enum):
    user = "user"
    assistant = "assistant"


class ChatMessageBase(BaseModel):
    role: RoleEnum
    node_id: str
    message: str

class ChatMessageCreate(ChatMessageBase):
    pass


class ChatMessage(ChatMessageBase):
    id: str
    timestamp: datetime

    model_config = {"from_attributes": True}


class ChatMessageOut(BaseModel):
    chat_history: List[ChatMessage]
    graph: Dict[str, NodeV2]

class FileUpload(BaseModel):
    message: str
    active_node_uuid: str
    filename: str
    content: str
    mime_type: str
    size: int  # file size in bytes

class GeneratePayload(BaseModel):
    active_node_uuid: str
