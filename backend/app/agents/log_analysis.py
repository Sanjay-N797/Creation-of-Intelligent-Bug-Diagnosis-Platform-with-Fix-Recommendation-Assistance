import re
from typing import Dict, Any, List

class LogAnalysisAgent:
    def __init__(self):
        self.name = "Log Analysis Agent"
        self.icon = "🔍"

        self.error_types = {
            'NullPointerException': {'category': 'Null Reference', 'severity': 'High', 'description': 'Attempting to use a null reference'},
            'NullReferenceException': {'category': 'Null Reference', 'severity': 'High', 'description': 'Attempting to use a null reference'},
            'TypeError': {'category': 'Type Error', 'severity': 'Medium', 'description': 'Value is not of expected type'},
            'OutOfMemoryError': {'category': 'Resource Exhaustion', 'severity': 'Critical', 'description': 'JVM heap space exhausted'},
            'StackOverflowError': {'category': 'Infinite Recursion', 'severity': 'High', 'description': 'Call stack limit exceeded'},
            'ArrayIndexOutOfBoundsException': {'category': 'Bounds Error', 'severity': 'Medium', 'description': 'Array index outside valid range'},
            'ClassNotFoundException': {'category': 'Missing Dependency', 'severity': 'High', 'description': 'Required class not found in classpath'},
            'ConnectionRefusedException': {'category': 'Network Error', 'severity': 'High', 'description': 'Connection to service refused'},
            'TimeoutException': {'category': 'Timeout', 'severity': 'High', 'description': 'Operation exceeded time limit'},
            'SQLSyntaxErrorException': {'category': 'SQL Error', 'severity': 'Medium', 'description': 'Invalid SQL syntax'},
            'BadSqlGrammarException': {'category': 'SQL Error', 'severity': 'High', 'description': 'Malformed SQL query'},
            'ReferenceError': {'category': 'Reference Error', 'severity': 'Medium', 'description': 'Reference to undefined variable'},
            'SyntaxError': {'category': 'Syntax Error', 'severity': 'Medium', 'description': 'Code parsing failed'},
            'IllegalStateException': {'category': 'State Error', 'severity': 'High', 'description': 'Object in invalid state for operation'},
            'ConcurrentModificationException': {'category': 'Concurrency', 'severity': 'High', 'description': 'Collection modified during iteration'},
            'SecurityException': {'category': 'Security', 'severity': 'Critical', 'description': 'Security violation detected'},
            'FileNotFoundException': {'category': 'IO Error', 'severity': 'Medium', 'description': 'Specified file not found'},
            'PermissionError': {'category': 'Permission', 'severity': 'High', 'description': 'Insufficient permissions for operation'},
            'KeyError': {'category': 'Key Error', 'severity': 'Medium', 'description': 'Dictionary key not found'},
            'ValueError': {'category': 'Value Error', 'severity': 'Medium', 'description': 'Invalid value for operation'},
            'ImportError': {'category': 'Import Error', 'severity': 'High', 'description': 'Module import failed'},
            'AttributeError': {'category': 'Attribute Error', 'severity': 'Medium', 'description': 'Object missing expected attribute'}
        }

    def analyze(self, bug_report: Dict[str, Any]) -> Dict[str, Any]:
        stack_trace = bug_report.get("stackTrace", "") or bug_report.get("stack_trace", "") or ""
        description = bug_report.get("description", "") or ""
        combined_text = f"{description}\n{stack_trace}"

        language = self._detect_language(stack_trace)
        error_info = self._extract_error(stack_trace, language)
        frames = self._extract_frames(stack_trace, language)
        failure_point = self._identify_failure_point(frames)
        affected_components = self._identify_components(frames)
        error_type_info = self.error_types.get(error_info["type"], {
            "category": "Unknown",
            "severity": "Medium",
            "description": f"Error of type: {error_info['type']}"
        })
        log_insights = self._extract_log_insights(combined_text)

        frame_locations = [f["fullLocation"] for f in frames[:10]]
        formatted_failure_point = failure_point.get("location") if failure_point.get("location") != "Could not determine" else f"{failure_point.get('file', 'N/A')}:{failure_point.get('line', 'N/A')}"

        snippet_lines = []
        if error_info["type"] != "Unknown Error":
            snippet_lines.append(f"{error_info['type']}: {error_info['message']}")
        if frames:
            for f in frames[:3]:
                snippet_lines.append(f"  at {f['fullLocation']}")
        parsed_snippet = "\n".join(snippet_lines) if snippet_lines else (stack_trace[:300] if stack_trace else "No stack trace provided.")

        return {
            "agent": self.name,
            "icon": self.icon,
            "language": language,
            "programmingLanguage": language,
            "errorType": error_info["type"],
            "exceptionType": error_info["type"],
            "errorMessage": error_info["message"],
            "methodName": failure_point.get("method", "N/A"),
            "lineNumber": failure_point.get("line", "N/A"),
            "errorInfo": error_info,
            "errorTypeInfo": error_type_info,
            "frames": frames,
            "codePath": frame_locations,
            "failurePoint": formatted_failure_point,
            "failurePointDetails": failure_point,
            "parsedSnippet": parsed_snippet,
            "affectedComponents": affected_components,
            "logInsights": log_insights,
            "summary": f"{language.capitalize()} {error_info['type']} detected at {formatted_failure_point}",
            "details": {
                "error": f"❌ {error_info['type']}: {error_info['message']}",
                "errorCategory": f"📋 Category: {error_type_info['category']} — {error_type_info['description']}",
                "language": f"💻 Language: {language.capitalize()}",
                "failurePoint": f"📍 Failure Point: {failure_point.get('file', 'N/A')}:{failure_point.get('line', 'N/A')} in {failure_point.get('method', 'N/A')}()",
                "stackDepth": f"📚 Stack Depth: {len(frames)} frames analyzed",
                "components": f"🧩 Affected Components: {', '.join(affected_components) if affected_components else 'Could not determine'}",
                "logInsights": log_insights if log_insights else ['📝 No additional log patterns detected'],
                "frames": frame_locations
            }
        }


    def _detect_language(self, trace: str) -> str:
        if not trace:
            return "generic"
        if "Traceback (most recent call last)" in trace or re.search(r'File\s+"[^"]+",\s+line\s+\d+', trace):
            return "python"
        if re.search(r'\s+at\s+[\w.$]+\.[\w$<>]+\([\w.]+:\d+\)', trace) or ".java:" in trace:
            return "java"
        if re.search(r'\s+at\s+[\w.$ ]+\([\w/.:-]+:\d+:\d+\)', trace) or ".js:" in trace or ".ts:" in trace:
            return "javascript"
        return "generic"

    def _extract_error(self, trace: str, language: str) -> Dict[str, str]:
        if not trace:
            return {"type": "Unknown Error", "message": "No stack trace provided"}

        if language == "java":
            m = re.search(r'^([\w.]+(?:Error|Exception|Throwable))\s*:?\s*(.*)', trace, re.MULTILINE)
            if m:
                error_type = m.group(1).split('.')[-1]
                return {"type": error_type, "message": m.group(2).strip()}
        elif language == "javascript":
            m = re.search(r'^((?:TypeError|ReferenceError|SyntaxError|RangeError|Error|EvalError|URIError))\s*:?\s*(.*)', trace, re.MULTILINE)
            if m:
                return {"type": m.group(1), "message": m.group(2).strip()}
        elif language == "python":
            m = re.search(r'^([\w.]+(?:Error|Exception|Warning))\s*:?\s*(.*)', trace, re.MULTILINE)
            if m:
                error_type = m.group(1).split('.')[-1]
                return {"type": error_type, "message": m.group(2).strip()}

        # Generic fallback
        m = re.search(r'(?:Error|Exception|Failure)\s*:?\s*(.*)', trace, re.IGNORECASE)
        if m:
            return {"type": "Error", "message": m.group(1).strip()}

        return {"type": "Unknown Error", "message": "Could not parse error from trace"}

    def _extract_frames(self, trace: str, language: str) -> List[Dict[str, Any]]:
        frames = []
        if not trace:
            return frames

        if language == "java":
            pattern = re.compile(r'\s*at\s+([\w.$]+)\.([\w$<>]+)\(([\w.]+):(\d+)\)')
            for m in pattern.finditer(trace):
                cls, method, file, line = m.groups()
                frames.append({
                    "className": cls,
                    "method": method,
                    "file": file,
                    "line": int(line),
                    "fullLocation": f"{cls}.{method}({file}:{line})"
                })
        elif language == "javascript":
            pattern = re.compile(r'\s*at\s+(?:([\w.$ <>]+)\s+)?\(?([\w/.:-]+):(\d+)(?::(\d+))?\)?')
            for m in pattern.finditer(trace):
                method = m.group(1) or "anonymous"
                file = m.group(2)
                line = int(m.group(3))
                frames.append({
                    "className": "",
                    "method": method,
                    "file": file,
                    "line": line,
                    "fullLocation": f"{method} ({file}:{line})"
                })
        elif language == "python":
            pattern = re.compile(r'\s*File\s+"([^"]+)",\s+line\s+(\d+)(?:,\s+in\s+(\w+))?')
            for m in pattern.finditer(trace):
                file = m.group(1)
                line = int(m.group(2))
                method = m.group(3) or "module"
                frames.append({
                    "className": "",
                    "method": method,
                    "file": file,
                    "line": line,
                    "fullLocation": f"{method} ({file}:{line})"
                })

        return frames

    def _identify_failure_point(self, frames: List[Dict[str, Any]]) -> Dict[str, Any]:
        if not frames:
            return {"location": "Could not determine", "file": "N/A", "line": "N/A", "method": "N/A"}

        app_frame = None
        for f in frames:
            loc = f["fullLocation"].lower()
            if not any(k in loc for k in ['java.', 'javax.', 'sun.', 'org.springframework', 'org.apache', 'node_modules', 'internal/']):
                app_frame = f
                break

        frame = app_frame or frames[0]
        return {
            "location": frame["fullLocation"],
            "file": frame.get("file", "N/A"),
            "line": frame.get("line", "N/A"),
            "method": frame.get("method", "N/A"),
            "className": frame.get("className", "")
        }

    def _identify_components(self, frames: List[Dict[str, Any]]) -> List[str]:
        components = set()
        for frame in frames:
            cls = frame.get("className", "")
            if cls:
                parts = cls.split('.')
                if len(parts) >= 3:
                    components.add(parts[-2])
            file = frame.get("file", "")
            if file:
                filename = file.split('/')[-1].split('.')[0]
                if len(filename) > 1:
                    components.add(filename)
        return list(components)

    def _extract_log_insights(self, text: str) -> List[str]:
        insights = []
        lower = text.lower()
        if re.search(r'\d+\s*(?:ms|milliseconds|seconds)\s*(?:timeout|elapsed)', lower):
            insights.append('⏱️ Timeout or latency issue detected')
        if re.search(r'\d+/\d+\s*(?:connections|threads|pool)', lower):
            insights.append('🔗 Resource pool utilization data found')
        if re.search(r'(?:request|response)\s*(?:size|length)\s*:?\s*\d+', lower):
            insights.append('📦 Request/response size data available')
        if re.search(r'(?:retry|retries|attempt)\s*:?\s*\d+', lower):
            insights.append('🔄 Retry attempts detected')
        if re.search(r'(?:status|http)\s*:?\s*(?:4\d{2}|5\d{2})', lower):
            insights.append('🌐 HTTP error status code found')
        if re.search(r'(?:active|pending|idle|waiting)\s*:?\s*\d+', lower):
            insights.append('📊 System state metrics available')
        return insights
