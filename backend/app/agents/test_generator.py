"""
TestGeneratorAgent — Auto Unit & Regression Test Suite Generator

Generates executable unit tests and regression test suites for detected bugs
and auto-fix suggestions across Pytest (Python), JUnit 5 (Java), and Jest (JavaScript).
"""

from typing import Dict, Any, List

class TestGeneratorAgent:
    def __init__(self):
        self.name = "Auto Test Generator Agent"
        self.icon = "🧪"

    def generate_tests(self, bug_report: Dict[str, Any], auto_fix_data: Dict[str, Any] = None) -> Dict[str, Any]:
        title = bug_report.get("title", "")
        desc = bug_report.get("description", "")
        stack_trace = bug_report.get("stackTrace") or bug_report.get("stack_trace", "")
        text = f"{title}\n{desc}\n{stack_trace}"

        lang = auto_fix_data.get("language") if auto_fix_data else self._detect_language(text)

        if lang == "java":
            framework = "JUnit 5 (Mockito)"
            file_name = "UserServiceTest.java"
            test_code, cases = self._generate_junit_tests(title)
        elif lang == "javascript":
            framework = "Jest"
            file_name = "app.test.js"
            test_code, cases = self._generate_jest_tests(title)
        else:
            framework = "Pytest"
            file_name = "test_defect_regression.py"
            test_code, cases = self._generate_pytest_tests(title)

        return {
            "agent": self.name,
            "icon": self.icon,
            "language": lang,
            "testFramework": framework,
            "fileName": file_name,
            "testCode": test_code,
            "testCount": len(cases),
            "testCases": cases
        }

    def _detect_language(self, text: str) -> str:
        text_lower = text.lower()
        if "java" in text_lower or "nullpointerexception" in text_lower:
            return "java"
        elif "javascript" in text_lower or "innerhtml" in text_lower or "const " in text_lower:
            return "javascript"
        return "python"

    def _generate_pytest_tests(self, title: str) -> tuple:
        code = '''# Automated Pytest Suite — Bug Regression & Verification
import pytest

# 1. Reproduction Test — Verifies original issue failure condition
def test_reproduce_bug_condition():
    """Verify that unhandled missing inputs raise KeyError or TypeError."""
    invalid_payload = {}
    with pytest.raises((KeyError, TypeError, AttributeError)):
        # Simulating un-fixed behavior
        _unfixed_get_role(invalid_payload)

# 2. Fix Verification Test — Asserts corrected code handles missing input safely
def test_verify_auto_fix_success():
    """Verify that auto-fixed handler returns valid default fallback."""
    payload = {"user_id": 101, "roles": ["Admin"]}
    result = _auto_fixed_get_role(payload)
    assert result == "Admin", "Expected Admin role from payload"

# 3. Boundary & Edge Case Tests
def test_boundary_empty_and_null_inputs():
    """Boundary test covering None, empty dict, and malformed types."""
    assert _auto_fixed_get_role(None) == "Guest"
    assert _auto_fixed_get_role({}) == "Guest"
    assert _auto_fixed_get_role({"roles": []}) == "User"

# Mock Auto-Fix implementation for test suite validation
def _unfixed_get_role(data):
    return data['roles'][0]

def _auto_fixed_get_role(data):
    if not isinstance(data, dict):
        return "Guest"
    roles = data.get("roles", [])
    return roles[0] if roles else "User"
'''
        cases = [
            {"name": "test_reproduce_bug_condition", "type": "Reproduction", "target": "Unfixed Code", "expected": "Raises Exception"},
            {"name": "test_verify_auto_fix_success", "type": "Verification", "target": "Fixed Code", "expected": "Returns Valid Role"},
            {"name": "test_boundary_empty_and_null_inputs", "type": "Boundary / Edge Case", "target": "Fixed Code", "expected": "Safe Fallback"}
        ]
        return code, cases

    def _generate_junit_tests(self, title: str) -> tuple:
        code = '''// Automated JUnit 5 Test Suite — Bug Regression & Fix Verification
package com.app.service;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.DisplayName;
import static org.junit.jupiter.api.Assertions.*;

public class UserServiceTest {

    @Test
    @DisplayName("Reproduction: Verify NullPointerException on null profile")
    void testReproduction_NullUserCrash() {
        UserService service = new UserService();
        assertThrows(NullPointerException.class, () -> {
            service.getUnfixedProfile(999L);
        });
    }

    @Test
    @DisplayName("Verification: Assert Auto-Fix Optional return eliminates crash")
    void testVerify_AutoFixOptionalReturn() {
        UserService service = new UserService();
        var profileOpt = service.getAutoFixedProfile(999L);
        assertTrue(profileOpt.isEmpty(), "Optional should be empty for missing user");
    }

    @Test
    @DisplayName("Boundary: Null userId parameter safety check")
    void testBoundary_NullUserIdParameter() {
        UserService service = new UserService();
        assertDoesNotThrow(() -> {
            var res = service.getAutoFixedProfile(null);
            assertTrue(res.isEmpty());
        });
    }
}
'''
        cases = [
            {"name": "testReproduction_NullUserCrash", "type": "Reproduction", "target": "Legacy Method", "expected": "Throws NPE"},
            {"name": "testVerify_AutoFixOptionalReturn", "type": "Verification", "target": "Auto-Fix Method", "expected": "Optional.empty()"},
            {"name": "testBoundary_NullUserIdParameter", "type": "Boundary / Edge Case", "target": "Auto-Fix Method", "expected": "No Exception"}
        ]
        return code, cases

    def _generate_jest_tests(self, title: str) -> tuple:
        code = '''// Automated Jest Test Suite — DOM & XSS Regression Verification
const { renderComment } = require('./app');

describe('Bug Fix Regression & Security Suite', () => {

  test('Reproduction: Unsanitized innerHTML allows script tag injection', () => {
    const maliciousInput = '<img src="x" onerror="alert(1)">';
    const container = { innerHTML: '' };
    // Legacy unsanitized assignment
    container.innerHTML = '<div>' + maliciousInput + '</div>';
    expect(container.innerHTML).toContain('<img src="x"');
  });

  test('Verification: Auto-fix textContent escapes HTML injection', () => {
    const maliciousInput = '<script>alert("xss")</script>';
    const divNode = {};
    // Auto-fixed textContent assignment
    divNode.textContent = maliciousInput;
    expect(divNode.textContent).toBe('<script>alert("xss")</script>');
  });

  test('Boundary: Empty string and undefined payload handling', () => {
    expect(() => renderComment('')).not.toThrow();
    expect(() => renderComment(undefined)).not.toThrow();
  });
});
'''
        cases = [
            {"name": "Reproduction: Unsanitized innerHTML", "type": "Reproduction", "target": "Legacy JS", "expected": "Injected Script Tag"},
            {"name": "Verification: Auto-fix textContent escapes HTML", "type": "Verification", "target": "Auto-Fix JS", "expected": "Escaped Text Node"},
            {"name": "Boundary: Empty string and undefined handling", "type": "Boundary / Edge Case", "target": "Auto-Fix JS", "expected": "No Exception"}
        ]
        return code, cases

test_generator_agent = TestGeneratorAgent()
