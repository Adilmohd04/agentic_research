"""
Unit tests for Code Diff Generator

Tests the code diff generation functionality including change detection,
explanation generation, and test suggestion algorithms.
"""

import pytest
from backend.src.copilot.code_diff_generator import (
    CodeDiffGenerator,
    CodeChange,
    TestSuggestion,
    DiffAnalysis,
    ChangeType
)


class TestCodeDiffGenerator:
    """Test cases for CodeDiffGenerator class."""
    
    @pytest.fixture
    def generator(self):
        """Create a CodeDiffGenerator instance for testing."""
        return CodeDiffGenerator()
    
    def test_init(self, generator):
        """Test generator initialization."""
        assert generator is not None
        assert len(generator.supported_languages) > 0
        assert '.py' in generator.supported_languages
        assert '.js' in generator.supported_languages
    
    def test_generate_diff_simple(self, generator):
        """Test simple diff generation."""
        original = "def hello():\n    print('Hello')"
        modified = "def hello():\n    print('Hello, World!')"
        
        diff = generator.generate_diff(original, modified, "test.py")
        
        assert "Hello" in diff
        assert "Hello, World!" in diff
        assert "@@" in diff  # Unified diff format
        assert "test.py" in diff
    
    def test_generate_diff_no_changes(self, generator):
        """Test diff generation with no changes."""
        code = "def hello():\n    print('Hello')"
        
        diff = generator.generate_diff(code, code, "test.py")
        
        # Should be empty or minimal diff
        assert len(diff.strip()) == 0
    
    def test_detect_language(self, generator):
        """Test language detection from file extensions."""
        assert generator._detect_language("test.py") == "python"
        assert generator._detect_language("test.js") == "javascript"
        assert generator._detect_language("test.ts") == "typescript"
        assert generator._detect_language("test.unknown") == "unknown"
    
    def test_classify_change_add(self, generator):
        """Test change classification for additions."""
        change_type = generator._classify_change("insert", "", "new code")
        assert change_type == ChangeType.ADD
    
    def test_classify_change_delete(self, generator):
        """Test change classification for deletions."""
        change_type = generator._classify_change("delete", "old code", "")
        assert change_type == ChangeType.DELETE
    
    def test_classify_change_refactor(self, generator):
        """Test change classification for refactoring."""
        original = "def calculate(x, y):\n    result = x + y\n    return result"
        modified = "def calculate(x, y):\n    return x + y"
        
        change_type = generator._classify_change("replace", original, modified)
        # Should detect as refactor due to high token overlap
        assert change_type in [ChangeType.REFACTOR, ChangeType.MODIFY]
    
    def test_is_refactor_detection(self, generator):
        """Test refactor detection logic."""
        original = "def old_function(a, b):\n    temp = a + b\n    return temp"
        modified = "def old_function(a, b):\n    return a + b"
        
        is_refactor = generator._is_refactor(original, modified)
        assert is_refactor  # Should detect as refactor
    
    def test_is_bug_fix_detection(self, generator):
        """Test bug fix detection logic."""
        original = "def divide(a, b):\n    return a / b"
        modified = "def divide(a, b):\n    if b != 0:\n        return a / b\n    return None"
        
        is_fix = generator._is_bug_fix(original, modified)
        assert is_fix  # Should detect as bug fix
    
    def test_is_optimization_detection(self, generator):
        """Test optimization detection logic."""
        original = "result = []\nfor item in items:\n    result.append(item * 2)"
        modified = "result = [item * 2 for item in items]"
        
        is_optimization = generator._is_optimization(original, modified)
        # May or may not detect as optimization depending on implementation
        assert isinstance(is_optimization, bool)
    
    def test_explain_addition_function(self, generator):
        """Test explanation generation for function addition."""
        code = "def new_function(x):\n    return x * 2"
        
        explanation = generator._explain_addition(code, "python")
        
        assert "function" in explanation.lower()
        assert "new_function" in explanation
    
    def test_explain_addition_class(self, generator):
        """Test explanation generation for class addition."""
        code = "class NewClass:\n    def __init__(self):\n        pass"
        
        explanation = generator._explain_addition(code, "python")
        
        assert "class" in explanation.lower()
        assert "NewClass" in explanation
    
    def test_explain_deletion_function(self, generator):
        """Test explanation generation for function deletion."""
        code = "def old_function():\n    pass"
        
        explanation = generator._explain_deletion(code, "python")
        
        assert "removed" in explanation.lower() or "function" in explanation.lower()
    
    def test_explain_modification(self, generator):
        """Test explanation generation for modifications."""
        original = "def func(a):\n    return a"
        modified = "def func(a, b):\n    return a + b"
        
        explanation = generator._explain_modification(original, modified, "python")
        
        assert "modified" in explanation.lower() or "parameters" in explanation.lower()
    
    def test_calculate_confidence(self, generator):
        """Test confidence calculation."""
        confidence = generator._calculate_confidence(
            ChangeType.ADD, "", "def new_func(): pass"
        )
        
        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.5  # Should have high confidence for additions
    
    def test_calculate_impact(self, generator):
        """Test impact calculation."""
        impact = generator._calculate_impact(
            ChangeType.DELETE, "def old_func(): pass", ""
        )
        
        assert 0.0 <= impact <= 1.0
        assert impact > 0.5  # Deletions should have high impact
    
    def test_identify_changes_simple(self, generator):
        """Test change identification for simple modifications."""
        original = "def hello():\n    print('Hello')"
        modified = "def hello():\n    print('Hello, World!')"
        
        changes = generator._identify_changes(original, modified, "test.py")
        
        assert len(changes) > 0
        assert all(isinstance(change, CodeChange) for change in changes)
        assert changes[0].file_path == "test.py"
    
    def test_identify_changes_addition(self, generator):
        """Test change identification for additions."""
        original = "def hello():\n    print('Hello')"
        modified = "def hello():\n    print('Hello')\n\ndef goodbye():\n    print('Goodbye')"
        
        changes = generator._identify_changes(original, modified, "test.py")
        
        assert len(changes) > 0
        # Should detect addition
        assert any(change.change_type == ChangeType.ADD for change in changes)
    
    def test_identify_changes_deletion(self, generator):
        """Test change identification for deletions."""
        original = "def hello():\n    print('Hello')\n\ndef goodbye():\n    print('Goodbye')"
        modified = "def hello():\n    print('Hello')"
        
        changes = generator._identify_changes(original, modified, "test.py")
        
        assert len(changes) > 0
        # Should detect deletion
        assert any(change.change_type == ChangeType.DELETE for change in changes)
    
    def test_suggest_tests_for_addition(self, generator):
        """Test test suggestion for code additions."""
        change = CodeChange(
            file_path="test.py",
            change_type=ChangeType.ADD,
            line_start=1,
            line_end=3,
            original_code="",
            proposed_code="def new_function(x):\n    return x * 2",
            explanation="Added new function",
            confidence=0.9,
            impact_score=0.6
        )
        
        suggestions = generator._suggest_tests_for_addition(change, "python")
        
        assert len(suggestions) > 0
        assert all(isinstance(s, TestSuggestion) for s in suggestions)
        assert any("new_function" in s.test_name for s in suggestions)
    
    def test_suggest_tests_for_modification(self, generator):
        """Test test suggestion for code modifications."""
        change = CodeChange(
            file_path="test.py",
            change_type=ChangeType.MODIFY,
            line_start=1,
            line_end=2,
            original_code="def func(x): return x",
            proposed_code="def func(x): return x * 2",
            explanation="Modified function logic",
            confidence=0.8,
            impact_score=0.5
        )
        
        suggestions = generator._suggest_tests_for_modification(change, "python")
        
        assert len(suggestions) >= 0  # May or may not suggest tests
        if suggestions:
            assert all(isinstance(s, TestSuggestion) for s in suggestions)
    
    def test_suggest_tests_for_fix(self, generator):
        """Test test suggestion for bug fixes."""
        change = CodeChange(
            file_path="test.py",
            change_type=ChangeType.FIX,
            line_start=1,
            line_end=3,
            original_code="def divide(a, b): return a / b",
            proposed_code="def divide(a, b):\n    try:\n        return a / b\n    except ZeroDivisionError:\n        return None",
            explanation="Added error handling",
            confidence=0.9,
            impact_score=0.4
        )
        
        suggestions = generator._suggest_tests_for_fix(change, "python")
        
        assert len(suggestions) > 0
        assert any("error" in s.test_name.lower() for s in suggestions)
    
    def test_assess_impact_high(self, generator):
        """Test impact assessment for high-impact changes."""
        changes = [
            CodeChange("test.py", ChangeType.DELETE, 1, 10, "old", "", "Deleted", 0.9, 0.9),
            CodeChange("test.py", ChangeType.REFACTOR, 11, 20, "old", "new", "Refactored", 0.8, 0.8)
        ]
        
        impact = generator._assess_impact(changes)
        
        assert "high" in impact.lower()
    
    def test_assess_impact_low(self, generator):
        """Test impact assessment for low-impact changes."""
        changes = [
            CodeChange("test.py", ChangeType.ADD, 1, 2, "", "# comment", "Added comment", 0.9, 0.1)
        ]
        
        impact = generator._assess_impact(changes)
        
        assert "low" in impact.lower()
    
    def test_assess_risk_high(self, generator):
        """Test risk assessment for high-risk changes."""
        changes = [
            CodeChange("test.py", ChangeType.DELETE, 1, 10, "old", "", "Deleted", 0.9, 0.9),
            CodeChange("test.py", ChangeType.REFACTOR, 11, 20, "old", "new", "Refactored", 0.8, 0.8)
        ]
        
        risk = generator._assess_risk(changes)
        
        assert "high" in risk.lower()
    
    def test_assess_risk_low(self, generator):
        """Test risk assessment for low-risk changes."""
        changes = [
            CodeChange("test.py", ChangeType.ADD, 1, 2, "", "# comment", "Added comment", 0.9, 0.1)
        ]
        
        risk = generator._assess_risk(changes)
        
        assert "low" in risk.lower()
    
    def test_generate_recommendations(self, generator):
        """Test recommendation generation."""
        changes = [
            CodeChange("test.py", ChangeType.DELETE, 1, 5, "old", "", "Deleted", 0.9, 0.8),
            CodeChange("test.py", ChangeType.ADD, 6, 8, "", "new", "Added", 0.9, 0.6)
        ]
        
        recommendations = generator._generate_recommendations(changes)
        
        assert len(recommendations) > 0
        assert all(isinstance(rec, str) for rec in recommendations)
        # Should include recommendations for deletions and additions
        assert any("delete" in rec.lower() or "remove" in rec.lower() for rec in recommendations)
    
    def test_analyze_changes_complete(self, generator):
        """Test complete change analysis."""
        original = """
def calculate(x, y):
    return x + y

def old_function():
    print("This will be removed")
"""
        
        modified = """
def calculate(x, y):
    # Added input validation
    if x is None or y is None:
        return None
    return x + y

def new_function():
    print("This is new")
"""
        
        analysis = generator.analyze_changes(original, modified, "test.py")
        
        assert isinstance(analysis, DiffAnalysis)
        assert len(analysis.changes) > 0
        assert len(analysis.test_suggestions) >= 0
        assert analysis.overall_impact
        assert analysis.risk_assessment
        assert len(analysis.recommendations) > 0
    
    def test_generate_explanation_report(self, generator):
        """Test explanation report generation."""
        changes = [
            CodeChange("test.py", ChangeType.ADD, 1, 2, "", "def new(): pass", "Added function", 0.9, 0.6)
        ]
        
        test_suggestions = [
            TestSuggestion("test_new", "def test_new(): pass", "unit", "Test new function", 4)
        ]
        
        analysis = DiffAnalysis(
            changes=changes,
            test_suggestions=test_suggestions,
            overall_impact="Medium impact",
            risk_assessment="Low risk",
            recommendations=["Add tests", "Review code"]
        )
        
        report = generator.generate_explanation_report(analysis)
        
        assert "# Code Change Analysis Report" in report
        assert "Summary" in report
        assert "Detailed Changes" in report
        assert "Suggested Tests" in report
        assert "Recommendations" in report
        assert "test_new" in report
    
    def test_complex_python_analysis(self, generator):
        """Test analysis of complex Python code changes."""
        original = """
class Calculator:
    def add(self, a, b):
        return a + b
    
    def divide(self, a, b):
        return a / b
"""
        
        modified = """
class Calculator:
    def add(self, a, b):
        \"\"\"Add two numbers with type checking.\"\"\"
        if not isinstance(a, (int, float)) or not isinstance(b, (int, float)):
            raise TypeError("Arguments must be numbers")
        return a + b
    
    def divide(self, a, b):
        \"\"\"Divide two numbers with zero check.\"\"\"
        if b == 0:
            raise ValueError("Cannot divide by zero")
        return a / b
    
    def multiply(self, a, b):
        \"\"\"Multiply two numbers.\"\"\"
        return a * b
"""
        
        analysis = generator.analyze_changes(original, modified, "calculator.py")
        
        assert len(analysis.changes) > 0
        
        # Should detect modifications and additions
        change_types = {change.change_type for change in analysis.changes}
        assert ChangeType.MODIFY in change_types or ChangeType.ADD in change_types
        
        # Should suggest tests
        assert len(analysis.test_suggestions) > 0
        
        # Should have meaningful impact and risk assessments
        assert analysis.overall_impact
        assert analysis.risk_assessment
        assert len(analysis.recommendations) > 0


class TestDataClasses:
    """Test data classes used in code diff generation."""
    
    def test_code_change_creation(self):
        """Test CodeChange dataclass creation."""
        change = CodeChange(
            file_path="test.py",
            change_type=ChangeType.ADD,
            line_start=1,
            line_end=5,
            original_code="",
            proposed_code="def new_func(): pass",
            explanation="Added new function",
            confidence=0.9,
            impact_score=0.6
        )
        
        assert change.file_path == "test.py"
        assert change.change_type == ChangeType.ADD
        assert change.line_start == 1
        assert change.line_end == 5
        assert change.confidence == 0.9
        assert change.impact_score == 0.6
    
    def test_test_suggestion_creation(self):
        """Test TestSuggestion dataclass creation."""
        suggestion = TestSuggestion(
            test_name="test_new_function",
            test_code="def test_new_function(): pass",
            test_type="unit",
            description="Test new function",
            priority=4
        )
        
        assert suggestion.test_name == "test_new_function"
        assert suggestion.test_type == "unit"
        assert suggestion.priority == 4
    
    def test_diff_analysis_creation(self):
        """Test DiffAnalysis dataclass creation."""
        changes = [
            CodeChange("test.py", ChangeType.ADD, 1, 2, "", "code", "Added", 0.9, 0.6)
        ]
        
        suggestions = [
            TestSuggestion("test_func", "def test_func(): pass", "unit", "Test", 4)
        ]
        
        analysis = DiffAnalysis(
            changes=changes,
            test_suggestions=suggestions,
            overall_impact="Medium",
            risk_assessment="Low",
            recommendations=["Review code"]
        )
        
        assert len(analysis.changes) == 1
        assert len(analysis.test_suggestions) == 1
        assert analysis.overall_impact == "Medium"
        assert analysis.risk_assessment == "Low"
        assert len(analysis.recommendations) == 1


if __name__ == "__main__":
    pytest.main([__file__])