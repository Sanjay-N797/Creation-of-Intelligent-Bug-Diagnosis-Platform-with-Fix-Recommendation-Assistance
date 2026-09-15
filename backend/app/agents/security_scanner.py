"""
SecurityScannerAgent — Comprehensive Static Application Security Testing (SAST)

Scans code snippets, stack traces, and defect logs to detect:
  1. SQL Injection (SQLi) — CWE-89
  2. Cross-Site Scripting (XSS) — CWE-79
  3. Hardcoded Secrets & Credentials — CWE-798
  4. Unsafe APIs & Remote Code Execution (`eval`, `exec`, `subprocess(shell=True)`, `pickle.loads`, path traversal) — CWE-95 / CWE-22
  5. Insecure Transport / HTTP Misconfiguration — CWE-319
"""

import re
from typing import Dict, Any, List, Tuple

class SecurityScannerAgent:
    def __init__(self):
        self.name = "Security Scanner Agent"
        self.icon = "🛡️"

        # (Rule ID, Category, Severity, CWE, Pattern, Message, Recommendation)
        self.rules: List[Tuple[str, str, str, str, re.Pattern, str, str]] = [
            # ── SQL Injection ──
            ("SEC-SQL-001", "SQL Injection", "Critical", "CWE-89",
             re.compile(r"""SELECT\s+.*\+\s*\w+|['"]\s*SELECT\s+.*|SQL Injection""", re.IGNORECASE),
             "SQL Injection risk: Dynamic string concatenation/formatting in SQL query.",
             "Use parameterized queries with bound variables (:param) or an ORM like SQLAlchemy / Hibernate."),

            ("SEC-SQL-002", "SQL Injection", "Critical", "CWE-89",
             re.compile(r"""db\.execute\s*\(\s*['"].*\s*\+\s*\w+""", re.IGNORECASE),
             "Unsanitized raw SQL execution detected.",
             "Pass parameters as a separate tuple or dict argument to db.execute()."),

            # ── Cross-Site Scripting ──
            ("SEC-XSS-001", "Cross-Site Scripting", "High", "CWE-79",
             re.compile(r"""innerHTML\s*=|\.html\(|document\.write\(""", re.IGNORECASE),
             "Potential DOM XSS: Direct HTML assignment without sanitization.",
             "Use textContent, innerText, or DOMPurify.sanitize() before inserting user input into DOM."),

            ("SEC-XSS-002", "Cross-Site Scripting", "High", "CWE-79",
             re.compile(r"""dangerouslySetInnerHTML""", re.IGNORECASE),
             "React dangerouslySetInnerHTML usage detected.",
             "Ensure content is sanitized using DOMPurify before setting dangerouslySetInnerHTML."),

            # ── Hardcoded Secrets ──
            ("SEC-SEC-001", "Hardcoded Secrets", "Critical", "CWE-798",
             re.compile(r"""(password|secret|api_key|apikey|private_key|token)\s*=\s*['"][a-zA-Z0-9_\-]{8,}['"]""", re.IGNORECASE),
             "Hardcoded secret credential detected in source code.",
             "Store secrets in environment variables (.env) or a Vault / AWS Secrets Manager."),

            ("SEC-SEC-002", "Hardcoded Secrets", "Critical", "CWE-798",
             re.compile(r"""AKIA[0-9A-Z]{16}""", re.IGNORECASE),
             "AWS Access Key ID detected in source file.",
             "Revoke this AWS key immediately and retrieve credentials via IAM roles or environment variables."),

            # ── Unsafe APIs & Execution ──
            ("SEC-API-001", "Unsafe APIs", "Critical", "CWE-95",
             re.compile(r"""\beval\s*\(|\bexec\s*\(""", re.IGNORECASE),
             "Dangerous code execution: eval() or exec() usage.",
             "Replace eval()/exec() with safe parsers like json.loads() or static ast.literal_eval()."),

            ("SEC-API-002", "Unsafe APIs", "High", "CWE-78",
             re.compile(r"""subprocess\.(Popen|call|run)\s*\(.*shell\s*=\s*True""", re.IGNORECASE),
             "Command Injection risk: subprocess executed with shell=True.",
             "Set shell=False and pass command and arguments as a list of strings."),

            ("SEC-API-003", "Unsafe APIs", "High", "CWE-502",
             re.compile(r"""pickle\.loads\s*\(""", re.IGNORECASE),
             "Unsafe deserialization using Python pickle.",
             "Avoid unpickling data from untrusted sources; use JSON or Protocol Buffers."),

            ("SEC-API-004", "Unsafe APIs", "Medium", "CWE-22",
             re.compile(r"""\.\./|\.\.\\""", re.IGNORECASE),
             "Potential Path Traversal sequence detected (../).",
             "Sanitize file paths using os.path.basename() or pathlib.Path.resolve()."),

            # ── Insecure Transport ──
            ("SEC-NET-001", "Insecure Transport", "Medium", "CWE-319",
             re.compile(r"""http://(?!localhost|127\.0\.0\.1)""", re.IGNORECASE),
             "Insecure HTTP URL detected for external connection.",
             "Enforce HTTPS for all external API endpoints and web traffic.")
        ]

    def scan_code(self, code: str, title: str = "") -> Dict[str, Any]:
        if not code and title:
            code = title

        lines = code.splitlines() if code else []
        findings = []
        rule_hits = set()

        for rule_id, category, severity, cwe, pattern, msg, rec in self.rules:
            for line_idx, line in enumerate(lines, 1):
                if pattern.search(line):
                    findings.append({
                        "ruleId": rule_id,
                        "category": category,
                        "severity": severity,
                        "cwe": cwe,
                        "line": line_idx,
                        "lineContent": line.strip(),
                        "message": msg,
                        "recommendation": rec
                    })
                    rule_hits.add(rule_id)

        # Calculate security score & risk level
        total = len(findings)
        crit_count = sum(1 for f in findings if f["severity"] == "Critical")
        high_count = sum(1 for f in findings if f["severity"] == "High")
        med_count = sum(1 for f in findings if f["severity"] == "Medium")

        score = max(0, 100 - (crit_count * 30 + high_count * 20 + med_count * 10))

        if crit_count > 0:
            risk_level = "Critical"
        elif high_count > 0:
            risk_level = "High"
        elif med_count > 0:
            risk_level = "Medium"
        elif total > 0:
            risk_level = "Low"
        else:
            risk_level = "Clean"

        if total == 0:
            summary = "No security vulnerabilities detected in scanned code."
        else:
            summary = f"Detected {total} security vulnerabilities ({crit_count} Critical, {high_count} High, {med_count} Medium)."

        return {
            "agent": self.name,
            "icon": self.icon,
            "score": score,
            "riskLevel": risk_level,
            "totalVulnerabilities": total,
            "categoryCounts": {
                "SQL Injection": sum(1 for f in findings if f["category"] == "SQL Injection"),
                "Cross-Site Scripting": sum(1 for f in findings if f["category"] == "Cross-Site Scripting"),
                "Hardcoded Secrets": sum(1 for f in findings if f["category"] == "Hardcoded Secrets"),
                "Unsafe APIs": sum(1 for f in findings if f["category"] == "Unsafe APIs"),
                "Insecure Transport": sum(1 for f in findings if f["category"] == "Insecure Transport")
            },
            "findings": findings,
            "summary": summary
        }

security_scanner_agent = SecurityScannerAgent()
