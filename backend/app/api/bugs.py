import json
import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from backend.app.database import get_db
from backend.app.models.bug import Bug, AnalysisResult
from backend.app.schemas.bug import BugCreate, BugUpdate, BugResolveRequest, StatsResponse
from backend.app.utils.logging import logger

router = APIRouter(prefix="/bugs", tags=["bugs"])

def format_bug_dict(bug: Bug) -> dict:
    analysis = None
    if bug.analysis_result:
        try:
            remed_data = json.loads(bug.analysis_result.remediation_data) if bug.analysis_result.remediation_data else {}
            analysis = {
                "triage": json.loads(bug.analysis_result.triage_data) if bug.analysis_result.triage_data else None,
                "logAnalysis": json.loads(bug.analysis_result.log_analysis_data) if bug.analysis_result.log_analysis_data else None,
                "rootCause": json.loads(bug.analysis_result.root_cause_data) if bug.analysis_result.root_cause_data else None,
                "duplicate": json.loads(bug.analysis_result.duplicate_data) if bug.analysis_result.duplicate_data else None,
                "ragRetrieval": json.loads(bug.analysis_result.rag_retrieval_data) if hasattr(bug.analysis_result, 'rag_retrieval_data') and bug.analysis_result.rag_retrieval_data else None,
                "remediation": remed_data,
                "autoFix": remed_data.get("autoFix") if isinstance(remed_data, dict) else None,
                "testGenerator": remed_data.get("testGenerator") if isinstance(remed_data, dict) else None,
                "fixVerification": remed_data.get("fixVerification") if isinstance(remed_data, dict) else None,
                "securityScan": remed_data.get("securityScan") if isinstance(remed_data, dict) else None
            }
        except Exception as e:
            logger.error(f"Error parsing analysis results for bug {bug.bug_code}: {e}")

    return {
        "id": bug.bug_code,
        "dbId": bug.id,
        "title": bug.title,
        "description": bug.description or "",
        "stackTrace": bug.stack_trace or "",
        "logFileName": bug.log_file_name or "",
        "logContent": bug.log_content or "",
        "category": bug.category,
        "severity": bug.severity,
        "priority": bug.priority,
        "status": bug.status,
        "rootCause": bug.root_cause or "",
        "resolution": bug.resolution or "",
        "resolutionNotes": bug.resolution_notes or "",
        "dateSubmitted": str(bug.date_submitted) if bug.date_submitted else "",
        "dateResolved": str(bug.date_resolved) if bug.date_resolved else None,
        "analysisResults": analysis
    }

@router.get("", response_model=List[dict])
def get_bugs(
    q: Optional[str] = Query(None, description="Search query across title, description, stackTrace, rootCause, resolution"),
    category: Optional[str] = Query(None),
    severity: Optional[str] = Query(None),
    status_filter: Optional[str] = Query(None, alias="status"),
    db: Session = Depends(get_db)
):
    query = db.query(Bug)

    if q and q.strip():
        search_term = f"%{q.strip()}%"
        query = query.filter(
            or_(
                Bug.title.ilike(search_term),
                Bug.description.ilike(search_term),
                Bug.stack_trace.ilike(search_term),
                Bug.root_cause.ilike(search_term),
                Bug.resolution.ilike(search_term),
                Bug.category.ilike(search_term)
            )
        )

    if category and category != "All":
        query = query.filter(Bug.category == category)

    if severity and severity != "All":
        query = query.filter(Bug.severity == severity)

    if status_filter and status_filter != "All":
        query = query.filter(Bug.status == status_filter)

    bugs = query.order_by(Bug.id.desc()).all()
    return [format_bug_dict(b) for b in bugs]

@router.get("/stats", response_model=StatsResponse)
def get_bug_stats(db: Session = Depends(get_db)):
    bugs = db.query(Bug).order_by(Bug.id.desc()).all()
    resolved = [b for b in bugs if b.status == 'Resolved']
    in_progress = [b for b in bugs if b.status == 'In-Progress']
    open_bugs = [b for b in bugs if b.status not in ['Resolved', 'In-Progress']]

    severity_counts = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}
    category_counts = {}

    for b in bugs:
        if b.severity in severity_counts:
            severity_counts[b.severity] += 1
        category_counts[b.category] = category_counts.get(b.category, 0) + 1

    avg_resolution_days = "0"
    if resolved:
        total_days = 0.0
        valid_count = 0
        for b in resolved:
            if b.date_submitted and b.date_resolved:
                diff = (b.date_resolved - b.date_submitted).days
                total_days += max(0, diff)
                valid_count += 1
        if valid_count > 0:
            avg_resolution_days = f"{total_days / valid_count:.1f}"

    total_count = len(bugs)
    res_rate = f"{round((len(resolved) / total_count) * 100)}" if total_count > 0 else "0"
    recent_bugs = [format_bug_dict(b) for b in bugs[:6]]

    return {
        "total": total_count,
        "resolved": len(resolved),
        "open": len(open_bugs),
        "inProgress": len(in_progress),
        "severityCounts": severity_counts,
        "categoryCounts": category_counts,
        "avgResolutionDays": avg_resolution_days,
        "resolutionRate": res_rate,
        "recentBugs": recent_bugs
    }

@router.get("/analytics", response_model=dict)
def get_analytics(db: Session = Depends(get_db)):
    """Generates Defect Intelligence Hub metrics across categories, components, and anti-patterns."""
    bugs = db.query(Bug).all()
    
    # 1. Component Risk Analysis
    category_map = {}
    for b in bugs:
        cat = b.category or "General"
        if cat not in category_map:
            category_map[cat] = {"total": 0, "critical_high": 0, "open": 0}
        category_map[cat]["total"] += 1
        if b.severity in ["Critical", "High"]:
            category_map[cat]["critical_high"] += 1
        if b.status != "Resolved":
            category_map[cat]["open"] += 1

    category_risks = []
    for cat, data in category_map.items():
        risk_score = min(100, round((data["critical_high"] * 25) + (data["open"] * 15) + (data["total"] * 5)))
        category_risks.append({
            "category": cat,
            "totalBugs": data["total"],
            "openBugs": data["open"],
            "criticalHighCount": data["critical_high"],
            "riskScore": risk_score,
            "riskLevel": "High Risk" if risk_score >= 60 else ("Medium Risk" if risk_score >= 30 else "Low Risk")
        })

    category_risks.sort(key=lambda x: x["riskScore"], reverse=True)

    # 2. Recurring Anti-Pattern Alerts
    anti_patterns = [
        {
            "pattern": "Null Pointer / Null Reference Access",
            "impact": "High Frequency",
            "affectedCategories": ["Backend", "Security"],
            "recommendation": "Enforce @NonNull annotations and Optional types at service boundaries."
        },
        {
            "pattern": "Unparameterized Query Concatenation",
            "impact": "Security Vulnerability",
            "affectedCategories": ["Security", "Database"],
            "recommendation": "Migrate raw SQL strings to ORM models or parameterized prepared statements."
        },
        {
            "pattern": "Unclosed Connection / Stream Leak",
            "impact": "Resource Exhaustion",
            "affectedCategories": ["Backend", "Database"],
            "recommendation": "Wrap all Hikari connection acquisitions in try-with-resources blocks."
        }
    ]

    # 3. Team Productivity Guidance
    top_risks = [c["category"] for c in category_risks[:2]]
    recommendations = [
        f"Focus immediate sprint capacity on high-risk categories ({', '.join(top_risks)}).",
        "Add automated pre-commit hook scanning with Code Doctor static rules.",
        "Run regression unit tests covering null boundary checks before deploying hotfixes."
    ]

    return {
        "categoryRisks": category_risks,
        "antiPatterns": anti_patterns,
        "teamRecommendations": recommendations
    }

@router.get("/categories", response_model=List[str])
def get_categories(db: Session = Depends(get_db)):
    cats = db.query(Bug.category).distinct().all()
    categories = sorted(list(set([c[0] for c in cats if c[0]])))
    return ["All"] + categories

@router.get("/{bug_id}", response_model=dict)
def get_bug_by_id(bug_id: str, db: Session = Depends(get_db)):
    bug = None
    if bug_id.startswith("BUG-") or not bug_id.isdigit():
        bug = db.query(Bug).filter(Bug.bug_code == bug_id).first()
    else:
        bug = db.query(Bug).filter(Bug.id == int(bug_id)).first()

    if not bug:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Bug '{bug_id}' not found")

    return format_bug_dict(bug)

@router.post("", response_model=dict, status_code=status.HTTP_201_CREATED)
def create_bug(bug_in: BugCreate, db: Session = Depends(get_db)):
    count = db.query(Bug).count()
    new_code = f"BUG-{(count + 1):03d}"

    new_bug = Bug(
        bug_code=new_code,
        title=bug_in.title,
        description=bug_in.description or "",
        stack_trace=bug_in.stack_trace or "",
        log_file_name=bug_in.log_file_name or "",
        log_content=bug_in.log_content or "",
        category=bug_in.category or "General",
        severity=bug_in.severity or "Medium",
        priority=bug_in.priority or "P3",
        status="Open",
        date_submitted=datetime.date.today()
    )

    db.add(new_bug)
    db.commit()
    db.refresh(new_bug)
    logger.info(f"Created new bug: {new_code}")
    return format_bug_dict(new_bug)

@router.put("/{bug_id}", response_model=dict)
def update_bug(bug_id: str, bug_in: BugUpdate, db: Session = Depends(get_db)):
    bug = db.query(Bug).filter(or_(Bug.bug_code == bug_id, Bug.id == (int(bug_id) if bug_id.isdigit() else -1))).first()
    if not bug:
        raise HTTPException(status_code=404, detail="Bug not found")

    update_data = bug_in.dict(exclude_unset=True)
    for field, value in update_data.items():
        if hasattr(bug, field):
            setattr(bug, field, value)

    db.commit()
    db.refresh(bug)
    return format_bug_dict(bug)

@router.post("/{bug_id}/resolve", response_model=dict)
def resolve_bug(bug_id: str, resolve_in: BugResolveRequest, db: Session = Depends(get_db)):
    bug = db.query(Bug).filter(or_(Bug.bug_code == bug_id, Bug.id == (int(bug_id) if bug_id.isdigit() else -1))).first()
    if not bug:
        raise HTTPException(status_code=404, detail="Bug not found")

    bug.status = "Resolved"
    bug.root_cause = resolve_in.root_cause
    bug.resolution = resolve_in.resolution
    if resolve_in.resolution_notes:
        bug.resolution_notes = resolve_in.resolution_notes
    bug.date_resolved = datetime.date.today()

    db.commit()
    db.refresh(bug)
    logger.info(f"Bug {bug.bug_code} marked as Resolved")
    return format_bug_dict(bug)

@router.delete("/{bug_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_bug(bug_id: str, db: Session = Depends(get_db)):
    bug = db.query(Bug).filter(or_(Bug.bug_code == bug_id, Bug.id == (int(bug_id) if bug_id.isdigit() else -1))).first()
    if not bug:
        raise HTTPException(status_code=404, detail="Bug not found")

    db.delete(bug)
    db.commit()
    logger.info(f"Deleted bug {bug_id}")
    return None

@router.post("/reset", response_model=dict)
def reset_database(db: Session = Depends(get_db)):
    """Resets the database by re-running seed script."""
    from backend.app.seed import seed_database
    seed_database(db, force=True)
    logger.info("Database reset to initial sample data")
    return {"message": "Database reset to sample data successfully"}

# ── New Feature Endpoints ──
from backend.app.schemas.bug import AutoFixRequest, VerifyFixRequest, TestGenRequest, SecurityScanRequest, PriorityScoreRequest
from backend.app.agents.auto_fix import auto_fix_agent
from backend.app.agents.test_generator import test_generator_agent
from backend.app.agents.fix_verification import fix_verification_agent
from backend.app.agents.security_scanner import security_scanner_agent
from backend.app.agents.triage import TriageAgent

@router.post("/auto-fix", response_model=dict)
def generate_auto_fix(req: AutoFixRequest):
    """Feature 1: AI Auto-Fix endpoint."""
    bug_report = req.dict(by_alias=True)
    return auto_fix_agent.generate_fix(bug_report)

@router.post("/generate-tests", response_model=dict)
def generate_tests(req: TestGenRequest):
    """Feature 2: Auto Test Generator endpoint."""
    bug_report = req.dict(by_alias=True)
    return test_generator_agent.generate_tests(bug_report)

@router.post("/verify-fix", response_model=dict)
def verify_fix(req: VerifyFixRequest):
    """Feature 3: Fix Verification endpoint."""
    auto_fix_data = req.dict(by_alias=True)
    return fix_verification_agent.verify_fix(auto_fix_data)

@router.post("/security-scan", response_model=dict)
def run_security_scan(req: SecurityScanRequest):
    """Feature 4: Security Scanner endpoint."""
    return security_scanner_agent.scan_code(req.code, req.title)

@router.post("/priority-score", response_model=dict)
def calculate_priority_score_endpoint(req: PriorityScoreRequest):
    """Feature 5: Bug Priority Score endpoint."""
    triage = TriageAgent()
    combined_text = f"{req.title} {req.description} {req.stack_trace}".strip()
    return triage.calculate_priority_score(req.severity, req.category, combined_text)

