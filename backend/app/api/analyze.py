import json
import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.app.database import get_db
from backend.app.models.bug import Bug, AnalysisResult
from backend.app.schemas.bug import BugCreate
from backend.app.agents.pipeline import pipeline
from backend.app.api.bugs import format_bug_dict
from backend.app.utils.logging import logger

router = APIRouter(prefix="/bugs", tags=["analysis"])

@router.post("/analyze", response_model=dict, status_code=status.HTTP_201_CREATED)
def analyze_bug(bug_in: BugCreate, db: Session = Depends(get_db)):
    """Runs full multi-agent analysis on a submitted bug and saves bug + results to database."""
    title = bug_in.title.strip()
    description = (bug_in.description or "").strip()
    stack_trace = (bug_in.stack_trace or "").strip()
    log_file_name = (bug_in.log_file_name or "").strip()
    log_content = (bug_in.log_content or "").strip()

    # If stack trace is empty but log content is provided, combine/use log content
    effective_stack = stack_trace
    if not effective_stack and log_content:
        effective_stack = log_content

    if not title:
        raise HTTPException(status_code=400, detail="Bug title is required")
    if not description and not effective_stack:
        raise HTTPException(status_code=400, detail="Description, stack trace, or log file content is required")

    bug_report_dict = {
        "title": title,
        "description": description,
        "stackTrace": effective_stack,
        "logFileName": log_file_name,
        "logContent": log_content,
        "category": bug_in.category or "Auto-detect",
        "clarifications": bug_in.clarifications or {}
    }

    # Fetch resolved bugs from database for similarity & historical matching
    resolved_db_bugs = db.query(Bug).filter(Bug.status == "Resolved").all()
    resolved_bugs_list = [
        {
            "id": b.id,
            "bug_code": b.bug_code,
            "title": b.title,
            "description": b.description or "",
            "stack_trace": b.stack_trace or "",
            "category": b.category,
            "severity": b.severity,
            "status": b.status,
            "root_cause": b.root_cause,
            "resolution": b.resolution,
            "date_resolved": b.date_resolved
        } for b in resolved_db_bugs
    ]

    # Execute Python Agent Pipeline (Log Parsing, Triage, Root Cause, TF-IDF Duplicates, FAISS RAG, Remediation)
    analysis_results = pipeline.run_pipeline(bug_report_dict, resolved_bugs_list)

    # Determine final values from agent triage
    triage = analysis_results.get("triage", {})
    severity = triage.get("severity", "Medium")
    priority = triage.get("priority", "P3")
    category = triage.get("category", bug_in.category if bug_in.category != "Auto-detect" else "General")

    # Generate bug code
    count = db.query(Bug).count()
    new_code = f"BUG-{(count + 1):03d}"

    # Save Bug entity
    new_bug = Bug(
        bug_code=new_code,
        title=title,
        description=description,
        stack_trace=effective_stack,
        log_file_name=log_file_name,
        log_content=log_content,
        category=category,
        severity=severity,
        priority=priority,
        status="Open",
        date_submitted=datetime.date.today()
    )

    db.add(new_bug)
    db.commit()
    db.refresh(new_bug)

    # Combine remediation with new feature outputs
    remed_payload = analysis_results.get("remediation", {})
    remed_payload["autoFix"] = analysis_results.get("autoFix")
    remed_payload["testGenerator"] = analysis_results.get("testGenerator")
    remed_payload["fixVerification"] = analysis_results.get("fixVerification")
    remed_payload["securityScan"] = analysis_results.get("securityScan")

    # Save AnalysisResult entity
    analysis_record = AnalysisResult(
        bug_id=new_bug.id,
        triage_data=json.dumps(analysis_results.get("triage", {})),
        log_analysis_data=json.dumps(analysis_results.get("logAnalysis", {})),
        root_cause_data=json.dumps(analysis_results.get("rootCause", {})),
        duplicate_data=json.dumps(analysis_results.get("duplicate", {})),
        rag_retrieval_data=json.dumps(analysis_results.get("ragRetrieval", {})),
        remediation_data=json.dumps(remed_payload)
    )

    db.add(analysis_record)
    db.commit()
    db.refresh(new_bug)

    logger.info(f"Analyzed and saved bug {new_code} via Agent Pipeline")
    return format_bug_dict(new_bug)
