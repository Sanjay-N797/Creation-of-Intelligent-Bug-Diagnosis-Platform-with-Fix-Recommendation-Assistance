"""
CodeReviewAgent — Automated Code Review & Refactoring Advisor ("Code Doctor")

Performs static analysis on user-submitted code snippets to detect:
  - Security vulnerabilities (SQL injection, XSS, hardcoded secrets)
  - Resource management issues (unclosed streams, raw queries)
  - Code quality anti-patterns (magic numbers, deep nesting, long methods)
  - Best practice violations (missing error handling, type issues)

Returns a health score (0-100), categorized findings, and refactored code suggestions.
"""

import re
from typing import Dict, Any, List, Tuple


class CodeReviewAgent:
    def __init__(self):
        self.name = "Code Review Agent"
        self.icon = "🩺"

        # Each rule: (id, category, severity, pattern, message, suggestion)
        self.rules: List[Tuple[str, str, str, re.Pattern, str, str]] = [
            # ── Security ──
            ("SEC-001", "Security", "Critical",
             re.compile(r"""['"]SELECT\s+.*\+\s*\w+""", re.IGNORECASE),
             "SQL injection risk: string concatenation in SQL query.",
             "Use parameterized queries or an ORM instead of string concatenation."),

            ("SEC-002", "Security", "Critical",
             re.compile(r"""(password|secret|api_key|apikey|token)\s*=\s*['"][^'"]{4,}['"]""", re.IGNORECASE),
             "Hardcoded secret detected.",
             "Move secrets to environment variables or a secrets manager."),

            ("SEC-003", "Security", "High",
             re.compile(r"""innerHTML\s*=|\.html\(|document\.write\(""", re.IGNORECASE),
             "Potential XSS: direct DOM HTML injection.",
             "Use textContent, createElement, or a sanitization library instead."),

            ("SEC-004", "Security", "High",
             re.compile(r"""eval\s*\("""),
             "Use of eval() is a security risk.",
             "Replace eval() with safer alternatives like JSON.parse() or function constructors."),

            ("SEC-005", "Security", "Medium",
             re.compile(r"""http://""", re.IGNORECASE),
             "Insecure HTTP URL detected.",
             "Use HTTPS for all external connections."),

            # ── Resource Management ──
            ("RES-001", "Resource Management", "High",
             re.compile(r"""(open|fopen|getConnection)\s*\("""),
             "Resource opened without visible close/cleanup.",
             "Use try-with-resources, context managers, or finally blocks for cleanup."),

            ("RES-002", "Resource Management", "Medium",
             re.compile(r"""new\s+(FileInputStream|FileOutputStream|Socket|ServerSocket)\s*\("""),
             "Raw resource construction without lifecycle management.",
             "Wrap in try-with-resources or use a managed pool."),

            # ── Error Handling ──
            ("ERR-001", "Error Handling", "High",
             re.compile(r"""except\s*:\s*$|catch\s*\(\s*(Exception|Error)\s+\w+\)\s*\{?\s*(//|/\*|#)?\s*$""", re.MULTILINE),
             "Empty or overly broad exception handler.",
             "Catch specific exceptions and add proper logging/handling."),

            ("ERR-002", "Error Handling", "Medium",
             re.compile(r"""catch\s*\(\s*\w+\s*\)\s*\{\s*\}"""),
             "Silent exception swallowing — catch block is empty.",
             "Log the error or re-throw with context."),

            ("ERR-003", "Error Handling", "Medium",
             re.compile(r"""(console\.log|print|System\.out\.print)\s*\(\s*(e|err|error|ex|exception)\s*\)""", re.IGNORECASE),
             "Error logged to console instead of structured logger.",
             "Use a structured logging framework (e.g., logging, log4j, winston)."),

            # ── Code Quality ──
            ("CQ-001", "Code Quality", "Low",
             re.compile(r"""\b(100|200|404|500|1000|3600|86400|1024|2048)\b"""),
             "Magic number detected.",
             "Extract to a named constant for readability and maintainability."),

            ("CQ-002", "Code Quality", "Medium",
             re.compile(r"""(if|else|for|while)\s*[\({].*\n.*\s+(if|else|for|while)\s*[\({].*\n.*\s+(if|else|for|while)\s*[\({]"""),
             "Deep nesting detected (3+ levels).",
             "Refactor using early returns, guard clauses, or extract methods."),

            ("CQ-003", "Code Quality", "Low",
             re.compile(r"""TODO|FIXME|HACK|XXX|TEMP""", re.IGNORECASE),
             "TODO/FIXME marker found in code.",
             "Address the TODO or create a tracked issue for it."),

            ("CQ-004", "Code Quality", "Medium",
             re.compile(r"""^\s*(var|let)\s+""", re.MULTILINE),
             "Mutable variable declaration (var/let).",
             "Prefer const for immutable bindings where possible."),

            # ── Type Safety ──
            ("TS-001", "Type Safety", "Medium",
             re.compile(r"""\b==\b(?!=)"""),
             "Loose equality operator (==) used.",
             "Use strict equality (=== / !==) to avoid type coercion bugs."),

            ("TS-002", "Type Safety", "Low",
             re.compile(r"""\bany\b"""),
             "TypeScript 'any' type detected.",
             "Replace with a specific type or use 'unknown' with type guards."),
        ]

    def analyze(self, code_snippet: str) -> Dict[str, Any]:
        """Analyze a code snippet and return health score, findings, and suggestions."""
        if not code_snippet or not code_snippet.strip():
            return {
                "agent": self.name,
                "icon": self.icon,
                "score": 0,
                "grade": "N/A",
                "findings": [],
                "summary": "No code provided for review.",
                "categoryCounts": {},
                "refactoredCode": None,
            }

        lines = code_snippet.split("\n")
        findings: List[Dict[str, Any]] = []

        for rule_id, category, severity, pattern, message, suggestion in self.rules:
            for line_num, line in enumerate(lines, start=1):
                if pattern.search(line):
                    findings.append({
                        "ruleId": rule_id,
                        "category": category,
                        "severity": severity,
                        "line": line_num,
                        "lineContent": line.strip()[:120],
                        "message": message,
                        "suggestion": suggestion,
                    })

        # Deduplicate by (ruleId, line)
        seen = set()
        unique_findings = []
        for f in findings:
            key = (f["ruleId"], f["line"])
            if key not in seen:
                seen.add(key)
                unique_findings.append(f)
        findings = unique_findings

        # Score calculation
        score = self._calculate_score(findings, len(lines))
        grade = self._score_to_grade(score)

        # Category breakdown
        category_counts: Dict[str, int] = {}
        for f in findings:
            cat = f["category"]
            category_counts[cat] = category_counts.get(cat, 0) + 1

        # Sort findings: Critical > High > Medium > Low
        severity_order = {"Critical": 0, "High": 1, "Medium": 2, "Low": 3}
        findings.sort(key=lambda x: severity_order.get(x["severity"], 4))

        return {
            "agent": self.name,
            "icon": self.icon,
            "score": score,
            "grade": grade,
            "findings": findings,
            "totalIssues": len(findings),
            "categoryCounts": category_counts,
            "summary": self._build_summary(score, grade, findings),
            "refactoredCode": None,  # Placeholder for future LLM-based refactoring
        }

    def _calculate_score(self, findings: List[Dict], total_lines: int) -> int:
        """
        Health score formula:
        Start at 100, deduct points per finding based on severity.
        Normalize slightly by code length (longer code tolerates more findings).
        """
        if not findings:
            return 100

        deductions = {"Critical": 20, "High": 12, "Medium": 6, "Low": 2}
        total_deduction = sum(deductions.get(f["severity"], 5) for f in findings)

        # Slight normalization: larger snippets get a small tolerance
        length_factor = max(1.0, total_lines / 50.0)
        adjusted = total_deduction / length_factor

        return max(0, min(100, round(100 - adjusted)))

    def _score_to_grade(self, score: int) -> str:
        if score >= 90:
            return "A"
        elif score >= 75:
            return "B"
        elif score >= 60:
            return "C"
        elif score >= 40:
            return "D"
        else:
            return "F"

    def _build_summary(self, score: int, grade: str, findings: List[Dict]) -> str:
        if not findings:
            return f"🎉 Code Health Score: {score}/100 (Grade {grade}) — No issues detected. Clean code!"

        critical = sum(1 for f in findings if f["severity"] == "Critical")
        high = sum(1 for f in findings if f["severity"] == "High")

        parts = [f"Code Health Score: {score}/100 (Grade {grade}) — {len(findings)} issue(s) found."]
        if critical:
            parts.append(f"🚨 {critical} critical issue(s) require immediate attention.")
        if high:
            parts.append(f"⚠️ {high} high-severity issue(s) should be addressed soon.")
        return " ".join(parts)


code_review_agent = CodeReviewAgent()
