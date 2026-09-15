from typing import Dict, Any, List

class RemediationAgent:
    def __init__(self):
        self.name = "Remediation Agent"
        self.icon = "🛠️"

        # Each fix pattern now contains three strategy tiers
        self.fix_patterns = {
            'Null Reference': {
                'strategies': [
                    {
                        'name': 'Quick Hotfix',
                        'approach': 'Add a simple null guard at the failure point to prevent the crash immediately.',
                        'steps': [
                            'Add null/undefined check before the failing access',
                            'Return a safe default or log a warning',
                        ],
                        'codeExample': """// Quick Hotfix — null guard
const profile = user.getProfile();
if (profile == null) {
  log.warn("Profile is null for user: " + user.getId());
  return defaultProfile();
}
const name = profile.getName();""",
                        'pros': ['Fastest to deploy', 'Minimal code change', 'Low regression risk'],
                        'cons': ['Masks root cause', 'May hide upstream bugs', 'Technical debt'],
                        'effort': '30 min - 1 hour',
                        'risk': 'Low'
                    },
                    {
                        'name': 'Defensive Refactor',
                        'approach': 'Introduce Optional/Maybe types and validate at service boundaries with proper error propagation.',
                        'steps': [
                            'Wrap nullable returns with Optional<T> at service layer',
                            'Add @NonNull / @Nullable annotations for API contracts',
                            'Implement input validation at all public method entries',
                            'Write unit tests covering null input scenarios',
                        ],
                        'codeExample': """// Defensive Refactor — Optional pattern
public Optional<Profile> getProfile(Long userId) {
    User user = userRepo.findById(userId)
        .orElseThrow(() -> new UserNotFoundException(userId));
    return Optional.ofNullable(user.getProfile());
}

// Caller
String name = userService.getProfile(id)
    .map(Profile::getName)
    .orElse("Anonymous");""",
                        'pros': ['Addresses root cause', 'Type-safe contracts', 'Reusable pattern'],
                        'cons': ['Moderate effort', 'Requires updating callers', 'Needs code review'],
                        'effort': '2-4 hours',
                        'risk': 'Medium'
                    },
                    {
                        'name': 'Architectural Redesign',
                        'approach': 'Eliminate null from the domain model entirely using Null Object pattern and domain validation layer.',
                        'steps': [
                            'Introduce a NullObject implementation for the affected entity',
                            'Create a domain validation layer that enforces invariants at creation',
                            'Replace null returns with domain-specific empty/default objects',
                            'Add integration tests verifying end-to-end data flow',
                            'Update API documentation and team coding guidelines',
                        ],
                        'codeExample': """// Architectural — Null Object Pattern
public class NullProfile implements Profile {
    public String getName() { return "Guest"; }
    public boolean isNull()  { return true; }
}

// Factory ensures non-null
public Profile getProfileOrDefault(Long userId) {
    Profile p = profileRepo.findByUserId(userId);
    return (p != null) ? p : new NullProfile();
}""",
                        'pros': ['Permanent fix', 'Eliminates null from domain', 'Best long-term maintainability'],
                        'cons': ['Highest effort', 'Requires architectural review', 'May need data migration'],
                        'effort': '1-2 days',
                        'risk': 'High (requires thorough testing)'
                    }
                ]
            },
            'Resource Exhaustion': {
                'strategies': [
                    {
                        'name': 'Quick Hotfix',
                        'approach': 'Add explicit close/cleanup calls at the immediate leak location.',
                        'steps': [
                            'Identify the unclosed resource in the stack trace',
                            'Add explicit close() call in a finally block',
                        ],
                        'codeExample': """// Quick Hotfix — explicit close
Connection conn = null;
try {
    conn = dataSource.getConnection();
    // ... use connection
} finally {
    if (conn != null) conn.close();
}""",
                        'pros': ['Stops the leak immediately', 'Small change footprint'],
                        'cons': ['Only fixes one location', 'Other leak sites may exist'],
                        'effort': '30 min - 1 hour',
                        'risk': 'Low'
                    },
                    {
                        'name': 'Defensive Refactor',
                        'approach': 'Adopt try-with-resources across the codebase and add pool monitoring.',
                        'steps': [
                            'Convert all resource acquisitions to try-with-resources',
                            'Add connection pool monitoring and alerting',
                            'Configure pool size limits and idle timeouts',
                            'Add unit tests verifying resource cleanup',
                        ],
                        'codeExample': """// Defensive Refactor — try-with-resources
try (Connection conn = dataSource.getConnection();
     PreparedStatement ps = conn.prepareStatement(sql);
     ResultSet rs = ps.executeQuery()) {
    while (rs.next()) {
        processRow(rs);
    }
} // All resources auto-closed""",
                        'pros': ['Eliminates entire class of leaks', 'Industry best practice'],
                        'cons': ['Must audit all resource usage', 'Moderate refactoring effort'],
                        'effort': '2-4 hours',
                        'risk': 'Medium'
                    },
                    {
                        'name': 'Architectural Redesign',
                        'approach': 'Introduce a resource management abstraction layer with automatic lifecycle tracking.',
                        'steps': [
                            'Create a ResourceManager abstraction with automatic lifecycle tracking',
                            'Implement health check endpoints for pool monitoring',
                            'Add circuit breaker pattern for resource acquisition',
                            'Set up Prometheus/Grafana metrics for pool utilization',
                            'Document resource management guidelines for the team',
                        ],
                        'codeExample': """// Architectural — Resource Manager with monitoring
@Component
public class ManagedDataSource implements AutoCloseable {
    private final HikariDataSource pool;
    private final MeterRegistry metrics;

    public Connection acquire() {
        metrics.counter("db.connections.acquired").increment();
        return pool.getConnection();
    }

    @Scheduled(fixedRate = 60000)
    public void healthCheck() {
        int active = pool.getHikariPoolMXBean().getActiveConnections();
        if (active > pool.getMaximumPoolSize() * 0.8) {
            alertService.warn("Connection pool near capacity");
        }
    }
}""",
                        'pros': ['Full observability', 'Prevents future exhaustion', 'Production-grade resilience'],
                        'cons': ['Significant development effort', 'Requires infrastructure changes'],
                        'effort': '1-3 days',
                        'risk': 'High (requires staging validation)'
                    }
                ]
            },
            'Concurrency': {
                'strategies': [
                    {
                        'name': 'Quick Hotfix',
                        'approach': 'Add synchronized block around the critical section.',
                        'steps': [
                            'Wrap the shared mutable state access with synchronized block',
                            'Verify the lock granularity is correct',
                        ],
                        'codeExample': """// Quick Hotfix — synchronized
synchronized(inventoryLock) {
    if (inventory.getStock() > 0) {
        inventory.decrementStock();
    }
}""",
                        'pros': ['Immediately prevents race condition', 'Simple to reason about'],
                        'cons': ['May reduce throughput', 'Coarse-grained locking'],
                        'effort': '30 min - 1 hour',
                        'risk': 'Low'
                    },
                    {
                        'name': 'Defensive Refactor',
                        'approach': 'Use database-level locking (SELECT FOR UPDATE) with proper transaction boundaries.',
                        'steps': [
                            'Apply SELECT FOR UPDATE on critical data reads',
                            'Ensure proper @Transactional boundaries',
                            'Replace mutable state with atomic operations where possible',
                            'Add concurrency stress tests',
                        ],
                        'codeExample': """// Defensive Refactor — optimistic locking
@Transactional
public void processOrder(Long itemId) {
    Item item = itemRepo.findByIdWithLock(itemId);
    if (item.getStock() > 0) {
        item.setStock(item.getStock() - 1);
        itemRepo.save(item);
    } else {
        throw new OutOfStockException(itemId);
    }
}""",
                        'pros': ['Database-enforced consistency', 'Handles distributed scenarios'],
                        'cons': ['Potential deadlocks if misused', 'Requires careful transaction design'],
                        'effort': '3-6 hours',
                        'risk': 'Medium'
                    },
                    {
                        'name': 'Architectural Redesign',
                        'approach': 'Adopt event-driven architecture with message queues to serialize concurrent operations.',
                        'steps': [
                            'Introduce a message queue for serializing inventory operations',
                            'Implement CQRS pattern separating reads from writes',
                            'Add idempotency keys for retry safety',
                            'Implement saga pattern for distributed transactions',
                            'Add load testing and chaos engineering validation',
                        ],
                        'codeExample': """// Architectural — Event-driven serialization
@Service
public class OrderEventHandler {
    @RabbitListener(queues = "orders")
    @Transactional
    public void handleOrder(OrderEvent event) {
        Item item = itemRepo.findById(event.getItemId());
        if (item.getStock() > 0) {
            item.decrementStock();
            eventPublisher.publish(new OrderConfirmed(event));
        } else {
            eventPublisher.publish(new OrderRejected(event));
        }
    }
}""",
                        'pros': ['Eliminates race conditions by design', 'Horizontally scalable'],
                        'cons': ['Significant complexity', 'Eventual consistency trade-offs'],
                        'effort': '2-5 days',
                        'risk': 'High (architectural change)'
                    }
                ]
            },
            'Security': {
                'strategies': [
                    {
                        'name': 'Quick Hotfix',
                        'approach': 'Replace the vulnerable query with a parameterized statement immediately.',
                        'steps': [
                            'Switch from string concatenation to parameterized query',
                            'Validate the fix prevents the specific attack vector',
                        ],
                        'codeExample': """// Quick Hotfix — parameterized query
PreparedStatement ps = conn.prepareStatement(
    "SELECT * FROM users WHERE name = ?"
);
ps.setString(1, userInput);""",
                        'pros': ['Blocks the immediate vulnerability', 'Minimal change'],
                        'cons': ['Other injection points may exist', 'Does not add defense-in-depth'],
                        'effort': '30 min - 1 hour',
                        'risk': 'Critical — Deploy ASAP'
                    },
                    {
                        'name': 'Defensive Refactor',
                        'approach': 'Audit all input paths, add validation/sanitization, and implement security headers.',
                        'steps': [
                            'Audit all user input entry points for injection risks',
                            'Implement input validation and sanitization at all boundaries',
                            'Add output encoding appropriate to the rendering context',
                            'Configure security headers (CSP, X-Frame-Options, HSTS)',
                            'Run automated security scan (OWASP ZAP)',
                        ],
                        'codeExample': """// Defensive Refactor — input validation layer
@Component
public class InputValidator {
    public String sanitize(String input) {
        if (input == null) return "";
        // Strip potential injection characters
        return input.replaceAll("[;'\"\\\\]", "")
                     .trim()
                     .substring(0, Math.min(input.length(), 500));
    }
}""",
                        'pros': ['Comprehensive protection', 'Industry standard approach'],
                        'cons': ['Requires full codebase audit', 'May break legitimate input'],
                        'effort': '4-8 hours',
                        'risk': 'Medium'
                    },
                    {
                        'name': 'Architectural Redesign',
                        'approach': 'Adopt ORM with automatic parameterization, WAF, and security pipeline.',
                        'steps': [
                            'Migrate raw SQL to ORM (e.g. SQLAlchemy, Hibernate)',
                            'Implement Web Application Firewall (WAF) rules',
                            'Add rate limiting and request throttling',
                            'Implement Content Security Policy headers',
                            'Set up automated SAST/DAST in CI/CD pipeline',
                            'Conduct penetration testing',
                        ],
                        'codeExample': """// Architectural — ORM eliminates SQL injection
// SQLAlchemy (Python)
user = db.query(User).filter(User.name == user_input).first()

// Hibernate (Java)
User user = session.createQuery(
    "FROM User WHERE name = :name", User.class)
    .setParameter("name", userInput)
    .getSingleResult();""",
                        'pros': ['Eliminates entire vulnerability class', 'Defense-in-depth'],
                        'cons': ['Major migration effort', 'ORM learning curve', 'Performance tuning needed'],
                        'effort': '2-5 days',
                        'risk': 'High (requires migration plan)'
                    }
                ]
            },
            'Type Error': {
                'strategies': [
                    {
                        'name': 'Quick Hotfix',
                        'approach': 'Add runtime type check before the failing operation.',
                        'steps': [
                            'Add typeof / instanceof guard before the failing call',
                            'Return safe default for unexpected types',
                        ],
                        'codeExample': """// Quick Hotfix
if (!Array.isArray(data)) {
    console.warn('Expected array, got:', typeof data);
    return [];
}
return data.map(item => item?.value ?? null);""",
                        'pros': ['Prevents crash', 'Simple and safe'],
                        'cons': ['Does not fix upstream type mismatch'],
                        'effort': '15-30 min',
                        'risk': 'Low'
                    },
                    {
                        'name': 'Defensive Refactor',
                        'approach': 'Add TypeScript types or JSDoc annotations and validate at boundaries.',
                        'steps': [
                            'Add TypeScript interfaces or JSDoc type annotations',
                            'Implement Zod/Joi schema validation at API boundaries',
                            'Write unit tests for type edge cases',
                        ],
                        'codeExample': """// Defensive Refactor — typed + validated
interface DataItem { value: string; }

function processData(data: DataItem[]): string[] {
    return data.map(item => item.value);
}""",
                        'pros': ['Compile-time safety', 'Self-documenting code'],
                        'cons': ['Requires TypeScript migration or JSDoc effort'],
                        'effort': '1-3 hours',
                        'risk': 'Low'
                    },
                    {
                        'name': 'Architectural Redesign',
                        'approach': 'Migrate to TypeScript strict mode across the project.',
                        'steps': [
                            'Enable TypeScript strict mode in tsconfig.json',
                            'Migrate all .js files to .ts with proper types',
                            'Add CI lint check rejecting any/unknown types',
                            'Implement runtime schema validation at API layer',
                        ],
                        'codeExample': """// Architectural — full TypeScript strict
// tsconfig.json: "strict": true, "noImplicitAny": true
import { z } from 'zod';

const DataSchema = z.array(z.object({ value: z.string() }));

export function processData(rawInput: unknown): string[] {
    const data = DataSchema.parse(rawInput);
    return data.map(item => item.value);
}""",
                        'pros': ['Zero runtime type errors', 'Full codebase safety'],
                        'cons': ['Large migration effort', 'Requires team buy-in'],
                        'effort': '1-3 days',
                        'risk': 'Medium'
                    }
                ]
            },
            'Timeout': {
                'strategies': [
                    {
                        'name': 'Quick Hotfix',
                        'approach': 'Increase timeout threshold and add basic retry.',
                        'steps': [
                            'Increase timeout value for the failing call',
                            'Add a single retry on timeout failure',
                        ],
                        'codeExample': """// Quick Hotfix — increased timeout
const controller = new AbortController();
setTimeout(() => controller.abort(), 10000); // 10s
const response = await fetch(url, { signal: controller.signal });""",
                        'pros': ['Immediate relief', 'No architectural change'],
                        'cons': ['Does not fix the slow operation', 'May just delay the failure'],
                        'effort': '15-30 min',
                        'risk': 'Low'
                    },
                    {
                        'name': 'Defensive Refactor',
                        'approach': 'Optimize the slow operation and add retry with exponential backoff.',
                        'steps': [
                            'Profile the slow operation to find the bottleneck',
                            'Optimize query/API call causing the timeout',
                            'Implement retry with exponential backoff',
                            'Add circuit breaker to prevent cascade failures',
                        ],
                        'codeExample': """// Defensive Refactor — retry with backoff
async function fetchWithRetry(url, retries = 3) {
    for (let i = 0; i < retries; i++) {
        try {
            const ctrl = new AbortController();
            const t = setTimeout(() => ctrl.abort(), 5000);
            const res = await fetch(url, { signal: ctrl.signal });
            clearTimeout(t);
            return res;
        } catch (err) {
            if (i === retries - 1) throw err;
            await new Promise(r => setTimeout(r, 1000 * 2 ** i));
        }
    }
}""",
                        'pros': ['Handles transient failures', 'Prevents cascade'],
                        'cons': ['Does not fix slow root operation'],
                        'effort': '2-3 hours',
                        'risk': 'Medium'
                    },
                    {
                        'name': 'Architectural Redesign',
                        'approach': 'Move long-running work to async queues with progress polling.',
                        'steps': [
                            'Move the long-running operation to a background worker',
                            'Return a job ID immediately for status polling',
                            'Implement WebSocket or SSE for progress updates',
                            'Add dead letter queue for failed jobs',
                        ],
                        'codeExample': """// Architectural — async job pattern
@app.post("/api/process")
async def start_job(data: ProcessRequest):
    job_id = queue.enqueue(process_heavy_task, data)
    return {"jobId": job_id, "status": "queued"}

@app.get("/api/jobs/{job_id}")
async def check_status(job_id: str):
    job = queue.get(job_id)
    return {"status": job.status, "progress": job.progress}""",
                        'pros': ['No timeout possible', 'Scalable to any workload'],
                        'cons': ['Adds infrastructure complexity', 'Eventual consistency'],
                        'effort': '1-3 days',
                        'risk': 'High (new infrastructure)'
                    }
                ]
            },
            'SQL Error': {
                'strategies': [
                    {
                        'name': 'Quick Hotfix',
                        'approach': 'Fix the SQL syntax and switch to parameterized query.',
                        'steps': [
                            'Correct the SQL syntax error',
                            'Use parameterized query instead of string concatenation',
                        ],
                        'codeExample': """// Quick Hotfix
db.query("SELECT * FROM items WHERE id = ?", [itemId]);""",
                        'pros': ['Immediate fix', 'Prevents injection'],
                        'cons': ['Only fixes one query'],
                        'effort': '15-30 min',
                        'risk': 'Low'
                    },
                    {
                        'name': 'Defensive Refactor',
                        'approach': 'Adopt query builder or ORM for all database operations.',
                        'steps': [
                            'Replace raw SQL with ORM or query builder',
                            'Add query logging for debugging',
                            'Test queries against dev database',
                            'Add database migration scripts for schema changes',
                        ],
                        'codeExample': """// Defensive Refactor — ORM
items = db.query(Item).filter(
    Item.category == category
).order_by(Item.created_at.desc()).limit(20).all()""",
                        'pros': ['Type-safe queries', 'Portable across DB engines'],
                        'cons': ['ORM learning curve', 'Some complex queries harder to express'],
                        'effort': '2-4 hours',
                        'risk': 'Medium'
                    },
                    {
                        'name': 'Architectural Redesign',
                        'approach': 'Implement repository pattern with database migration framework.',
                        'steps': [
                            'Create a repository layer abstracting all data access',
                            'Add Alembic/Flyway migration framework for schema versioning',
                            'Implement read/write replica support',
                            'Add query performance monitoring',
                        ],
                        'codeExample': """// Architectural — Repository Pattern
class ItemRepository:
    def __init__(self, db: Session):
        self.db = db

    def find_by_category(self, category: str, limit: int = 20):
        return self.db.query(Item).filter(
            Item.category == category
        ).limit(limit).all()

    def create(self, data: ItemCreate) -> Item:
        item = Item(**data.dict())
        self.db.add(item)
        self.db.commit()
        return item""",
                        'pros': ['Clean separation of concerns', 'Testable with mocks'],
                        'cons': ['More boilerplate code', 'Overhead for simple projects'],
                        'effort': '1-2 days',
                        'risk': 'Medium'
                    }
                ]
            },
            'IO Error': {
                'strategies': [
                    {
                        'name': 'Quick Hotfix',
                        'approach': 'Add existence check and try-catch around the failing IO operation.',
                        'steps': [
                            'Add file/path existence check before access',
                            'Wrap IO operation in try-catch with fallback',
                        ],
                        'codeExample': """// Quick Hotfix
if (fs.existsSync(filePath)) {
    try {
        return fs.readFileSync(filePath);
    } catch (err) {
        return defaultData();
    }
}""",
                        'pros': ['Prevents crash', 'Simple'],
                        'cons': ['Does not address why the file is missing'],
                        'effort': '15-30 min',
                        'risk': 'Low'
                    },
                    {
                        'name': 'Defensive Refactor',
                        'approach': 'Implement proper error handling, logging, and configurable file paths.',
                        'steps': [
                            'Add structured error handling for all IO operations',
                            'Make file paths configurable via environment variables',
                            'Add logging for IO failures with context',
                            'Implement health check for required file dependencies',
                        ],
                        'codeExample': """// Defensive Refactor
import { readFile } from 'fs/promises';

async function loadConfig(path) {
    try {
        const data = await readFile(path, 'utf-8');
        return JSON.parse(data);
    } catch (err) {
        logger.error({ path, error: err.message }, 'Config load failed');
        return getDefaultConfig();
    }
}""",
                        'pros': ['Robust error handling', 'Observable failures'],
                        'cons': ['Some refactoring needed'],
                        'effort': '1-2 hours',
                        'risk': 'Low'
                    },
                    {
                        'name': 'Architectural Redesign',
                        'approach': 'Abstract file access behind a storage service supporting local, S3, and fallbacks.',
                        'steps': [
                            'Create a StorageService interface with local/cloud implementations',
                            'Implement fallback chain (local → S3 → default)',
                            'Add file integrity checks (checksums)',
                            'Implement caching layer for frequently read files',
                        ],
                        'codeExample': """// Architectural — Storage abstraction
class StorageService:
    def read(self, key: str) -> bytes:
        for backend in [self.local, self.s3, self.default]:
            try:
                return backend.read(key)
            except FileNotFoundError:
                continue
        raise StorageError(f"File not found: {key}")""",
                        'pros': ['Cloud-ready', 'Resilient to failures'],
                        'cons': ['Over-engineering for simple cases'],
                        'effort': '1-2 days',
                        'risk': 'Medium'
                    }
                ]
            }
        }

    def analyze(self, bug_report: Dict[str, Any], triage_result: Dict[str, Any], log_result: Dict[str, Any], root_cause_result: Dict[str, Any], duplicate_result: Dict[str, Any], rag_result: Dict[str, Any] = None) -> Dict[str, Any]:
        title = bug_report.get("title", "")
        description = bug_report.get("description", "")
        stack_trace = bug_report.get("stackTrace", "") or bug_report.get("stack_trace", "") or ""
        combined_text = f"{title} {description} {stack_trace}".lower()

        matched_fix, matched_key = self._match_fix_pattern(log_result, root_cause_result, combined_text)
        historical_fixes = self._get_historical_fixes(duplicate_result)

        # Merge RAG retrieved resolutions into historical_fixes if available
        if rag_result and rag_result.get("items"):
            for rag_item in rag_result["items"]:
                if not any(h.get("bugId") == rag_item.get("id") for h in historical_fixes):
                    historical_fixes.append({
                        "bugId": rag_item.get("id"),
                        "title": rag_item.get("title"),
                        "resolution": rag_item.get("confirmedResolution"),
                        "similarity": f"{rag_item.get('similarityScore', 0)}% (RAG Vector match)"
                    })

        strategies = matched_fix.get("strategies", [])

        # Use the middle strategy (Defensive Refactor) as the primary recommendation
        primary = strategies[1] if len(strategies) > 1 else (strategies[0] if strategies else {})
        steps = primary.get("steps", [])
        code_example = primary.get("codeExample")
        effort = primary.get("effort", "2-4 hours")
        risk = primary.get("risk", "Medium")

        formatted_strategies = [
            {
                "name": s["name"],
                "approach": s["approach"],
                "description": s["approach"],
                "steps": s["steps"],
                "codeExample": s.get("codeExample"),
                "codeSnippet": s.get("codeExample"),
                "pros": s.get("pros", []),
                "cons": s.get("cons", []),
                "effort": s.get("effort", "Unknown"),
                "risk": s.get("risk", "Unknown"),
            }
            for s in strategies
        ]

        strategy_dict = {
            "hotfix": formatted_strategies[0] if len(formatted_strategies) > 0 else {},
            "refactor": formatted_strategies[1] if len(formatted_strategies) > 1 else {},
            "architecture": formatted_strategies[2] if len(formatted_strategies) > 2 else {}
        }

        return {
            "agent": self.name,
            "icon": self.icon,
            "steps": steps,
            "codeExample": code_example,
            "codeSnippet": code_example,
            "estimatedEffort": effort,
            "riskLevel": risk,
            "historicalFixes": historical_fixes,
            "matchedPattern": matched_key,
            "strategies": formatted_strategies,
            "strategyMap": strategy_dict,
            "summary": f"Recommended fix approach: {effort} estimated effort, {risk} risk.",
            "details": {
                "steps": [f"{i+1}. {s}" for i, s in enumerate(steps)],
                "codeExample": code_example,
                "estimatedEffort": effort,
                "riskLevel": risk,
                "historicalFixes": [f"📚 {h['bugId']}: {h['resolution']}" for h in historical_fixes] if historical_fixes else ['No direct historical fix matches found']
            }
        }



    def _match_fix_pattern(self, log_res: Dict[str, Any], root_cause_res: Dict[str, Any], text: str):
        if log_res and log_res.get("errorTypeInfo"):
            cat = log_res["errorTypeInfo"].get("category")
            if cat in self.fix_patterns:
                return self.fix_patterns[cat], cat

        mapping = {
            'Null Reference Access': 'Null Reference',
            'Memory Exhaustion': 'Resource Exhaustion',
            'Concurrency Issue': 'Concurrency',
            'Security Vulnerability': 'Security',
            'Data Integrity Issue': 'SQL Error',
            'API/Integration Error': 'Timeout',
            'UI/Rendering Issue': 'Type Error',
            'Configuration Error': 'IO Error'
        }

        if root_cause_res and root_cause_res.get("matchedPatterns"):
            for pname in root_cause_res["matchedPatterns"]:
                fkey = mapping.get(pname)
                if fkey and fkey in self.fix_patterns:
                    return self.fix_patterns[fkey], fkey

        for k, pat in self.fix_patterns.items():
            if k.lower() in text:
                return pat, k

        default_fix = {
            'strategies': [
                {
                    'name': 'Quick Hotfix',
                    'approach': 'Apply a targeted fix at the failure point.',
                    'steps': [
                        'Review the error message and stack trace carefully',
                        'Add error handling around the failure point',
                    ],
                    'codeExample': None,
                    'pros': ['Fastest resolution', 'Minimal change'],
                    'cons': ['May not address root cause'],
                    'effort': '30 min - 1 hour',
                    'risk': 'Low'
                },
                {
                    'name': 'Defensive Refactor',
                    'approach': 'Reproduce, diagnose, and apply a proper fix with tests.',
                    'steps': [
                        'Reproduce the issue in a development environment',
                        'Add logging around the failure point for more context',
                        'Implement a fix and write unit tests to verify',
                        'Test in staging before deploying to production',
                    ],
                    'codeExample': None,
                    'pros': ['Thorough fix', 'Includes verification'],
                    'cons': ['More time needed'],
                    'effort': '2-4 hours',
                    'risk': 'Medium'
                },
                {
                    'name': 'Architectural Redesign',
                    'approach': 'Refactor the affected module with proper patterns and testing.',
                    'steps': [
                        'Analyze the module architecture for design weaknesses',
                        'Refactor with appropriate design patterns',
                        'Add comprehensive integration test coverage',
                        'Update documentation and coding guidelines',
                    ],
                    'codeExample': None,
                    'pros': ['Long-term stability', 'Improved maintainability'],
                    'cons': ['Significant effort', 'Requires planning'],
                    'effort': '1-3 days',
                    'risk': 'High'
                }
            ]
        }
        return default_fix, "General"

    def _get_historical_fixes(self, dup_res: Dict[str, Any]) -> List[Dict[str, Any]]:
        if not dup_res or not dup_res.get("duplicates"):
            return []

        out = []
        for d in dup_res["duplicates"]:
            res = d.get("resolution")
            if res and res != "Not documented":
                out.append({
                    "bugId": d.get("id"),
                    "title": d.get("title"),
                    "resolution": res,
                    "similarity": d.get("similarity")
                })
        return out[:3]
