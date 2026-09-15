from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.app.database import get_db
from backend.app.models.bug import Bug, ChatMessage
from backend.app.schemas.bug import ChatMessageCreate, ChatMessageResponse
from backend.app.agents.chat import chat_agent
from backend.app.api.bugs import format_bug_dict
from backend.app.utils.logging import logger

router = APIRouter(prefix="/bugs", tags=["chat"])

@router.get("/{bug_id}/chat", response_model=List[ChatMessageResponse])
def get_chat_history(bug_id: str, db: Session = Depends(get_db)):
    """Fetch chat history for a specific bug."""
    bug = db.query(Bug).filter(or_(Bug.bug_code == bug_id, Bug.id == (int(bug_id) if bug_id.isdigit() else -1))).first()
    if not bug:
        raise HTTPException(status_code=404, detail="Bug not found")

    messages = db.query(ChatMessage).filter(ChatMessage.bug_id == bug.id).order_by(ChatMessage.id.asc()).all()
    return messages

@router.post("/{bug_id}/chat", response_model=ChatMessageResponse, status_code=status.HTTP_201_CREATED)
def send_chat_message(bug_id: str, message_in: ChatMessageCreate, db: Session = Depends(get_db)):
    """Send user chat message, execute ChatAgent, save history, and return advisor response."""
    bug = db.query(Bug).filter(or_(Bug.bug_code == bug_id, Bug.id == (int(bug_id) if bug_id.isdigit() else -1))).first()
    if not bug:
        raise HTTPException(status_code=404, detail="Bug not found")

    user_text = message_in.message.strip()
    if not user_text:
        raise HTTPException(status_code=400, detail="Message cannot be empty")

    # 1. Save user message
    user_msg = ChatMessage(
        bug_id=bug.id,
        sender="user",
        message=user_text
    )
    db.add(user_msg)
    db.commit()

    # 2. Fetch history & format bug info
    history = db.query(ChatMessage).filter(ChatMessage.bug_id == bug.id).order_by(ChatMessage.id.asc()).all()
    history_list = [{"sender": m.sender, "message": m.message} for m in history]
    bug_dict = format_bug_dict(bug)

    # 3. Generate response using ChatAgent
    advisor_reply = chat_agent.respond(bug_dict, history_list, user_text)

    # 4. Save advisor response
    advisor_msg = ChatMessage(
        bug_id=bug.id,
        sender="advisor",
        message=advisor_reply
    )
    db.add(advisor_msg)
    db.commit()
    db.refresh(advisor_msg)

    logger.info(f"AI Mentor responded to chat on bug {bug.bug_code}")
    return advisor_msg
