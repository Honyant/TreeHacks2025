import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, Text, JSON
from database import Base

class Node(Base):
    __tablename__ = "nodes"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    node_class = Column(String, nullable=False)  # e.g., heading, tweet, report, video, etc.
    content = Column(JSON, nullable=False)  # free JSON with metadata

class Edge(Base):
    __tablename__ = "edges"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    from_node_id = Column(String, ForeignKey("nodes.id"), nullable=False)
    to_node_id = Column(String, ForeignKey("nodes.id"), nullable=False)

class ChatMessage(Base):
    __tablename__ = "chat_messages"
    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    role = Column(String, nullable=False)  # "user" or "assistant"
    message = Column(Text, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow)
