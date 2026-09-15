from fastapi import APIRouter, HTTPException, status
from backend.app.schemas.bug import CodeReviewRequest, CodeReviewResponse
from backend.app.agents.code_review import code_review_agent
from backend.app.utils.logging import logger

router = APIRouter(prefix="/code-review", tags=["code-review"])

@router.post("", response_model=CodeReviewResponse, status_code=status.HTTP_200_OK)
def audit_code(request: CodeReviewRequest):
    """Run automated code review static analysis rules on submitted code snippet."""
    code_text = request.code.strip()
    if not code_text:
        raise HTTPException(status_code=400, detail="Code snippet cannot be empty")

    logger.info("Running Code Doctor static analysis code review...")
    result = code_review_agent.analyze(code_text)
    return result
