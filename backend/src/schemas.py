from datetime import datetime
from pydantic import BaseModel
from typing import Any, Dict

class NodeBase(BaseModel):
    node_class: str
    content: Dict[str, Any]

class NodeCreate(NodeBase):
    pass

class Node(NodeBase):
    id: str
    
    model_config = {
        "from_attributes": True
    }

class EdgeBase(BaseModel):
    from_node_id: str
    to_node_id: str

class EdgeCreate(EdgeBase):
    pass

class Edge(EdgeBase):
    id: str
    
    model_config = {
        "from_attributes": True
    }

class ChatMessageBase(BaseModel):
    role: str
    message: str

class ChatMessageCreate(ChatMessageBase):
    pass

class ChatMessage(ChatMessageBase):
    id: str
    timestamp: datetime
    
    model_config = {
        "from_attributes": True
    }
