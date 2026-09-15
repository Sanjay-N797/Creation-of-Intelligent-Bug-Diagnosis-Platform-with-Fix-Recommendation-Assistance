from typing import Dict, Any, List
from backend.app.agents.triage import TriageAgent
from backend.app.agents.log_analysis import LogAnalysisAgent
from backend.app.agents.root_cause import RootCauseAgent
from backend.app.agents.duplicate import DuplicateDetectionAgent
from backend.app.utils.rag_retrieval import rag_retriever
from backend.app.agents.remediation import RemediationAgent
from backend.app.agents.auto_fix import auto_fix_agent
from backend.app.agents.test_generator import test_generator_agent
from backend.app.agents.fix_verification import fix_verification_agent
from backend.app.agents.security_scanner import security_scanner_agent

class AgentPipeline:
    def __init__(self):
        self.triage_agent = TriageAgent()
        self.log_analysis_agent = LogAnalysisAgent()
        self.root_cause_agent = RootCauseAgent()
        self.duplicate_agent = DuplicateDetectionAgent()
        self.rag_retriever = rag_retriever
        self.remediation_agent = RemediationAgent()
        self.auto_fix_agent = auto_fix_agent
        self.test_generator_agent = test_generator_agent
        self.fix_verification_agent = fix_verification_agent
        self.security_scanner_agent = security_scanner_agent

    def run_pipeline(self, bug_report: Dict[str, Any], resolved_bugs: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Runs multi-agent AI pipeline in sequence and returns compiled analysis results."""
        triage_res = self.triage_agent.analyze(bug_report)
        log_res = self.log_analysis_agent.analyze(bug_report)
        root_cause_res = self.root_cause_agent.analyze(bug_report, triage_res, log_res, resolved_bugs)
        duplicate_res = self.duplicate_agent.analyze(bug_report, resolved_bugs)
        rag_res = self.rag_retriever.retrieve_similar_resolutions(bug_report, resolved_bugs, top_k=3)
        remediation_res = self.remediation_agent.analyze(bug_report, triage_res, log_res, root_cause_res, duplicate_res, rag_res)
        
        # New Feature 1: AI Auto-Fix
        auto_fix_res = self.auto_fix_agent.generate_fix(bug_report, root_cause_res, log_res)
        
        # New Feature 2: Auto Test Generator
        test_gen_res = self.test_generator_agent.generate_tests(bug_report, auto_fix_res)
        
        # New Feature 3: Fix Verification
        fix_verify_res = self.fix_verification_agent.verify_fix(auto_fix_res, bug_report)
        
        # New Feature 4: Security Scanner
        scan_text = f"{bug_report.get('title', '')}\n{bug_report.get('stackTrace', '')}\n{bug_report.get('description', '')}\n{bug_report.get('logContent', '')}"
        security_scan_res = self.security_scanner_agent.scan_code(scan_text, bug_report.get('title', ''))

        return {
            "triage": triage_res,
            "logAnalysis": log_res,
            "rootCause": root_cause_res,
            "duplicate": duplicate_res,
            "ragRetrieval": rag_res,
            "remediation": remediation_res,
            "autoFix": auto_fix_res,
            "testGenerator": test_gen_res,
            "fixVerification": fix_verify_res,
            "securityScan": security_scan_res
        }

pipeline = AgentPipeline()


