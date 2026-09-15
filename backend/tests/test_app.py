import unittest
from fastapi.testclient import TestClient
from backend.app.main import app
from backend.app.database import SessionLocal
from backend.app.seed import seed_database

class TestSmartBugAnalyzer(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        db = SessionLocal()
        seed_database(db, force=True)
        db.close()
        cls.client = TestClient(app)

    def test_health_check(self):
        response = self.client.get("/api/health")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")

    def test_get_bugs(self):
        response = self.client.get("/api/v1/bugs")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreaterEqual(len(data), 15)

    def test_get_stats(self):
        response = self.client.get("/api/v1/bugs/stats")
        self.assertEqual(response.status_code, 200)
        stats = response.json()
        self.assertGreaterEqual(stats["total"], 15)
        self.assertGreaterEqual(stats["resolved"], 15)

    def test_get_analytics(self):
        response = self.client.get("/api/v1/bugs/analytics")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertIn("categoryRisks", data)
        self.assertIn("antiPatterns", data)
        self.assertIn("teamRecommendations", data)
        self.assertGreaterEqual(len(data["categoryRisks"]), 1)

    def test_get_categories(self):
        response = self.client.get("/api/v1/bugs/categories")
        self.assertEqual(response.status_code, 200)
        cats = response.json()
        self.assertIn("All", cats)
        self.assertIn("Backend", cats)

    def test_analyze_bug_pipeline(self):
        bug_data = {
            "title": "NullPointerException in OrderService.createOrder()",
            "description": "Order creation fails with null reference exception when user cart is empty.",
            "stackTrace": "java.lang.NullPointerException\n  at com.app.OrderService.createOrder(OrderService.java:45)",
            "category": "Backend"
        }
        response = self.client.post("/api/v1/bugs/analyze", json=bug_data)
        self.assertEqual(response.status_code, 201)
        res = response.json()
        self.assertTrue(res["id"].startswith("BUG-"))
        self.assertIsNotNone(res["analysisResults"])
        self.assertIn("triage", res["analysisResults"])
        self.assertIn("logAnalysis", res["analysisResults"])
        self.assertIn("rootCause", res["analysisResults"])
        self.assertIn("duplicate", res["analysisResults"])
        self.assertIn("remediation", res["analysisResults"])

        # Feature assertions for 10-step Bug Fixer
        log_an = res["analysisResults"]["logAnalysis"]
        self.assertEqual(log_an["exceptionType"], "NullPointerException")
        self.assertEqual(log_an["programmingLanguage"], "java")
        self.assertEqual(log_an["methodName"], "createOrder")
        self.assertEqual(log_an["lineNumber"], 45)

        # RAG Knowledge Retrieval assertion
        self.assertIn("ragRetrieval", res["analysisResults"])
        rag_res = res["analysisResults"]["ragRetrieval"]
        self.assertIn("items", rag_res)
        self.assertIn("retrievedCount", rag_res)

        # Feature 2: Multi-Fix Strategy Matrix
        remediation = res["analysisResults"]["remediation"]
        self.assertIn("strategies", remediation)
        self.assertEqual(len(remediation["strategies"]), 3)
        strategy_names = [s["name"] for s in remediation["strategies"]]
        self.assertIn("Quick Hotfix", strategy_names)
        self.assertIn("Defensive Refactor", strategy_names)
        self.assertIn("Architectural Redesign", strategy_names)
        for s in remediation["strategies"]:
            self.assertIn("pros", s)
            self.assertIn("cons", s)
            self.assertIn("effort", s)
            self.assertIn("risk", s)

        # Feature 5: Beginner Learning Mode (beginnerExplanation)
        root_cause = res["analysisResults"]["rootCause"]
        self.assertIn("beginnerExplanation", root_cause)
        beginner = root_cause["beginnerExplanation"]
        self.assertIn("analogy", beginner)
        self.assertIn("simplifiedSummary", beginner)
        self.assertIn("keyConcepts", beginner)

    def test_resolve_bug(self):
        res_data = {
            "rootCause": "Verified null check missing in UserService",
            "resolution": "Applied null check and unit test"
        }
        response = self.client.post("/api/v1/bugs/BUG-001/resolve", json=res_data)
        self.assertEqual(response.status_code, 200)
        bug = response.json()
        self.assertEqual(bug["status"], "Resolved")
        self.assertEqual(bug["rootCause"], "Verified null check missing in UserService")

    def test_chat_mentor(self):
        # 1. Send chat message
        msg_data = {"message": "Why did this NullPointerException occur?"}
        response = self.client.post("/api/v1/bugs/BUG-001/chat", json=msg_data)
        self.assertEqual(response.status_code, 201)
        res = response.json()
        self.assertEqual(res["sender"], "advisor")
        self.assertIn("Diagnostic Explanation", res["message"])

        # 2. Get chat history
        hist_response = self.client.get("/api/v1/bugs/BUG-001/chat")
        self.assertEqual(hist_response.status_code, 200)
        messages = hist_response.json()
        self.assertGreaterEqual(len(messages), 2)
        self.assertEqual(messages[0]["sender"], "user")
        self.assertEqual(messages[1]["sender"], "advisor")

    def test_clarification_questions(self):
        # 1. Low context bug (no severity keywords, no stack trace) -> confidence = 50 -> triggers clarification questions
        low_context_bug = {
            "title": "Unknown behavior in widget",
            "description": "Something feels odd",
            "category": "Frontend"
        }
        res1 = self.client.post("/api/v1/bugs/analyze", json=low_context_bug)
        self.assertEqual(res1.status_code, 201)
        data1 = res1.json()
        triage1 = data1["analysisResults"]["triage"]
        self.assertLess(triage1["confidence"], 70)
        self.assertGreaterEqual(len(triage1["clarificationQuestions"]), 1)

        # 2. Refine with clarifications -> boosts confidence score
        refined_bug = {
            "title": "Unknown behavior in widget",
            "description": "Something feels odd",
            "category": "Frontend",
            "clarifications": {
                "q_env": "Yes, live production",
                "q_state": "Active session / valid payload"
            }
        }
        res2 = self.client.post("/api/v1/bugs/analyze", json=refined_bug)
        self.assertEqual(res2.status_code, 201)
        data2 = res2.json()
        triage2 = data2["analysisResults"]["triage"]
        self.assertGreater(triage2["confidence"], triage1["confidence"])
        self.assertEqual(len(triage2["clarificationQuestions"]), 0)

    def test_code_doctor(self):
        vulnerable_code = {
            "code": "let query = \"SELECT * FROM users WHERE name = '\" + userInput + \"'\";\neval(\"grantAdmin()\");"
        }
        response = self.client.post("/api/v1/code-review", json=vulnerable_code)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["agent"], "Code Review Agent")
        self.assertLess(data["score"], 100)
        self.assertGreaterEqual(data["totalIssues"], 2)
        rule_ids = [f["ruleId"] for f in data["findings"]]
        self.assertIn("SEC-001", rule_ids)
        self.assertIn("SEC-004", rule_ids)

    # ── 5 New Features Integration Tests ──

    def test_ai_auto_fix_endpoint(self):
        bug_data = {
            "title": "NullPointerException in UserService.getProfile()",
            "stackTrace": "java.lang.NullPointerException\n  at UserService.getProfile(UserService.java:142)",
            "category": "Backend"
        }
        response = self.client.post("/api/v1/bugs/auto-fix", json=bug_data)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["agent"], "AI Auto-Fix Agent")
        self.assertIn("originalCode", data)
        self.assertIn("fixedCode", data)
        self.assertIn("diff", data)
        self.assertIn("explanation", data)

    def test_auto_test_generator_endpoint(self):
        bug_data = {
            "title": "KeyError in user role parsing",
            "stackTrace": "KeyError: 'roles'\n  at service.py line 30",
            "language": "python"
        }
        response = self.client.post("/api/v1/bugs/generate-tests", json=bug_data)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["agent"], "Auto Test Generator Agent")
        self.assertIn("testCode", data)
        self.assertIn("testFramework", data)
        self.assertGreaterEqual(data["testCount"], 1)

    def test_fix_verification_endpoint(self):
        fix_data = {
            "fixedCode": "def get_role(user):\n    return user.get('roles', ['Guest'])[0]\n",
            "language": "python"
        }
        response = self.client.post("/api/v1/bugs/verify-fix", json=fix_data)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["agent"], "Fix Verification Agent")
        self.assertEqual(data["status"], "PASS")
        self.assertEqual(data["score"], 100)
        self.assertGreaterEqual(len(data["checks"]), 3)

    def test_security_scanner_endpoint(self):
        vulnerable_code = {
            "code": "query = 'SELECT * FROM users WHERE name = ' + user_input\nsecret = 'AWS_SECRET_KEY_123456'\neval('execute_command()')"
        }
        response = self.client.post("/api/v1/bugs/security-scan", json=vulnerable_code)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["agent"], "Security Scanner Agent")
        self.assertEqual(data["riskLevel"], "Critical")
        self.assertGreaterEqual(data["totalVulnerabilities"], 2)
        categories = [f["category"] for f in data["findings"]]
        self.assertIn("SQL Injection", categories)
        self.assertIn("Unsafe APIs", categories)

    def test_bug_priority_score_endpoint(self):
        priority_req = {
            "severity": "Critical",
            "category": "Security",
            "title": "SQL Injection in live production authentication service",
            "description": "Production database outage caused by breach attempt"
        }
        response = self.client.post("/api/v1/bugs/priority-score", json=priority_req)
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertGreaterEqual(data["score"], 80)
        self.assertEqual(data["level"], "Critical")
        self.assertIn("breakdown", data)
        self.assertIn("severity", data["breakdown"])

    def test_pipeline_includes_all_5_features(self):
        bug_report = {
            "title": "Critical SQL Injection in UserService",
            "description": "SELECT * FROM users WHERE name = ' + name",
            "stackTrace": "java.lang.NullPointerException at UserService.java:142",
            "category": "Backend"
        }
        response = self.client.post("/api/v1/bugs/analyze", json=bug_report)
        self.assertEqual(response.status_code, 201)
        res = response.json()
        analysis = res["analysisResults"]

        # Feature 1: AI Auto-Fix
        self.assertIn("autoFix", analysis)
        self.assertIsNotNone(analysis["autoFix"]["fixedCode"])

        # Feature 2: Auto Test Generator
        self.assertIn("testGenerator", analysis)
        self.assertIsNotNone(analysis["testGenerator"]["testCode"])

        # Feature 3: Fix Verification
        self.assertIn("fixVerification", analysis)
        self.assertEqual(analysis["fixVerification"]["status"], "PASS")

        # Feature 4: Security Scanner
        self.assertIn("securityScan", analysis)
        self.assertGreaterEqual(analysis["securityScan"]["totalVulnerabilities"], 1)

        # Feature 5: Bug Priority Score
        self.assertIn("priorityScore", analysis["triage"])
        self.assertGreaterEqual(analysis["triage"]["priorityScore"]["score"], 0)

if __name__ == "__main__":
    unittest.main()

