from backend.app.api.bugs import router as bugs_router
from backend.app.api.analyze import router as analyze_router
from backend.app.api.auth import router as auth_router
from backend.app.api.chat import router as chat_router
from backend.app.api.code_review import router as code_review_router

__all__ = ["bugs_router", "analyze_router", "auth_router", "chat_router", "code_review_router"]
