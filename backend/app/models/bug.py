import datetime
from sqlalchemy import Column, Integer, String, Text, Date, DateTime, ForeignKey, Table
from sqlalchemy.orm import relationship
from backend.app.database import Base

bug_tags = Table(
    'bug_tags',
    Base.metadata,
    Column('bug_id', Integer, ForeignKey('bugs.id', ondelete="CASCADE"), primary_key=True),
    Column('tag_id', Integer, ForeignKey('tags.id', ondelete="CASCADE"), primary_key=True)
)

class Bug(Base):
    __tablename__ = 'bugs'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    bug_code = Column(String(20), unique=True, index=True, nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    stack_trace = Column(Text, nullable=True)
    log_file_name = Column(String(255), nullable=True)
    log_content = Column(Text, nullable=True)
    category = Column(String(50), default='General', index=True)
    severity = Column(String(20), default='Medium', index=True)
    priority = Column(String(10), default='P3')
    status = Column(String(20), default='Open', index=True)
    root_cause = Column(Text, nullable=True)
    resolution = Column(Text, nullable=True)
    resolution_notes = Column(Text, nullable=True)
    date_submitted = Column(Date, default=datetime.date.today)
    date_resolved = Column(Date, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)

    # Relationships
    analysis_result = relationship("AnalysisResult", back_populates="bug", uselist=False, cascade="all, delete-orphan")
    chat_messages = relationship("ChatMessage", back_populates="bug", cascade="all, delete-orphan", order_by="ChatMessage.id")
    tags = relationship("Tag", secondary=bug_tags, back_populates="bugs")

class AnalysisResult(Base):
    __tablename__ = 'analysis_results'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    bug_id = Column(Integer, ForeignKey('bugs.id', ondelete="CASCADE"), unique=True, nullable=False)
    triage_data = Column(Text, nullable=True)
    log_analysis_data = Column(Text, nullable=True)
    root_cause_data = Column(Text, nullable=True)
    duplicate_data = Column(Text, nullable=True)
    rag_retrieval_data = Column(Text, nullable=True)
    remediation_data = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    bug = relationship("Bug", back_populates="analysis_result")

class ChatMessage(Base):
    __tablename__ = 'chat_messages'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    bug_id = Column(Integer, ForeignKey('bugs.id', ondelete="CASCADE"), nullable=False)
    sender = Column(String(20), nullable=False)  # 'user' or 'advisor'
    message = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

    bug = relationship("Bug", back_populates="chat_messages")

class User(Base):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(100), nullable=True)
    role = Column(String(20), default='user')
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class Tag(Base):
    __tablename__ = 'tags'

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(50), unique=True, nullable=False)

    bugs = relationship("Bug", secondary=bug_tags, back_populates="tags")
