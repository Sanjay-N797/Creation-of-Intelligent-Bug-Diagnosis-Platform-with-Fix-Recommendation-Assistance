from typing import Dict, Any, List

class TriageAgent:
    def __init__(self):
        self.name = "Triage Agent"
        self.icon = "🎯"

        self.severity_patterns = {
            "Critical": {
                "keywords": [
                    'crash', 'down', 'outage', 'data loss', 'corruption', 'security breach',
                    'injection', 'xss', 'vulnerability', 'unauthorized', 'production down',
                    'system failure', 'unresponsive', 'out of memory', 'oom', 'deadlock',
                    'denial of service', 'dos', 'exploit', 'breach', 'leak sensitive',
                    'cannot start', 'fatal', 'panic', 'segfault', 'core dump'
                ],
                "weight": 4
            },
            "High": {
                "keywords": [
                    'error', 'fail', 'broken', 'not working', 'exception', 'timeout',
                    'memory leak', 'race condition', 'data inconsistency', 'authentication',
                    'authorization', 'permission denied', 'connection refused', 'pool exhausted',
                    'infinite loop', 'freeze', 'hang', 'block', 'corrupt', 'missing data',
                    'token expired', 'session lost', 'rate limit'
                ],
                "weight": 3
            },
            "Medium": {
                "keywords": [
                    'slow', 'performance', 'degraded', 'incorrect', 'wrong', 'unexpected',
                    'layout', 'display', 'rendering', 'pagination', 'sorting', 'filter',
                    'upload', 'download', 'format', 'conversion', 'timezone', 'locale',
                    'mobile', 'responsive', 'compatibility', 'browser'
                ],
                "weight": 2
            },
            "Low": {
                "keywords": [
                    'typo', 'cosmetic', 'minor', 'enhancement', 'improvement', 'refactor',
                    'documentation', 'style', 'alignment', 'color', 'font', 'spacing',
                    'tooltip', 'placeholder', 'label', 'message', 'wording',
                    'nice to have', 'suggestion'
                ],
                "weight": 1
            }
        }

        self.priority_map = {
            "Critical": "P1",
            "High": "P1",
            "Medium": "P2",
            "Low": "P3"
        }

        self.category_patterns = {
            "Security": ['sql injection', 'xss', 'csrf', 'vulnerability', 'security', 'exploit',
                        'unauthorized', 'authentication bypass', 'cors', 'injection', 'breach'],
            "Backend": ['server', 'api', 'database', 'null pointer', 'exception', 'service',
                       'controller', 'repository', 'connection pool', 'thread', 'memory'],
            "Frontend": ['css', 'layout', 'render', 'component', 'react', 'angular', 'vue',
                        'dom', 'browser', 'safari', 'chrome', 'responsive', 'ui', 'display'],
            "Database": ['sql', 'query', 'table', 'index', 'migration', 'schema', 'orm',
                        'pagination', 'transaction', 'deadlock', 'connection pool'],
            "Authentication": ['login', 'logout', 'token', 'jwt', 'session', 'oauth',
                              'password', 'auth', 'sso', 'mfa', '2fa'],
            "Performance": ['slow', 'latency', 'throughput', 'memory leak', 'cpu', 'load',
                           'cache', 'optimization', 'bottleneck', 'scaling'],
            "DevOps": ['deploy', 'pipeline', 'docker', 'kubernetes', 'ci/cd', 'build',
                      'configuration', 'environment', 'monitoring', 'logging']
        }

    def analyze(self, bug_report: Dict[str, Any]) -> Dict[str, Any]:
        title = bug_report.get("title", "")
        description = bug_report.get("description", "")
        stack_trace = bug_report.get("stackTrace", "") or bug_report.get("stack_trace", "")
        user_category = bug_report.get("category", "")
        clarifications = bug_report.get("clarifications", {}) or {}

        # Append user clarifications if present
        clarification_text = " ".join([f"{k}: {v}" for k, v in clarifications.items()])
        combined_text = f"{title} {description} {stack_trace} {clarification_text}".lower()

        severity = self._classify_severity(combined_text)
        priority = self._determine_priority(severity, combined_text)
        category = self._detect_category(combined_text, user_category)
        confidence = self._calculate_confidence(combined_text, severity)
        
        # Boost confidence if user provided clarifications
        if clarifications:
            confidence = min(98, confidence + 20)

        tags = self._extract_tags(combined_text)

        # Generate clarification questions if confidence is low (< 70%) and no clarifications were provided
        clarification_questions = []
        if confidence < 70 and not clarifications:
            clarification_questions = [
                {
                    "id": "q_env",
                    "question": "Did this error occur in a live production environment under heavy load?",
                    "options": ["Yes, live production", "No, local/staging dev environment", "Unknown / Not specified"]
                },
                {
                    "id": "q_state",
                    "question": "Was the associated user session or database connection active right before the crash?",
                    "options": ["Active session / valid payload", "Expired session / empty payload", "Uncertain"]
                }
            ]

        reasoning = self._generate_reasoning(severity, priority, category, confidence, combined_text)

        priority_score_data = self.calculate_priority_score(severity, category, combined_text)

        return {
            "agent": self.name,
            "icon": self.icon,
            "severity": severity,
            "priority": priority,
            "category": category,
            "affectedComponent": category,
            "reasoning": reasoning,
            "confidence": confidence,
            "priorityScore": priority_score_data,
            "tags": tags,
            "clarificationQuestions": clarification_questions,
            "summary": f"Classified as {severity} severity ({priority}) in affected component \"{category}\" with {confidence}% confidence. Priority Score: {priority_score_data['score']}/100 ({priority_score_data['level']}).",
            "details": {
                "classification": f"🔴 {severity} Severity | Priority: {priority}" if severity == "Critical" else (
                    f"🟠 {severity} Severity | Priority: {priority}" if severity == "High" else (
                        f"🟡 {severity} Severity | Priority: {priority}" if severity == "Medium" else f"🟢 {severity} Severity | Priority: {priority}"
                    )
                ),
                "priorityScore": f"⚡ Priority Score: {priority_score_data['score']}/100 [{priority_score_data['level']}]",
                "category": f"📂 Component: {category}",
                "reasoning": f"🧠 Reasoning: {reasoning}",
                "confidence": f"📊 Confidence: {confidence}%",
                "tags": f"🏷️ Tags: {', '.join(tags)}",
                "recommendation": self._get_recommendation(severity, priority)
            }
        }

    def _generate_reasoning(self, severity: str, priority: str, category: str, confidence: int, text: str) -> str:
        reasons = []
        if severity == "Critical":
            reasons.append("High-impact system crash or security vulnerability pattern detected.")
        elif severity == "High":
            reasons.append("Functional failure or exception pattern identified disrupting core operations.")
        elif severity == "Medium":
            reasons.append("Degraded performance, rendering, or non-fatal logical issue detected.")
        else:
            reasons.append("Cosmetic, minor layout, or non-critical enhancement request.")

        if 'production' in text or 'live' in text:
            reasons.append("Priority escalated due to live production impact.")
        if 'data loss' in text or 'corruption' in text:
            reasons.append("Priority escalated due to potential data loss or integrity risk.")

        reasons.append(f"Affected component classified as '{category}' based on domain pattern analysis.")
        reasons.append(f"Diagnostic confidence rated at {confidence}% based on stack trace frame availability and pattern matches.")
        return " ".join(reasons)


    def _classify_severity(self, text: str) -> str:
        scores = {"Critical": 0, "High": 0, "Medium": 0, "Low": 0}

        for level, config in self.severity_patterns.items():
            for kw in config["keywords"]:
                if kw in text:
                    scores[level] += config["weight"]

        max_score = 0
        max_severity = "Medium"
        for level, score in scores.items():
            if score > max_score:
                max_score = score
                max_severity = level

        return max_severity

    def _determine_priority(self, severity: str, text: str) -> str:
        priority = self.priority_map.get(severity, "P3")
        if 'production' in text or 'live' in text or 'customer-facing' in text:
            if priority == 'P2':
                priority = 'P1'
            elif priority == 'P3':
                priority = 'P2'

        if 'data loss' in text or 'data corruption' in text or 'data integrity' in text:
            priority = 'P1'

        return priority

    def _detect_category(self, text: str, user_category: str) -> str:
        if user_category and user_category != "Auto-detect":
            return user_category

        scores = {}
        for category, keywords in self.category_patterns.items():
            scores[category] = sum(1 for kw in keywords if kw in text)

        max_score = 0
        detected = "General"
        for cat, score in scores.items():
            if score > max_score:
                max_score = score
                detected = cat

        return detected if max_score > 0 else "General"

    def _calculate_confidence(self, text: str, severity: str) -> int:
        match_count = sum(1 for kw in self.severity_patterns[severity]["keywords"] if kw in text)
        confidence = min(95, 50 + (match_count * 15))
        if 'at ' in text and ('.java:' in text or '.js:' in text or '.py:' in text):
            confidence = min(95, confidence + 10)
        return confidence

    def _extract_tags(self, text: str) -> List[str]:
        tag_keywords = {
            'crash': ['crash', 'fatal', 'unresponsive'],
            'memory-leak': ['memory leak', 'out of memory', 'oom', 'heap'],
            'security': ['vulnerability', 'injection', 'xss', 'exploit', 'breach'],
            'performance': ['slow', 'latency', 'performance', 'bottleneck'],
            'ui-bug': ['layout', 'display', 'css', 'render', 'responsive'],
            'data-loss': ['data loss', 'corruption', 'missing data'],
            'authentication': ['auth', 'login', 'token', 'session', 'jwt'],
            'api-error': ['api', '500', '404', '401', '403', 'endpoint'],
            'database': ['sql', 'database', 'query', 'connection pool'],
            'timeout': ['timeout', 'timed out', 'request timeout'],
            'race-condition': ['race condition', 'concurrent', 'deadlock', 'thread'],
            'compatibility': ['browser', 'safari', 'chrome', 'mobile', 'responsive'],
            'deployment': ['deploy', 'build', 'pipeline', 'docker']
        }

        matched = [tag for tag, kws in tag_keywords.items() if any(kw in text for kw in kws)]
        return matched if matched else ['general']

    def _get_recommendation(self, severity: str, priority: str) -> str:
        if priority == 'P1':
            return '⚡ IMMEDIATE ACTION REQUIRED — Assign to senior developer, notify team lead.'
        elif priority == 'P2':
            return '📋 Schedule for next sprint — Assign to available developer.'
        else:
            return '📝 Add to backlog — Address when capacity allows.'

    def calculate_priority_score(self, severity: str, category: str, text: str) -> Dict[str, Any]:
        """Calculates Bug Priority Score (0-100) using severity, impact, frequency, and affected module."""
        # 1. Severity Score (35%)
        sev_weights = {"Critical": 100, "High": 75, "Medium": 50, "Low": 25}
        sev_score = sev_weights.get(severity, 50)

        # 2. Impact Score (30%)
        if any(k in text for k in ['crash', 'outage', 'data loss', 'security', 'vulnerability', 'injection', 'breach']):
            impact_score = 100
        elif any(k in text for k in ['exception', 'error', 'failed', 'timeout', 'auth', 'broken']):
            impact_score = 75
        elif any(k in text for k in ['slow', 'degraded', 'rendering', 'display', 'layout']):
            impact_score = 50
        else:
            impact_score = 25

        # 3. Frequency Score (20%)
        if any(k in text for k in ['production', 'live', 'all users', 'constant', 'always']):
            freq_score = 100
        elif any(k in text for k in ['frequent', 'intermittent', 'multiple times', 'repeat']):
            freq_score = 70
        elif any(k in text for k in ['occasional', 'sometimes']):
            freq_score = 40
        else:
            freq_score = 20

        # 4. Affected Module Criticality (15%)
        mod_weights = {
            "Security": 100, "Authentication": 100,
            "Backend": 85, "Database": 80,
            "Performance": 70, "Frontend": 55,
            "DevOps": 50, "General": 40
        }
        mod_score = mod_weights.get(category, 50)

        composite_score = int(
            (0.35 * sev_score) +
            (0.30 * impact_score) +
            (0.20 * freq_score) +
            (0.15 * mod_score)
        )

        if composite_score >= 80:
            level = "Critical"
            badge_class = "badge-critical"
        elif composite_score >= 65:
            level = "High"
            badge_class = "badge-high"
        elif composite_score >= 45:
            level = "Medium"
            badge_class = "badge-medium"
        else:
            level = "Low"
            badge_class = "badge-low"

        return {
            "score": composite_score,
            "level": level,
            "badgeClass": badge_class,
            "breakdown": {
                "severity": sev_score,
                "impact": impact_score,
                "frequency": freq_score,
                "module": mod_score
            },
            "formula": "35% Severity + 30% Impact + 20% Frequency + 15% Affected Module"
        }

