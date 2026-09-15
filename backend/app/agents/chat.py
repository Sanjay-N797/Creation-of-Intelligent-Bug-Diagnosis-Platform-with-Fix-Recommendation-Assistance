from typing import Dict, Any, List
import re


class ChatAgent:
    """
    AI Coding Mentor Chat Agent.

    Provides context-aware programming mentorship for any software development
    question. Uses bug context when relevant, and general programming knowledge
    for broader questions. Supports conversational follow-ups via chat history.
    """

    def __init__(self):
        self.name = "AI Mentor Chat Agent"

    def respond(self, bug_info: Dict[str, Any], history: List[Dict[str, Any]], user_message: str) -> str:
        msg_lower = user_message.lower().strip()
        title = bug_info.get("title", "")
        stack_trace = bug_info.get("stack_trace", "") or bug_info.get("stackTrace", "")
        root_cause = bug_info.get("root_cause", "") or "Not yet identified"
        resolution = bug_info.get("resolution", "") or "Pending resolution"
        category = bug_info.get("category", "General")
        status = bug_info.get("status", "Open")
        severity = bug_info.get("severity", "Medium")
        priority = bug_info.get("priority", "P3")
        bug_code = bug_info.get("bug_code", bug_info.get("id", ""))

        analysis = bug_info.get("analysis_results", {}) or {}
        log_res = analysis.get("logAnalysis", {}) or {}
        remediation = analysis.get("remediation", {}) or {}
        triage = analysis.get("triage", {}) or {}
        root_cause_analysis = analysis.get("rootCause", {}) or {}

        failure_point = (log_res.get("details", {}) or {}).get("failurePoint", "Unknown location")
        remediation_steps = remediation.get("steps", [])
        code_example = remediation.get("codeExample", "")
        error_type = (log_res.get("details", {}) or {}).get("error", "")

        # Build conversational context from history
        recent_context = self._get_recent_context(history)

        # Route to appropriate response generator -- check specific domain topics first
        if self._matches_topic(msg_lower, ["algorithm", "data structure", "sort", "search", "binary search",
                                            "binary", "hash map", "tree", "graph", "linked list", "queue",
                                            "dynamic programming", "recursion", "big o", "complexity"]):
            return self._respond_algorithms(msg_lower)

        elif self._matches_topic(msg_lower, ["sql", "query", "database", "join", "index", "transaction",
                                              "normali", "schema", "table", "foreign key", "primary key",
                                              "stored procedure", "orm"]):
            return self._respond_sql(msg_lower, title, category)

        elif self._matches_topic(msg_lower, ["git", "branch", "merge", "rebase", "commit", "pull request",
                                              "version control", "cherry-pick", "stash", "gitflow"]):
            return self._respond_git(msg_lower)

        elif self._matches_topic(msg_lower, ["memory leak", "performance", "optimiz", "slow", "latency",
                                              "throughput", "bottleneck", "profil", "cache", "load",
                                              "scalab", "concurren"]):
            return self._respond_performance(msg_lower, title, category)

        elif self._matches_topic(msg_lower, ["security", "vulnerab", "injection", "xss", "csrf",
                                              "encrypt", "jwt", "oauth", "cors",
                                              "sanitiz", "ssl", "tls"]):
            return self._respond_security(msg_lower, title, category)

        elif self._matches_topic(msg_lower, ["design pattern", "solid", "architect", "microservice",
                                              "monolith", "mvc", "mvvm", "singleton", "factory",
                                              "observer", "dependency injection", "clean code",
                                              "refactor", "abstraction", "encapsulat"]):
            return self._respond_architecture(msg_lower)

        elif self._matches_topic(msg_lower, ["deploy", "ci/cd", "docker", "kubernetes", "pipeline",
                                              "container", "devops", "jenkins", "github actions",
                                              "terraform", "cloud"]):
            return self._respond_devops(msg_lower)

        elif self._matches_topic(msg_lower, ["api", "rest", "endpoint", "http", "request", "response",
                                              "status code", "graphql", "websocket", "grpc"]):
            return self._respond_api(msg_lower)

        elif self._matches_topic(msg_lower, ["python", "java", "javascript", "typescript", "c++",
                                              "rust", "go", "ruby", "php", "swift", "kotlin"]):
            return self._respond_language(msg_lower)

        elif self._matches_topic(msg_lower, ["test", "verify", "reproduce", "unit test", "mock", "pytest",
                                              "jest", "junit", "testing strategy", "test case", "tdd",
                                              "integration test", "e2e test", "coverage"]):
            return self._respond_testing(title, failure_point, category, stack_trace, msg_lower)

        elif self._matches_topic(msg_lower, ["fix", "patch", "resolve", "solution", "how to fix",
                                              "code example", "snippet", "remediat", "workaround",
                                              "hotfix"]):
            return self._respond_fix(title, failure_point, code_example, remediation_steps, category)

        elif self._matches_topic(msg_lower, ["severity", "priority", "critical", "urgent",
                                              "triage", "sla", "escalat"]):
            return self._respond_triage(bug_code, severity, priority, status, title, triage)

        elif self._matches_topic(msg_lower, ["why", "cause", "reason", "happen", "crash",
                                              "root cause", "diagnos", "what went wrong", "failure",
                                              "explain error", "explain bug", "explain crash",
                                              "explain failure", "explain cause"]):
            return self._respond_root_cause(title, failure_point, root_cause, category,
                                            error_type, stack_trace, root_cause_analysis)

        elif self._matches_topic(msg_lower, ["debug", "breakpoint", "log", "trace", "inspect",
                                              "stack trace", "error handling", "exception",
                                              "try catch", "error message"]):
            return self._respond_debugging(msg_lower, title, stack_trace, failure_point)

        elif self._matches_topic(msg_lower, ["hello", "hi ", "hey", "help", "what can you",
                                              "who are you", "introduce"]):
            return self._respond_greeting(bug_code, title, category)

        else:
            return self._respond_general(msg_lower, title, category, bug_code, failure_point,
                                         recent_context)

    # ----------------------------------------------------------------
    # Topic matching
    # ----------------------------------------------------------------
    def _matches_topic(self, msg: str, keywords: List[str]) -> bool:
        return any(kw in msg for kw in keywords)

    def _get_recent_context(self, history: List[Dict[str, Any]]) -> str:
        if not history:
            return ""
        recent = history[-6:]  # last 3 exchanges
        parts = []
        for m in recent:
            role = "User" if m.get("sender") == "user" else "Mentor"
            parts.append(f"{role}: {m.get('message', '')[:200]}")
        return "\n".join(parts)

    # ----------------------------------------------------------------
    # Response generators
    # ----------------------------------------------------------------
    def _respond_testing(self, title, failure_point, category, stack_trace, msg_lower):
        base = (
            f"**Testing and Verification Guidance for '{title}'**\n\n"
        )

        if "unit test" in msg_lower or "tdd" in msg_lower or "pytest" in msg_lower:
            base += (
                "**Unit Testing Best Practices:**\n\n"
                "1. **Arrange-Act-Assert Pattern**: Structure each test with clear setup, "
                "execution, and verification phases.\n"
                "2. **Test Isolation**: Mock external dependencies (database, API calls, "
                "file system) to test logic in isolation.\n"
                "3. **Boundary Testing**: Include edge cases such as null inputs, empty "
                "strings, maximum values, and negative numbers.\n"
                "4. **Naming Convention**: Use descriptive names like "
                "`test_<method>_<scenario>_<expected_result>()`.\n\n"
            )
        elif "integration test" in msg_lower or "e2e" in msg_lower:
            base += (
                "**Integration / E2E Testing Approach:**\n\n"
                "1. Test the full request-response cycle through actual endpoints.\n"
                "2. Use a test database (in-memory SQLite or Docker container) to avoid "
                "corrupting production data.\n"
                "3. Validate both success paths and error paths (4xx, 5xx responses).\n"
                "4. Test concurrent access scenarios if the service handles shared state.\n\n"
            )
        else:
            base += (
                "**Recommended Testing Strategy:**\n\n"
                f"1. **Reproduce the failure**: Create a test that triggers the condition "
                f"at `{failure_point}` to confirm the bug exists.\n"
                f"2. **Write regression tests**: After applying the fix, ensure the test "
                f"passes and add it to the `{category}` test suite.\n"
                "3. **Boundary conditions**: Test with null/empty inputs, concurrent "
                "access, and resource exhaustion scenarios.\n"
                "4. **Code coverage**: Aim for at least 80% line coverage on the affected "
                "module.\n\n"
            )

        base += (
            "```python\n"
            "# Example test structure\n"
            "def test_bug_fix_prevents_regression():\n"
            "    # Arrange: set up the conditions that caused the original failure\n"
            "    input_data = create_test_input(edge_case=True)\n"
            "\n"
            "    # Act: invoke the method under test\n"
            "    result = service.process(input_data)\n"
            "\n"
            "    # Assert: verify the fix handles the edge case correctly\n"
            "    assert result is not None\n"
            "    assert result.status == 'success'\n"
            "```"
        )
        return base

    def _respond_root_cause(self, title, failure_point, root_cause, category,
                            error_type, stack_trace, root_cause_analysis):
        details = root_cause_analysis.get("details", {}) or {}
        top_cause = details.get("topCause", root_cause)
        patterns = details.get("patternsMatched", [])

        response = (
            f"**Diagnostic Explanation for '{title}'**\n\n"
            f"**Failure Location**: `{failure_point}`\n"
            f"**Root Cause**: {top_cause}\n"
        )

        if error_type:
            response += f"**Error Type**: {error_type}\n"

        response += f"**Category**: {category}\n\n"

        response += (
            "**Analysis:**\n\n"
            f"This error occurs when runtime execution reaches `{failure_point}` "
            "without the necessary pre-condition validations in place. "
        )

        if "null" in (root_cause or "").lower() or "null" in (error_type or "").lower():
            response += (
                "The underlying issue is a null reference access -- the code assumes "
                "an object exists when it may have been deleted, not initialized, or "
                "returned as null from a data access layer. "
            )
        elif "memory" in (root_cause or "").lower() or "leak" in (root_cause or "").lower():
            response += (
                "The underlying issue is resource exhaustion -- objects are being allocated "
                "but not properly released, causing memory to grow unbounded over time. "
            )
        elif "sql" in (root_cause or "").lower() or "injection" in (root_cause or "").lower():
            response += (
                "The underlying issue is unsafe query construction -- user input is being "
                "concatenated directly into SQL strings without parameterization, creating "
                "both correctness and security risks. "
            )
        else:
            response += (
                f"In `{category}` services, unhandled boundary conditions cause runtime "
                "exceptions to propagate up the call stack. "
            )

        response += (
            "\n\n**Recommended next steps:**\n"
            "1. Add defensive validation checks at the service entry point.\n"
            "2. Implement proper error handling with descriptive error messages.\n"
            "3. Add monitoring/alerting for this failure pattern.\n"
        )

        if patterns:
            response += "\n**Patterns matched in analysis:**\n"
            for p in patterns[:3]:
                response += f"- {p}\n"

        return response

    def _respond_fix(self, title, failure_point, code_example, remediation_steps, category):
        response = f"**Fix Recommendation for '{title}'**\n\n"

        if remediation_steps:
            response += "**Remediation Steps:**\n"
            for i, step in enumerate(remediation_steps[:5], 1):
                response += f"{i}. {step}\n"
            response += "\n"

        if code_example:
            response += (
                "**Code Fix Example:**\n\n"
                f"```\n{code_example}\n```\n\n"
            )
        else:
            response += (
                "**General Fix Strategy:**\n\n"
                f"1. Add null/boundary validation at `{failure_point}`.\n"
                "2. Wrap resource acquisitions in try-finally or context manager blocks.\n"
                "3. Return a descriptive error response instead of allowing exceptions to propagate.\n"
                "4. Add logging at the point of failure for production diagnostics.\n\n"
                "```python\n"
                "# Defensive validation example\n"
                "def process_request(data):\n"
                "    if data is None:\n"
                "        raise ValueError('Input data cannot be None')\n"
                "    \n"
                "    # Validate required fields\n"
                "    if not data.get('id'):\n"
                "        raise ValueError('Missing required field: id')\n"
                "    \n"
                "    # Proceed with processing\n"
                "    return handle_valid_data(data)\n"
                "```\n"
            )

        response += (
            f"**Category**: {category}\n"
            "**Post-fix checklist**: Run regression tests, verify in staging, "
            "update documentation."
        )
        return response

    def _respond_triage(self, bug_code, severity, priority, status, title, triage):
        confidence = triage.get("confidence", "N/A")
        response = (
            f"**Triage Summary for {bug_code}**\n\n"
            f"**Bug**: {title}\n"
            f"**Severity**: {severity}\n"
            f"**Priority**: {priority}\n"
            f"**Status**: {status}\n"
        )

        if confidence != "N/A":
            response += f"**Confidence**: {confidence}%\n"

        response += "\n"

        if priority in ["P1", "P0"] or severity == "Critical":
            response += (
                "**Action Required**: This is a critical-priority issue that should be "
                "addressed immediately with an emergency hotfix. Consider:\n"
                "1. Assigning a dedicated engineer for immediate investigation.\n"
                "2. Preparing a rollback plan if the fix cannot be deployed quickly.\n"
                "3. Notifying stakeholders about potential service impact.\n"
            )
        elif priority == "P2" or severity == "High":
            response += (
                "**Action Required**: This is a high-priority issue that should be "
                "scheduled for the current sprint. Consider:\n"
                "1. Including this in the next sprint planning session.\n"
                "2. Identifying related issues that could be addressed together.\n"
                "3. Ensuring adequate test coverage before deploying the fix.\n"
            )
        else:
            response += (
                "**Action Required**: This issue should be addressed in upcoming "
                "sprint planning. Consider:\n"
                "1. Evaluating if this blocks other development work.\n"
                "2. Checking for related issues that share the same root cause.\n"
                "3. Documenting workarounds if the fix will be delayed.\n"
            )

        return response

    def _respond_sql(self, msg_lower, title, category):
        response = "**SQL and Database Guidance**\n\n"

        if "join" in msg_lower:
            response += (
                "**SQL JOIN Types:**\n\n"
                "- **INNER JOIN**: Returns only rows with matching values in both tables.\n"
                "- **LEFT JOIN (LEFT OUTER)**: Returns all rows from the left table, plus "
                "matched rows from the right. Unmatched right-side columns become NULL.\n"
                "- **RIGHT JOIN (RIGHT OUTER)**: Returns all rows from the right table, "
                "plus matched rows from the left.\n"
                "- **FULL OUTER JOIN**: Returns all rows from both tables, with NULLs "
                "where there is no match.\n"
                "- **CROSS JOIN**: Returns the Cartesian product of both tables.\n\n"
                "```sql\n"
                "-- Example: Get all users with their orders (including users with no orders)\n"
                "SELECT u.name, o.order_id, o.total\n"
                "FROM users u\n"
                "LEFT JOIN orders o ON u.id = o.user_id\n"
                "ORDER BY u.name;\n"
                "```\n"
            )
        elif "index" in msg_lower:
            response += (
                "**Database Indexing Best Practices:**\n\n"
                "1. Index columns used frequently in WHERE, JOIN, and ORDER BY clauses.\n"
                "2. Use composite indexes for queries filtering on multiple columns.\n"
                "3. Avoid over-indexing -- each index slows down INSERT/UPDATE operations.\n"
                "4. Use EXPLAIN/EXPLAIN ANALYZE to verify index usage.\n"
                "5. Consider partial indexes for large tables with selective queries.\n\n"
                "```sql\n"
                "-- Create an index on frequently queried columns\n"
                "CREATE INDEX idx_bugs_category_status ON bugs(category, status);\n"
                "```\n"
            )
        elif "normali" in msg_lower:
            response += (
                "**Database Normalization:**\n\n"
                "- **1NF**: Eliminate repeating groups; each cell contains a single value.\n"
                "- **2NF**: Remove partial dependencies; all non-key columns depend on the "
                "entire primary key.\n"
                "- **3NF**: Remove transitive dependencies; non-key columns depend only on "
                "the primary key.\n"
                "- **BCNF**: Every determinant is a candidate key.\n\n"
                "Balance normalization with query performance. Denormalization is acceptable "
                "for read-heavy workloads where join overhead is costly.\n"
            )
        elif "transaction" in msg_lower:
            response += (
                "**Database Transactions (ACID):**\n\n"
                "- **Atomicity**: All operations in a transaction succeed or all are rolled back.\n"
                "- **Consistency**: The database moves from one valid state to another.\n"
                "- **Isolation**: Concurrent transactions do not interfere with each other.\n"
                "- **Durability**: Committed transactions survive system failures.\n\n"
                "```sql\n"
                "BEGIN TRANSACTION;\n"
                "  UPDATE accounts SET balance = balance - 100 WHERE id = 1;\n"
                "  UPDATE accounts SET balance = balance + 100 WHERE id = 2;\n"
                "COMMIT;\n"
                "```\n"
            )
        else:
            response += (
                "**General SQL Best Practices:**\n\n"
                "1. Always use parameterized queries to prevent SQL injection.\n"
                "2. Use appropriate data types and constraints (NOT NULL, UNIQUE, FK).\n"
                "3. Index columns used in WHERE, JOIN, and ORDER BY clauses.\n"
                "4. Write readable queries with proper formatting and aliases.\n"
                "5. Use transactions for operations that modify multiple rows/tables.\n"
                "6. Monitor slow queries with EXPLAIN and query profiling tools.\n"
            )

        if category in ["Database", "Backend"] and title:
            response += f"\n**Context**: This guidance applies to the current bug '{title}' in the {category} category."

        return response

    def _respond_git(self, msg_lower):
        response = "**Git and Version Control Guidance**\n\n"

        if "branch" in msg_lower or "gitflow" in msg_lower:
            response += (
                "**Branching Strategy:**\n\n"
                "A common branching model:\n"
                "- `main` / `master`: Production-ready code only.\n"
                "- `develop`: Integration branch for features.\n"
                "- `feature/<name>`: Individual feature branches from develop.\n"
                "- `hotfix/<name>`: Emergency fixes branched from main.\n"
                "- `release/<version>`: Stabilization before production release.\n\n"
                "```bash\n"
                "# Create a feature branch\n"
                "git checkout develop\n"
                "git pull origin develop\n"
                "git checkout -b feature/add-user-validation\n"
                "```\n"
            )
        elif "merge" in msg_lower or "rebase" in msg_lower:
            response += (
                "**Merge vs Rebase:**\n\n"
                "- **Merge**: Preserves complete history with a merge commit. Safer for "
                "shared branches.\n"
                "- **Rebase**: Creates a linear history by replaying commits. Cleaner log "
                "but rewrites history.\n\n"
                "**Rule of thumb**: Rebase local/private branches, merge shared/public branches.\n\n"
                "```bash\n"
                "# Merge approach\n"
                "git checkout develop\n"
                "git merge feature/my-feature\n"
                "\n"
                "# Rebase approach (for local branches only)\n"
                "git checkout feature/my-feature\n"
                "git rebase develop\n"
                "```\n"
            )
        elif "cherry-pick" in msg_lower:
            response += (
                "**Git Cherry-Pick:**\n\n"
                "Cherry-pick applies a specific commit from one branch to another "
                "without merging the entire branch.\n\n"
                "```bash\n"
                "# Apply a specific commit to the current branch\n"
                "git cherry-pick <commit-hash>\n"
                "\n"
                "# Cherry-pick without committing (stage changes only)\n"
                "git cherry-pick --no-commit <commit-hash>\n"
                "```\n"
                "Use sparingly -- it creates duplicate commits and can cause merge conflicts later.\n"
            )
        else:
            response += (
                "**Essential Git Commands:**\n\n"
                "```bash\n"
                "git status                    # Check working directory state\n"
                "git log --oneline -10         # View recent commit history\n"
                "git diff                      # View unstaged changes\n"
                "git stash                     # Temporarily save uncommitted changes\n"
                "git stash pop                 # Restore stashed changes\n"
                "git reset --soft HEAD~1       # Undo last commit, keep changes staged\n"
                "git reflog                    # Recovery tool for lost commits\n"
                "```\n"
            )

        return response

    def _respond_algorithms(self, msg_lower):
        response = "**Algorithms and Data Structures Guidance**\n\n"

        if "binary search" in msg_lower:
            response += (
                "**Binary Search** -- O(log n) time complexity\n\n"
                "Binary search works on sorted arrays by repeatedly dividing the "
                "search interval in half.\n\n"
                "```python\n"
                "def binary_search(arr, target):\n"
                "    left, right = 0, len(arr) - 1\n"
                "    while left <= right:\n"
                "        mid = (left + right) // 2\n"
                "        if arr[mid] == target:\n"
                "            return mid\n"
                "        elif arr[mid] < target:\n"
                "            left = mid + 1\n"
                "        else:\n"
                "            right = mid - 1\n"
                "    return -1  # Not found\n"
                "```\n\n"
                "**Key requirement**: The input array must be sorted.\n"
            )
        elif "sort" in msg_lower:
            response += (
                "**Sorting Algorithm Comparison:**\n\n"
                "| Algorithm      | Best   | Average  | Worst    | Space  | Stable |\n"
                "|----------------|--------|----------|----------|--------|--------|\n"
                "| Quick Sort     | O(n log n) | O(n log n) | O(n^2) | O(log n) | No  |\n"
                "| Merge Sort     | O(n log n) | O(n log n) | O(n log n) | O(n) | Yes |\n"
                "| Heap Sort      | O(n log n) | O(n log n) | O(n log n) | O(1) | No  |\n"
                "| Tim Sort       | O(n)   | O(n log n) | O(n log n) | O(n) | Yes |\n"
                "| Insertion Sort | O(n)   | O(n^2)   | O(n^2)   | O(1)  | Yes |\n\n"
                "Python's built-in `sorted()` and `.sort()` use TimSort.\n"
            )
        elif "dynamic programming" in msg_lower or "dp" in msg_lower:
            response += (
                "**Dynamic Programming Approach:**\n\n"
                "1. **Identify overlapping subproblems**: Can the problem be broken into "
                "smaller, repeating subproblems?\n"
                "2. **Define the state**: What variables describe a subproblem uniquely?\n"
                "3. **Write the recurrence relation**: How does the current state relate "
                "to previous states?\n"
                "4. **Choose top-down (memoization) or bottom-up (tabulation)**.\n"
                "5. **Optimize space** if only recent states are needed.\n\n"
                "```python\n"
                "# Example: Fibonacci with memoization\n"
                "from functools import lru_cache\n"
                "\n"
                "@lru_cache(maxsize=None)\n"
                "def fib(n):\n"
                "    if n <= 1:\n"
                "        return n\n"
                "    return fib(n - 1) + fib(n - 2)\n"
                "```\n"
            )
        elif "big o" in msg_lower or "complexity" in msg_lower:
            response += (
                "**Time Complexity Reference:**\n\n"
                "| Complexity | Name         | Example                    |\n"
                "|------------|------------- |----------------------------|\n"
                "| O(1)       | Constant     | Hash table lookup          |\n"
                "| O(log n)   | Logarithmic  | Binary search              |\n"
                "| O(n)       | Linear       | Array traversal            |\n"
                "| O(n log n) | Linearithmic | Merge sort                 |\n"
                "| O(n^2)     | Quadratic    | Nested loops               |\n"
                "| O(2^n)     | Exponential  | Recursive subset generation|\n\n"
                "**Tips**: Aim for O(n log n) or better for large inputs. "
                "Use hash maps for O(1) lookups.\n"
            )
        else:
            response += (
                "**Common Data Structures and When to Use Them:**\n\n"
                "- **Array/List**: Sequential access, indexed lookup. Use when order matters.\n"
                "- **Hash Map/Dict**: O(1) key-value lookup. Use for frequency counts, caching.\n"
                "- **Stack**: LIFO. Use for undo operations, expression parsing, DFS.\n"
                "- **Queue**: FIFO. Use for BFS, task scheduling, buffering.\n"
                "- **Tree (BST)**: O(log n) search/insert. Use for sorted data, range queries.\n"
                "- **Heap**: O(1) min/max access. Use for priority queues, top-K problems.\n"
                "- **Graph**: Use for networks, dependencies, shortest path problems.\n\n"
                "Feel free to ask about a specific algorithm or data structure for a detailed explanation.\n"
            )

        return response

    def _respond_performance(self, msg_lower, title, category):
        response = "**Performance and Optimization Guidance**\n\n"

        if "memory leak" in msg_lower:
            response += (
                "**Common Memory Leak Patterns:**\n\n"
                "1. **Unclosed resources**: Database connections, file handles, network "
                "sockets not released after use.\n"
                "2. **Event listener accumulation**: Registering listeners without removing "
                "them on component teardown.\n"
                "3. **Growing collections**: Maps, lists, or caches that grow without bounds "
                "or eviction policies.\n"
                "4. **Static references**: Holding references to large objects in static "
                "fields preventing garbage collection.\n"
                "5. **Thread-local variables**: Not cleaned up after thread pool reuse.\n\n"
                "**Detection**: Use profiling tools (VisualVM for Java, memory_profiler for "
                "Python, Chrome DevTools for JavaScript).\n"
            )
        elif "cache" in msg_lower:
            response += (
                "**Caching Strategies:**\n\n"
                "- **Cache-Aside (Lazy)**: Application checks cache first, loads from DB on miss.\n"
                "- **Write-Through**: Writes go to cache and DB simultaneously.\n"
                "- **Write-Behind**: Writes go to cache, asynchronously synced to DB.\n"
                "- **TTL-Based**: Set expiration to automatically invalidate stale data.\n\n"
                "**Eviction Policies**: LRU (Least Recently Used), LFU (Least Frequently "
                "Used), FIFO.\n\n"
                "```python\n"
                "from functools import lru_cache\n"
                "\n"
                "@lru_cache(maxsize=128)\n"
                "def get_user_profile(user_id):\n"
                "    return db.query(User).get(user_id)\n"
                "```\n"
            )
        else:
            response += (
                "**General Optimization Checklist:**\n\n"
                "1. **Profile before optimizing**: Identify the actual bottleneck with profiling tools.\n"
                "2. **Database queries**: Add indexes, avoid N+1 queries, use pagination.\n"
                "3. **Algorithm complexity**: Ensure you are using the right data structures.\n"
                "4. **I/O optimization**: Use connection pooling, batch operations, async I/O.\n"
                "5. **Caching**: Cache frequently accessed, rarely changing data.\n"
                "6. **Resource management**: Close connections, limit thread pool sizes.\n"
            )

        if title:
            response += f"\n**Context**: Current bug '{title}' ({category}) may be related to these patterns."

        return response

    def _respond_security(self, msg_lower, title, category):
        response = "**Security Best Practices**\n\n"

        if "injection" in msg_lower or "sql injection" in msg_lower:
            response += (
                "**Preventing SQL Injection:**\n\n"
                "1. **Always use parameterized queries** -- never concatenate user input into SQL.\n"
                "2. Use your ORM's query builder (SQLAlchemy, Hibernate, etc.).\n"
                "3. Apply input validation and whitelisting.\n"
                "4. Use least-privilege database accounts.\n\n"
                "```python\n"
                "# UNSAFE -- vulnerable to injection\n"
                "query = f\"SELECT * FROM users WHERE name = '{user_input}'\"\n"
                "\n"
                "# SAFE -- parameterized query\n"
                "query = \"SELECT * FROM users WHERE name = :name\"\n"
                "result = db.execute(text(query), {'name': user_input})\n"
                "```\n"
            )
        elif "xss" in msg_lower:
            response += (
                "**Preventing Cross-Site Scripting (XSS):**\n\n"
                "1. **Escape output**: HTML-encode all user-generated content before rendering.\n"
                "2. **Content Security Policy**: Set CSP headers to restrict inline scripts.\n"
                "3. **Use frameworks' built-in protection**: React auto-escapes JSX, "
                "Jinja2 auto-escapes templates.\n"
                "4. **Sanitize input**: Use libraries like DOMPurify for HTML input.\n"
                "5. **HttpOnly cookies**: Prevent JavaScript access to session cookies.\n"
            )
        elif "jwt" in msg_lower or "token" in msg_lower or "auth" in msg_lower:
            response += (
                "**Authentication and JWT Best Practices:**\n\n"
                "1. Use strong secret keys (256+ bits) for JWT signing.\n"
                "2. Set reasonable token expiration times.\n"
                "3. Store tokens in httpOnly cookies (not localStorage) for web apps.\n"
                "4. Implement token refresh mechanisms.\n"
                "5. Validate token claims (issuer, audience, expiration) on every request.\n"
                "6. Use HTTPS exclusively for token transmission.\n"
            )
        else:
            response += (
                "**Security Checklist for Applications:**\n\n"
                "1. Input validation and sanitization on all user inputs.\n"
                "2. Parameterized queries for all database operations.\n"
                "3. Output encoding to prevent XSS.\n"
                "4. HTTPS with TLS 1.2+ for all communications.\n"
                "5. Secure authentication with hashed passwords (bcrypt/argon2).\n"
                "6. Role-based access control (RBAC) for authorization.\n"
                "7. Rate limiting to prevent brute-force attacks.\n"
                "8. Security headers (CSP, X-Frame-Options, HSTS).\n"
                "9. Regular dependency vulnerability scanning.\n"
                "10. Logging and monitoring for security events.\n"
            )

        return response

    def _respond_architecture(self, msg_lower):
        response = "**Software Architecture and Design Guidance**\n\n"

        if "solid" in msg_lower:
            response += (
                "**SOLID Principles:**\n\n"
                "- **S -- Single Responsibility**: A class should have only one reason to change.\n"
                "- **O -- Open/Closed**: Open for extension, closed for modification.\n"
                "- **L -- Liskov Substitution**: Subtypes must be substitutable for their base types.\n"
                "- **I -- Interface Segregation**: Prefer specific interfaces over general-purpose ones.\n"
                "- **D -- Dependency Inversion**: Depend on abstractions, not concrete implementations.\n\n"
                "These principles help create maintainable, testable, and extensible codebases.\n"
            )
        elif "design pattern" in msg_lower:
            response += (
                "**Common Design Patterns:**\n\n"
                "**Creational:**\n"
                "- Factory Method: Delegate object creation to subclasses.\n"
                "- Singleton: Ensure a single instance with global access.\n"
                "- Builder: Construct complex objects step by step.\n\n"
                "**Structural:**\n"
                "- Adapter: Make incompatible interfaces work together.\n"
                "- Decorator: Add responsibilities dynamically.\n"
                "- Facade: Provide a simplified interface to a complex subsystem.\n\n"
                "**Behavioral:**\n"
                "- Observer: Notify dependents of state changes.\n"
                "- Strategy: Encapsulate interchangeable algorithms.\n"
                "- Command: Encapsulate requests as objects.\n"
            )
        elif "microservice" in msg_lower or "monolith" in msg_lower:
            response += (
                "**Microservices vs Monolith:**\n\n"
                "| Aspect | Monolith | Microservices |\n"
                "|--------|----------|---------------|\n"
                "| Deployment | Single unit | Independent services |\n"
                "| Scaling | Scale entire app | Scale individual services |\n"
                "| Complexity | Simpler initially | Higher operational complexity |\n"
                "| Team | Single team | Autonomous teams per service |\n"
                "| Data | Shared database | Database per service |\n\n"
                "**Recommendation**: Start monolithic, extract services when the team "
                "and traffic justify the operational overhead.\n"
            )
        else:
            response += (
                "**Architecture Decision Checklist:**\n\n"
                "1. Identify system quality attributes (scalability, latency, availability).\n"
                "2. Choose appropriate patterns (layered, event-driven, CQRS, etc.).\n"
                "3. Define clear module boundaries and interfaces.\n"
                "4. Plan for observability (logging, metrics, tracing).\n"
                "5. Document architectural decisions (ADRs).\n"
                "6. Design for failure (circuit breakers, retries, fallbacks).\n"
            )

        return response

    def _respond_debugging(self, msg_lower, title, stack_trace, failure_point):
        response = "**Debugging and Error Handling Guidance**\n\n"

        if stack_trace and ("stack trace" in msg_lower or "trace" in msg_lower):
            response += (
                f"**Reading the Stack Trace for '{title}':**\n\n"
                "1. Start from the bottom -- the last method call is where the error originated.\n"
                f"2. The failure point is at `{failure_point}`.\n"
                "3. Look for your application code (not framework/library frames) to find "
                "the relevant line.\n"
                "4. Check if the error is caused by null values, type mismatches, or "
                "resource unavailability.\n\n"
            )
        elif "error handling" in msg_lower or "exception" in msg_lower or "try catch" in msg_lower:
            response += (
                "**Error Handling Best Practices:**\n\n"
                "1. Catch specific exceptions, not generic Exception/Error.\n"
                "2. Log errors with context (input data, user ID, request ID).\n"
                "3. Fail fast -- validate inputs early and return clear error messages.\n"
                "4. Use custom exception classes for domain-specific errors.\n"
                "5. Never silently swallow exceptions (empty catch blocks).\n"
                "6. Implement global error handlers for unhandled exceptions.\n\n"
                "```python\n"
                "# Good: specific exception with context\n"
                "try:\n"
                "    result = process_data(input)\n"
                "except ValidationError as e:\n"
                "    logger.warning(f'Validation failed for input {input.id}: {e}')\n"
                "    raise HTTPException(status_code=400, detail=str(e))\n"
                "except DatabaseError as e:\n"
                "    logger.error(f'Database error processing {input.id}: {e}')\n"
                "    raise HTTPException(status_code=500, detail='Internal server error')\n"
                "```\n"
            )
        else:
            response += (
                "**Systematic Debugging Process:**\n\n"
                "1. **Reproduce**: Identify the exact steps to trigger the bug.\n"
                "2. **Isolate**: Narrow down the component or function causing the issue.\n"
                "3. **Inspect state**: Use debugger breakpoints, print statements, or "
                "logging to examine variable values.\n"
                "4. **Form hypothesis**: Based on the evidence, hypothesize the root cause.\n"
                "5. **Test fix**: Apply a minimal fix and verify it resolves the issue.\n"
                "6. **Prevent regression**: Write a test that catches this bug.\n\n"
                "**Tools**: IDE debuggers, logging frameworks, network inspectors (e.g., "
                "browser DevTools), database query analyzers.\n"
            )

        return response

    def _respond_devops(self, msg_lower):
        response = "**DevOps and Deployment Guidance**\n\n"

        if "docker" in msg_lower or "container" in msg_lower:
            response += (
                "**Docker Best Practices:**\n\n"
                "1. Use official base images and pin versions (e.g., `python:3.11-slim`).\n"
                "2. Use multi-stage builds to reduce image size.\n"
                "3. Copy requirements first, then code (for better layer caching).\n"
                "4. Use `.dockerignore` to exclude unnecessary files.\n"
                "5. Run as a non-root user in production.\n\n"
                "```dockerfile\n"
                "FROM python:3.11-slim\n"
                "WORKDIR /app\n"
                "COPY requirements.txt .\n"
                "RUN pip install --no-cache-dir -r requirements.txt\n"
                "COPY . .\n"
                "EXPOSE 8000\n"
                "CMD [\"uvicorn\", \"backend.app.main:app\", \"--host\", \"0.0.0.0\", \"--port\", \"8000\"]\n"
                "```\n"
            )
        elif "ci/cd" in msg_lower or "pipeline" in msg_lower or "github actions" in msg_lower:
            response += (
                "**CI/CD Pipeline Structure:**\n\n"
                "1. **Build**: Install dependencies, compile code.\n"
                "2. **Test**: Run unit tests, integration tests, linting.\n"
                "3. **Security Scan**: Check for vulnerable dependencies.\n"
                "4. **Deploy to Staging**: Deploy to a staging environment for review.\n"
                "5. **Deploy to Production**: After approval, deploy with rollback capability.\n\n"
                "**Key principles**: Automate everything, fail fast, keep pipelines under "
                "10 minutes, use environment-specific configurations.\n"
            )
        else:
            response += (
                "**Deployment Checklist:**\n\n"
                "1. Verify all tests pass in the CI pipeline.\n"
                "2. Review environment variables and secrets management.\n"
                "3. Set up health check endpoints for monitoring.\n"
                "4. Configure logging and alerting for production.\n"
                "5. Plan rollback strategy before deploying.\n"
                "6. Use blue-green or canary deployment for zero-downtime releases.\n"
            )

        return response

    def _respond_api(self, msg_lower):
        response = "**API Design and Development Guidance**\n\n"

        if "status code" in msg_lower:
            response += (
                "**HTTP Status Code Reference:**\n\n"
                "| Code | Meaning          | Usage                                |\n"
                "|------|------------------|--------------------------------------|\n"
                "| 200  | OK               | Successful GET/PUT                   |\n"
                "| 201  | Created          | Successful POST (resource created)   |\n"
                "| 204  | No Content       | Successful DELETE                    |\n"
                "| 400  | Bad Request      | Invalid input / validation error     |\n"
                "| 401  | Unauthorized     | Missing or invalid authentication    |\n"
                "| 403  | Forbidden        | Authenticated but not authorized     |\n"
                "| 404  | Not Found        | Resource does not exist              |\n"
                "| 409  | Conflict         | Resource state conflict              |\n"
                "| 422  | Unprocessable    | Semantic validation failure          |\n"
                "| 500  | Internal Error   | Unexpected server-side failure       |\n"
            )
        elif "rest" in msg_lower or "endpoint" in msg_lower:
            response += (
                "**RESTful API Design Principles:**\n\n"
                "1. Use nouns for resources: `/api/v1/users`, `/api/v1/bugs`.\n"
                "2. Use HTTP verbs for actions: GET (read), POST (create), PUT (update), DELETE.\n"
                "3. Version your API: `/api/v1/...`\n"
                "4. Use pagination for list endpoints: `?page=1&limit=20`.\n"
                "5. Return consistent error response format.\n"
                "6. Use proper status codes (see above).\n"
                "7. Support filtering, sorting, and searching via query parameters.\n"
            )
        else:
            response += (
                "**API Best Practices:**\n\n"
                "1. Document all endpoints (Swagger/OpenAPI).\n"
                "2. Validate all inputs at the API boundary.\n"
                "3. Use consistent response formats across all endpoints.\n"
                "4. Implement rate limiting and authentication.\n"
                "5. Log all requests with correlation IDs for debugging.\n"
                "6. Use CORS headers appropriately for web clients.\n"
            )

        return response

    def _respond_language(self, msg_lower):
        response = "**Programming Language Guidance**\n\n"

        if "python" in msg_lower:
            response += (
                "**Python Best Practices:**\n\n"
                "1. Follow PEP 8 style guide for consistent formatting.\n"
                "2. Use type hints for function signatures.\n"
                "3. Leverage list comprehensions and generators for clean iteration.\n"
                "4. Use context managers (`with` statement) for resource management.\n"
                "5. Prefer `pathlib` over `os.path` for file operations.\n"
                "6. Use virtual environments to isolate project dependencies.\n"
                "7. Write docstrings for all public functions and classes.\n\n"
                "```python\n"
                "# Modern Python example\n"
                "from pathlib import Path\n"
                "from typing import Optional\n"
                "\n"
                "def read_config(path: Path) -> Optional[dict]:\n"
                "    \"\"\"Read and parse a JSON configuration file.\"\"\"\n"
                "    if not path.exists():\n"
                "        return None\n"
                "    return json.loads(path.read_text())\n"
                "```\n"
            )
        elif "javascript" in msg_lower or "typescript" in msg_lower:
            response += (
                "**JavaScript/TypeScript Best Practices:**\n\n"
                "1. Use `const` by default, `let` when reassignment is needed.\n"
                "2. Prefer arrow functions for short callbacks.\n"
                "3. Use async/await over raw Promises for readability.\n"
                "4. Enable strict mode in TypeScript for type safety.\n"
                "5. Use optional chaining (`?.`) and nullish coalescing (`??`).\n"
                "6. Destructure objects and arrays for cleaner code.\n\n"
                "```javascript\n"
                "// Modern JavaScript\n"
                "const fetchUser = async (id) => {\n"
                "  const response = await fetch(`/api/users/${id}`);\n"
                "  if (!response.ok) throw new Error(`HTTP ${response.status}`);\n"
                "  return response.json();\n"
                "};\n"
                "```\n"
            )
        elif "java" in msg_lower:
            response += (
                "**Java Best Practices:**\n\n"
                "1. Use Optional instead of returning null.\n"
                "2. Prefer interfaces over abstract classes for contracts.\n"
                "3. Use try-with-resources for AutoCloseable objects.\n"
                "4. Leverage Stream API for collection processing.\n"
                "5. Follow naming conventions (camelCase for methods, PascalCase for classes).\n"
                "6. Use dependency injection frameworks (Spring) for loose coupling.\n"
            )
        else:
            response += (
                "**General Language-Agnostic Best Practices:**\n\n"
                "1. Write readable, self-documenting code with descriptive names.\n"
                "2. Keep functions small and focused (single responsibility).\n"
                "3. Handle errors explicitly -- do not ignore exceptions.\n"
                "4. Write tests alongside your code.\n"
                "5. Use version control (Git) for all code.\n"
                "6. Document public APIs and complex logic.\n"
            )

        return response

    def _respond_greeting(self, bug_code, title, category):
        response = (
            "**AI Coding Mentor**\n\n"
            f"I am here to assist you with bug **{bug_code}**"
        )
        if title:
            response += f" -- \"{title}\" ({category})"
        response += ".\n\n"

        response += (
            "You can ask me about:\n\n"
            "- **This bug**: Root cause analysis, fix recommendations, testing strategies\n"
            "- **Programming**: Python, Java, JavaScript, algorithms, data structures\n"
            "- **Databases**: SQL queries, indexing, normalization, transactions\n"
            "- **Architecture**: Design patterns, SOLID principles, microservices\n"
            "- **DevOps**: Docker, CI/CD, deployment strategies\n"
            "- **Security**: SQL injection prevention, XSS, authentication\n"
            "- **Git**: Branching, merging, cherry-picking, workflows\n"
            "- **Performance**: Memory leaks, caching, optimization\n"
            "- **Debugging**: Stack traces, error handling, systematic troubleshooting\n"
            "- **APIs**: REST design, HTTP status codes, best practices\n\n"
            "Ask any programming or software development question."
        )
        return response

    def _respond_general(self, msg_lower, title, category, bug_code, failure_point, recent_context):
        """
        General-purpose response for questions that do not match specific topic patterns.
        Provides a helpful, context-aware answer based on the question content and bug context.
        """
        response = ""

        # Check if the question seems related to the current bug
        bug_related_terms = []
        if title:
            bug_related_terms = [w.lower() for w in title.split() if len(w) > 3]

        is_bug_related = any(term in msg_lower for term in bug_related_terms) if bug_related_terms else False

        if is_bug_related or "this bug" in msg_lower or "this issue" in msg_lower or "current" in msg_lower:
            response = (
                f"**Regarding Bug {bug_code}: '{title}'**\n\n"
                f"**Category**: {category}\n"
                f"**Failure Point**: {failure_point}\n\n"
                "Based on the analysis of this bug:\n\n"
                "1. The issue originates from insufficient input validation or resource management "
                f"in the {category} layer.\n"
                "2. Implementing defensive checks at the identified failure point will prevent "
                "this class of errors.\n"
                "3. Adding comprehensive logging around the failure point will help diagnose "
                "similar issues in the future.\n\n"
                "For more specific guidance, try asking:\n"
                "- \"What is the root cause of this bug?\"\n"
                "- \"How do I fix this bug?\"\n"
                "- \"How do I write tests for this fix?\"\n"
            )
        elif "thank" in msg_lower or "thanks" in msg_lower:
            response = (
                "You are welcome. If you have additional questions about this bug, "
                "programming concepts, debugging strategies, or any other software "
                "development topic, feel free to ask."
            )
        elif "?" in msg_lower and len(msg_lower) > 10:
            # The user asked a question we don't have a specific handler for.
            # Provide a thoughtful general response based on detected keywords.
            response = self._generate_contextual_response(msg_lower, title, category, bug_code)
        else:
            response = (
                f"**AI Coding Mentor -- Bug {bug_code}**\n\n"
                f"I am assisting you with \"{title}\" ({category}).\n\n"
                "I can help with a wide range of programming and software development topics. "
                "Some examples of questions you can ask:\n\n"
                "- \"Why did this error occur?\"\n"
                "- \"How do I write a unit test for this fix?\"\n"
                "- \"Show me the recommended code fix.\"\n"
                "- \"How do I implement binary search in Python?\"\n"
                "- \"Explain SQL JOIN types.\"\n"
                "- \"What are common memory leak patterns?\"\n"
                "- \"How should I set up a Git branching strategy?\"\n"
                "- \"What are the SOLID design principles?\"\n\n"
                "Ask any question and I will provide a detailed response."
            )

        return response

    def _generate_contextual_response(self, msg_lower, title, category, bug_code):
        """Generate a helpful response for unmatched questions by analyzing content."""

        # Detect if the question is about concepts, definitions, or how-to
        if any(w in msg_lower for w in ["what is", "what are", "define", "meaning of", "difference between"]):
            return (
                f"**Concept Explanation**\n\n"
                "While I have specialized knowledge in bug analysis, debugging, and software "
                "development, I can provide guidance on the concept you asked about.\n\n"
                "Based on your question, here are some relevant points:\n\n"
                "1. Start by understanding the fundamental definition and purpose of the concept.\n"
                "2. Look at practical examples and use cases in real-world applications.\n"
                "3. Understand how it relates to the broader software development ecosystem.\n"
                "4. Practice implementing it in a small project or code exercise.\n\n"
                "For a more targeted answer, try rephrasing your question with specific "
                "technology keywords (e.g., Python, SQL, REST API, Git, Docker, etc.)."
            )

        elif any(w in msg_lower for w in ["how do i", "how to", "how can", "steps to", "guide"]):
            return (
                f"**How-To Guidance**\n\n"
                "Here is a general approach to the task you described:\n\n"
                "1. **Research**: Understand the requirements and constraints.\n"
                "2. **Plan**: Break the task into smaller, manageable steps.\n"
                "3. **Implement**: Write code incrementally, testing each step.\n"
                "4. **Test**: Verify your implementation with unit and integration tests.\n"
                "5. **Review**: Check for edge cases, error handling, and code quality.\n"
                "6. **Document**: Add comments and documentation for future maintainers.\n\n"
                "For a more specific answer, include details about the programming language, "
                "framework, or technology you are working with."
            )

        elif any(w in msg_lower for w in ["best practice", "recommend", "should i", "advice", "suggest"]):
            return (
                f"**Recommendations**\n\n"
                "General software development best practices:\n\n"
                "1. Write clean, readable code with meaningful variable and function names.\n"
                "2. Follow the DRY principle (Do not Repeat Yourself).\n"
                "3. Handle errors explicitly and provide helpful error messages.\n"
                "4. Write automated tests for critical paths.\n"
                "5. Use version control and write descriptive commit messages.\n"
                "6. Review code before merging (pair programming or pull requests).\n"
                "7. Monitor your application in production with logging and alerting.\n\n"
                "For context-specific recommendations, mention the specific technology stack "
                "or problem domain."
            )

        else:
            return (
                f"**AI Mentor Response**\n\n"
                "I can help with your question. To provide the most relevant guidance, "
                "I work best with questions about:\n\n"
                "- **Bug Analysis**: Root cause diagnosis, fix strategies, testing\n"
                "- **Programming**: Language-specific best practices, code patterns\n"
                "- **Databases**: SQL, query optimization, schema design\n"
                "- **Architecture**: Design patterns, system design, scalability\n"
                "- **DevOps**: Deployment, CI/CD, containerization\n"
                "- **Security**: Vulnerability prevention, authentication, encryption\n"
                "- **Version Control**: Git workflows, branching strategies\n\n"
                "Try rephrasing your question with more specific technical keywords, "
                "and I will provide a detailed, actionable response."
            )


chat_agent = ChatAgent()
