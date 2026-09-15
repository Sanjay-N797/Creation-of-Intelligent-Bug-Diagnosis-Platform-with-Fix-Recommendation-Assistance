from typing import Dict, Any, List
from backend.app.utils.similarity import calculate_similarity

class RootCauseAgent:
    def __init__(self):
        self.name = "Root Cause Agent"
        self.icon = "🧠"

        self.root_cause_patterns = {
            'Null Reference Access': {
                'triggers': ['nullpointer', 'null reference', 'undefined is not', 'cannot read property', 'none type', 'attributeerror'],
                'causes': [
                    'Variable or object reference not initialized before use',
                    'Database query returned null but result was assumed non-null',
                    'Optional/nullable field accessed without null check',
                    'Cache miss returning null instead of empty/default value',
                    'Object deleted/garbage collected but reference still held'
                ],
                'preventionTips': [
                    'Add null checks before accessing object properties',
                    'Use Optional/Maybe types for nullable returns',
                    'Implement null object pattern for defaults',
                    'Add defensive programming checks at service boundaries'
                ]
            },
            'Memory Exhaustion': {
                'triggers': ['outofmemory', 'memory leak', 'heap space', 'oom', 'memory usage'],
                'causes': [
                    'Resource (connections, streams, handles) not properly closed',
                    'Collection growing unboundedly without cleanup',
                    'Circular references preventing garbage collection',
                    'Large dataset loaded entirely into memory instead of streaming',
                    'Event listeners registered but never unregistered'
                ],
                'preventionTips': [
                    'Use try-with-resources or finally blocks for cleanup',
                    'Implement connection/resource pooling with size limits',
                    'Add monitoring for memory usage patterns',
                    'Use streaming/pagination for large datasets'
                ]
            },
            'Concurrency Issue': {
                'triggers': ['race condition', 'deadlock', 'concurrent', 'thread', 'synchroniz', 'atomic', 'locking'],
                'causes': [
                    'Non-atomic check-then-act sequence in multi-threaded context',
                    'Missing synchronization on shared mutable state',
                    'Lock ordering inconsistency causing deadlock',
                    'Stale read from cache in concurrent environment',
                    'Non-thread-safe collection used in concurrent context'
                ],
                'preventionTips': [
                    'Use atomic operations or optimistic locking',
                    'Implement proper lock ordering protocols',
                    'Use concurrent-safe collections (ConcurrentHashMap, etc.)',
                    'Apply SELECT FOR UPDATE for database-level locking'
                ]
            },
            'Security Vulnerability': {
                'triggers': ['injection', 'xss', 'csrf', 'vulnerability', 'exploit', 'breach', 'unauthorized', 'cors'],
                'causes': [
                    'User input directly concatenated into queries/commands',
                    'Missing input validation and sanitization',
                    'Improper output encoding allowing script injection',
                    'Misconfigured security headers or CORS policy',
                    'Hardcoded credentials or secrets in source code'
                ],
                'preventionTips': [
                    'Use parameterized queries for all database operations',
                    'Implement input validation at all entry points',
                    'Apply output encoding appropriate to context (HTML, JS, URL)',
                    'Configure security headers (CSP, X-Frame-Options, etc.)',
                    'Store secrets in environment variables or secret managers'
                ]
            },
            'Configuration Error': {
                'triggers': ['config', 'environment', 'property', 'setting', 'cors', 'timeout', 'limit', 'threshold'],
                'causes': [
                    'Environment-specific configuration not applied correctly',
                    'Default configuration values too restrictive for production',
                    'Missing configuration for new deployment environment',
                    'Configuration drift between environments',
                    'Incompatible configuration between dependent services'
                ],
                'preventionTips': [
                    'Use environment-specific configuration files',
                    'Validate configuration at startup',
                    'Document all configuration parameters',
                    'Implement configuration management tools'
                ]
            },
            'Data Integrity Issue': {
                'triggers': ['corrupt', 'inconsistent', 'data loss', 'duplicate', 'pagination', 'offset', 'wrong data'],
                'causes': [
                    'Missing database constraints allowing invalid data',
                    'Incomplete transaction handling causing partial updates',
                    'Offset-based pagination unstable with concurrent inserts',
                    'Missing cascade delete leaving orphaned records',
                    'Timezone/encoding mismatch corrupting stored data'
                ],
                'preventionTips': [
                    'Add database-level constraints (NOT NULL, UNIQUE, FK)',
                    'Use cursor-based pagination for stable results',
                    'Wrap related operations in database transactions',
                    'Implement data validation at application layer'
                ]
            },
            'Resource Exhaustion': {
                'triggers': ['pool', 'connection', 'exhaust', 'limit', 'capacity', 'quota', 'rate limit', 'throttl'],
                'causes': [
                    'Connection/resource leak under error conditions',
                    'Pool size insufficient for peak load',
                    'Missing connection timeout or max lifetime settings',
                    'Retry logic without backoff causing thundering herd',
                    'Rate limiter configuration not applied to all paths'
                ],
                'preventionTips': [
                    'Implement proper resource cleanup in all code paths',
                    'Configure connection pool monitoring and alerts',
                    'Add circuit breaker patterns for external dependencies',
                    'Implement exponential backoff for retries'
                ]
            },
            'Authentication & Authorization Failure': {
                'triggers': ['auth', 'unauthorized', '401', '403', 'token', 'jwt', 'session', 'login', 'permission', 'credentials', 'invalid token'],
                'causes': [
                    'Expired or invalid JWT/session token passed in request',
                    'Missing authentication header or credentials in request payload',
                    'Role-based access control (RBAC) permission check failed',
                    'Secret key mismatch between token issuer and validator'
                ],
                'preventionTips': [
                    'Implement automatic token refresh mechanisms on client',
                    'Add clear authorization error messages and audit logs',
                    'Centralize authentication middleware across all endpoints'
                ]
            },
            'Database & Connection Issue': {
                'triggers': ['sql', 'database', 'jdbc', 'orm', 'sqlalchemy', 'hikari', 'connection pool', 'badsql', 'sqlite', 'postgres', 'query'],
                'causes': [
                    'Database connection pool exhaustion under concurrent load',
                    'Malformed SQL syntax or un-migrated schema change',
                    'Database transaction timeout or lock contention deadlock',
                    'Unindexed query causing full table scan timeouts'
                ],
                'preventionTips': [
                    'Configure connection pool sizing and connection leak detection',
                    'Add database indexes for frequently queried filter columns',
                    'Use parameterized ORM queries to prevent SQL syntax errors'
                ]
            },
            'Network & Timeout Error': {
                'triggers': ['network', 'timeout', 'connectionrefused', 'connecttimedout', 'socket', 'dns', 'unreachable', 'gateway', '502', '504'],
                'causes': [
                    'Upstream microservice or database host unreachable',
                    'Network socket read/connect timeout limit exceeded',
                    'DNS resolution failure or firewall security group blocking port',
                    'Intermittent network packet drop without retry policy'
                ],
                'preventionTips': [
                    'Implement circuit breaker pattern for external HTTP dependencies',
                    'Configure exponential backoff and jitter for retries',
                    'Set explicit connect and read timeouts on HTTP client'
                ]
            },
            'API/Integration Error': {
                'triggers': ['api', 'endpoint', 'request', 'response', '401', '403', '404', '500', 'http', 'rest'],
                'causes': [
                    'API contract change not reflected in client code',
                    'Missing error handling for non-success HTTP responses',
                    'Incorrect content type or header configuration',
                    'Token/credential expiry not handled gracefully',
                    'Request payload exceeding server-side limits'
                ],
                'preventionTips': [
                    'Implement API versioning and contract testing',
                    'Add comprehensive error handling for all HTTP status codes',
                    'Use API client libraries with built-in retry logic',
                    'Monitor API health and response times'
                ]
            },
            'UI/Rendering Issue': {
                'triggers': ['layout', 'css', 'render', 'display', 'responsive', 'browser', 'safari', 'chrome', 'dom', 'react'],
                'causes': [
                    'CSS property not supported in target browser version',
                    'Missing vendor prefixes for cross-browser compatibility',
                    'Infinite re-render loop due to incorrect dependency management',
                    'DOM manipulation conflicting with framework rendering',
                    'Responsive breakpoint not handling edge case viewport sizes'
                ],
                'preventionTips': [
                    'Use CSS feature detection with @supports queries',
                    'Add browser compatibility testing to CI pipeline',
                    'Memoize expensive computations in render functions',
                    'Test across all target browsers and devices'
                ]
            }
        }

    def analyze(self, bug_report: Dict[str, Any], triage_result: Dict[str, Any], log_result: Dict[str, Any], resolved_bugs: List[Dict[str, Any]]) -> Dict[str, Any]:
        title = bug_report.get("title", "")
        description = bug_report.get("description", "")
        stack_trace = bug_report.get("stackTrace", "") or bug_report.get("stack_trace", "") or ""
        combined_text = f"{title} {description} {stack_trace}".lower()

        matched_patterns = self._match_patterns(combined_text)
        historical_causes = self._query_historical_knowledge(combined_text, resolved_bugs)
        probable_causes = self._rank_causes(matched_patterns, historical_causes, triage_result, log_result)
        prevention_tips = self._gather_prevention_tips(matched_patterns)

        pattern_names = [p["name"] for p in matched_patterns]

        summary = f"Most probable: {probable_causes[0]['cause']} ({probable_causes[0]['confidence']}% confidence)" if probable_causes else "Could not determine root cause — insufficient data."

        beginner_explanations = {
            'Null Reference Access': {
                'analogy': "Imagine looking for a book on a shelf, but the shelf is completely empty. When you try to open the missing book, you get stuck because there is nothing to open!",
                'simplifiedSummary': "The code tried to read data from a variable or object that was never initialized or was set to null.",
                'keyConcepts': [
                    {"term": "Null / Undefined", "definition": "A special marker in programming that indicates a variable holds 'no value' or point to nothing."},
                    {"term": "NullPointerException", "definition": "An error thrown when code tries to invoke a method or access a field on a null object."}
                ],
                'learningLinks': ["https://developer.mozilla.org/en-US/docs/Glossary/Null", "https://docs.oracle.com/javase/tutorial/java/javaOO/"]
            },
            'Memory Exhaustion': {
                'analogy': "Imagine a warehouse filling up with boxes every day, but nobody ever throws away old boxes. Eventually, the warehouse is full and no new boxes can fit!",
                'simplifiedSummary': "The application used up all available RAM memory because resources (like database connections or files) were opened but never closed.",
                'keyConcepts': [
                    {"term": "Garbage Collection", "definition": "An automatic process in runtimes like Java/Node.js that reclaims memory no longer in use."},
                    {"term": "Memory Leak", "definition": "When an application allocates memory but fails to release it back to the operating system."}
                ],
                'learningLinks': ["https://web.dev/articles/memory-discovering-issues"]
            },
            'Concurrency Issue': {
                'analogy': "Imagine two people trying to buy the very last concert ticket online at the exact same millisecond. If the system isn't locked, both might get charged but only one gets a ticket!",
                'simplifiedSummary': "Two or more background tasks tried to modify the exact same piece of data simultaneously without waiting for each other.",
                'keyConcepts': [
                    {"term": "Race Condition", "definition": "A bug where output depends on the uncontrollable sequence or timing of concurrent execution threads."},
                    {"term": "Mutex / Lock", "definition": "A mechanism that prevents multiple threads from accessing a shared resource at the same time."}
                ],
                'learningLinks': ["https://en.wikipedia.org/wiki/Race_condition"]
            },
            'Security Vulnerability': {
                'analogy': "Imagine asking a hotel receptionist for 'Room 101 OR true', and the receptionist unlocks all rooms in the hotel at once!",
                'simplifiedSummary': "Untrusted user text was directly passed into database commands or HTML pages without input sanitization.",
                'keyConcepts': [
                    {"term": "SQL Injection (SQLi)", "definition": "A vulnerability where an attacker manipulates SQL queries by inserting malicious code into input fields."},
                    {"term": "Input Sanitization", "definition": "Cleaning user input to strip dangerous control characters before processing."}
                ],
                'learningLinks': ["https://owasp.org/www-community/attacks/SQL_Injection"]
            }
        }

        # Pick matching beginner explanation or default
        matched_category = pattern_names[0] if pattern_names else 'Null Reference Access'
        beginner_exp = beginner_explanations.get(matched_category, beginner_explanations['Null Reference Access'])

        top_cause_str = probable_causes[0]['cause'] if probable_causes else "Unspecified root cause"
        rag_context_str = f" Historical defect RAG match: {historical_causes[0]['bugId']} ({historical_causes[0]['rootCause']})" if historical_causes else ""
        tech_explanation = f"Root cause diagnosed as '{matched_category}': {top_cause_str}.{rag_context_str}"

        return {
            "agent": self.name,
            "icon": self.icon,
            "category": matched_category,
            "technicalExplanation": tech_explanation,
            "probableCauses": probable_causes,
            "matchedPatterns": pattern_names,
            "historicalCauses": historical_causes,
            "preventionTips": prevention_tips,
            "beginnerSummary": beginner_exp.get("simplifiedSummary", ""),
            "analogy": beginner_exp.get("analogy", ""),
            "beginnerExplanation": beginner_exp,
            "summary": summary,
            "details": {
                "topCause": f"🎯 Primary Cause: {top_cause_str}",
                "allCauses": [f"{i+1}. [{c['confidence']}%] {c['cause']} ({c['source']})" for i, c in enumerate(probable_causes)],
                "historicalMatches": [f"📚 {h['bugId']}: {h['title']} ({h['similarity']}% similar) — Cause: {h['rootCause']}" for h in historical_causes] if historical_causes else ['No similar historical bugs found'],
                "preventionTips": [f"💡 {tip}" for tip in prevention_tips] if prevention_tips else ['No specific prevention tips available'],
                "patternsMatched": [f"🔗 {p['name']} ({p['confidence']}% match)" for p in matched_patterns] if matched_patterns else ['No known patterns matched']
            }
        }


    def _match_patterns(self, text: str) -> List[Dict[str, Any]]:
        matched = []
        for name, pattern in self.root_cause_patterns.items():
            match_count = sum(1 for t in pattern["triggers"] if t in text)
            if match_count > 0:
                matched.append({
                    "name": name,
                    "matchCount": match_count,
                    "confidence": min(95, 40 + match_count * 20),
                    "causes": pattern["causes"],
                    "preventionTips": pattern["preventionTips"]
                })
        return sorted(matched, key=lambda x: x["confidence"], reverse=True)

    def _query_historical_knowledge(self, text: str, resolved_bugs: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        results = []
        for bug in resolved_bugs:
            bug_text = f"{bug.get('title', '')} {bug.get('description', '')} {bug.get('stack_trace', '')}"
            sim = calculate_similarity(text, bug_text)
            if sim >= 0.1 and bug.get("root_cause"):
                results.append({
                    "bugId": bug.get("bug_code") or bug.get("id"),
                    "title": bug.get("title"),
                    "rootCause": bug.get("root_cause"),
                    "similarity": round(sim * 100)
                })
        return sorted(results, key=lambda x: x["similarity"], reverse=True)[:3]

    def _rank_causes(self, patterns: List[Dict[str, Any]], historical: List[Dict[str, Any]], triage: Dict[str, Any], log_res: Dict[str, Any]) -> List[Dict[str, Any]]:
        causes = []
        for idx, p in enumerate(patterns):
            for c in p["causes"][:2]:
                causes.append({
                    "cause": c,
                    "source": f"Pattern: {p['name']}",
                    "confidence": max(30, p["confidence"] - (idx * 10)),
                    "type": "pattern"
                })

        for h in historical:
            causes.append({
                "cause": h["rootCause"],
                "source": f"Historical: {h['bugId']} — {h['title']}",
                "confidence": min(90, h["similarity"] + 10),
                "type": "historical"
            })

        if log_res and log_res.get("errorTypeInfo"):
            causes.append({
                "cause": log_res["errorTypeInfo"]["description"],
                "source": f"Log Analysis: {log_res['errorInfo']['type']}",
                "confidence": 70,
                "type": "log-derived"
            })

        causes = sorted(causes, key=lambda x: x["confidence"], reverse=True)
        # Deduplicate
        seen = set()
        unique_causes = []
        for item in causes:
            if item["cause"] not in seen:
                seen.add(item["cause"])
                unique_causes.append(item)

        return unique_causes[:5]

    def _gather_prevention_tips(self, patterns: List[Dict[str, Any]]) -> List[str]:
        tips = []
        for p in patterns:
            for tip in p["preventionTips"]:
                if tip not in tips:
                    tips.append(tip)
        return tips[:6]
