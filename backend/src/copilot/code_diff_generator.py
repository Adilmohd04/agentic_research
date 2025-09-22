"""
Code Diff Generation System for Developer Copilot

This module provides comprehensive code diff generation capabilities including
proposing code changes, generating explanations, and suggesting tests.
"""

import ast
import difflib
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Any, Set
from dataclasses import dataclass, asdict
from enum import Enum
import logging

logger = logging.getLogger(__name__)

class ChangeType(Enum):
    """Types of code changes."""
    ADD = "add"
    MODIFY = "modify"
    DELETE = "delete"
    REFACTOR = "refactor"
    FIX = "fix"
    OPTIMIZE = "optimize"

@dataclass
class CodeChange:
    """Represents a single code change."""
    file_path: str
    change_type: ChangeType
    line_start: int
    line_end: int
    original_code: str
    proposed_code: str
    explanation: str
    confidence: float
    impact_score: float

@dataclass
class TestSuggestion:
    """Represents a suggested test case."""
    test_name: str
    test_code: str
    test_type: str  # 'unit', 'integration', 'edge_case'
    description: str
    priority: int  # 1-5, 5 being highest

@dataclass
class DiffAnalysis:
    """Analysis of code differences and suggestions."""
    changes: List[CodeChange]
    test_suggestions: List[TestSuggestion]
    overall_impact: str
    risk_assessment: str
    recommendations: List[str]

class CodeDiffGenerator:
    """Generates code diffs and explanations for proposed changes."""
    
    def __init__(self):
        """Initialize the code diff generator."""
        self.supported_languages = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'react',
            '.tsx': 'react-typescript',
            '.java': 'java',
            '.cpp': 'cpp',
            '.c': 'c',
            '.cs': 'csharp',
            '.go': 'go',
            '.rs': 'rust',
            '.php': 'php',
            '.rb': 'ruby'
        }
    
    def generate_diff(self, 
                     original_code: str, 
                     modified_code: str, 
                     file_path: str = "unknown",
                     context_lines: int = 3) -> str:
        """Generate a unified diff between original and modified code.
        
        Args:
            original_code: Original code content
            modified_code: Modified code content
            file_path: Path to the file being modified
            context_lines: Number of context lines to include
            
        Returns:
            Unified diff string
        """
        original_lines = original_code.splitlines(keepends=True)
        modified_lines = modified_code.splitlines(keepends=True)
        
        diff = difflib.unified_diff(
            original_lines,
            modified_lines,
            fromfile=f"a/{file_path}",
            tofile=f"b/{file_path}",
            n=context_lines
        )
        
        return ''.join(diff)
    
    def analyze_changes(self, 
                       original_code: str, 
                       modified_code: str, 
                       file_path: str) -> DiffAnalysis:
        """Analyze code changes and provide detailed insights.
        
        Args:
            original_code: Original code content
            modified_code: Modified code content
            file_path: Path to the file being modified
            
        Returns:
            DiffAnalysis object with detailed change analysis
        """
        # Generate individual changes
        changes = self._identify_changes(original_code, modified_code, file_path)
        
        # Generate test suggestions
        test_suggestions = self._suggest_tests(changes, file_path)
        
        # Assess overall impact
        overall_impact = self._assess_impact(changes)
        
        # Perform risk assessment
        risk_assessment = self._assess_risk(changes)
        
        # Generate recommendations
        recommendations = self._generate_recommendations(changes)
        
        return DiffAnalysis(
            changes=changes,
            test_suggestions=test_suggestions,
            overall_impact=overall_impact,
            risk_assessment=risk_assessment,
            recommendations=recommendations
        )
    
    def _identify_changes(self, 
                         original_code: str, 
                         modified_code: str, 
                         file_path: str) -> List[CodeChange]:
        """Identify individual code changes between versions.
        
        Args:
            original_code: Original code content
            modified_code: Modified code content
            file_path: Path to the file being modified
            
        Returns:
            List of CodeChange objects
        """
        changes = []
        original_lines = original_code.splitlines()
        modified_lines = modified_code.splitlines()
        
        # Use difflib to get detailed differences
        matcher = difflib.SequenceMatcher(None, original_lines, modified_lines)
        
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == 'equal':
                continue
            
            original_chunk = '\n'.join(original_lines[i1:i2])
            modified_chunk = '\n'.join(modified_lines[j1:j2])
            
            # Determine change type
            change_type = self._classify_change(tag, original_chunk, modified_chunk)
            
            # Generate explanation
            explanation = self._explain_change(
                change_type, original_chunk, modified_chunk, file_path
            )
            
            # Calculate confidence and impact
            confidence = self._calculate_confidence(change_type, original_chunk, modified_chunk)
            impact_score = self._calculate_impact(change_type, original_chunk, modified_chunk)
            
            change = CodeChange(
                file_path=file_path,
                change_type=change_type,
                line_start=i1 + 1,  # 1-based line numbers
                line_end=i2,
                original_code=original_chunk,
                proposed_code=modified_chunk,
                explanation=explanation,
                confidence=confidence,
                impact_score=impact_score
            )
            
            changes.append(change)
        
        return changes
    
    def _classify_change(self, tag: str, original: str, modified: str) -> ChangeType:
        """Classify the type of change based on content analysis.
        
        Args:
            tag: Diff operation tag ('replace', 'delete', 'insert')
            original: Original code chunk
            modified: Modified code chunk
            
        Returns:
            ChangeType enum value
        """
        if tag == 'delete':
            return ChangeType.DELETE
        elif tag == 'insert':
            return ChangeType.ADD
        elif tag == 'replace':
            # Analyze the nature of the replacement
            if self._is_refactor(original, modified):
                return ChangeType.REFACTOR
            elif self._is_bug_fix(original, modified):
                return ChangeType.FIX
            elif self._is_optimization(original, modified):
                return ChangeType.OPTIMIZE
            else:
                return ChangeType.MODIFY
        
        return ChangeType.MODIFY
    
    def _is_refactor(self, original: str, modified: str) -> bool:
        """Determine if change is a refactoring.
        
        Args:
            original: Original code
            modified: Modified code
            
        Returns:
            True if this appears to be a refactoring
        """
        # Look for patterns indicating refactoring
        refactor_patterns = [
            # Function extraction
            (r'def\s+\w+\(', r'def\s+\w+\(.*\):\s*\n\s*return\s+\w+\('),
            # Variable renaming
            (r'\b\w+\b', r'\b\w+\b'),
            # Code restructuring
            (r'if\s+.*:', r'if\s+.*:\s*\n.*else:'),
        ]
        
        # Simple heuristic: if structure changes but functionality seems similar
        original_tokens = set(re.findall(r'\b\w+\b', original))
        modified_tokens = set(re.findall(r'\b\w+\b', modified))
        
        # High token overlap suggests refactoring
        if original_tokens and modified_tokens:
            overlap = len(original_tokens & modified_tokens) / len(original_tokens | modified_tokens)
            return overlap > 0.7
        
        return False
    
    def _is_bug_fix(self, original: str, modified: str) -> bool:
        """Determine if change is a bug fix.
        
        Args:
            original: Original code
            modified: Modified code
            
        Returns:
            True if this appears to be a bug fix
        """
        # Look for common bug fix patterns
        bug_fix_patterns = [
            # Null/None checks
            (r'(?<!if\s)(?<!and\s)(?<!or\s)\w+\.\w+', r'if\s+\w+\s+is\s+not\s+None'),
            # Index bounds checking
            (r'\[\d+\]', r'if\s+len\(.*\)\s*>\s*\d+'),
            # Exception handling
            (r'(?<!try:)(?<!except)', r'try:.*except'),
            # Comparison fixes
            (r'==', r'is'),
            (r'!=', r'is not'),
        ]
        
        # Check for addition of error handling
        if 'try:' in modified and 'try:' not in original:
            return True
        if 'if' in modified and 'if' not in original and ('None' in modified or 'null' in modified):
            return True
        
        return False
    
    def _is_optimization(self, original: str, modified: str) -> bool:
        """Determine if change is an optimization.
        
        Args:
            original: Original code
            modified: Modified code
            
        Returns:
            True if this appears to be an optimization
        """
        # Look for optimization patterns
        optimization_patterns = [
            # List comprehensions
            (r'for\s+\w+\s+in.*:\s*\n\s*.*\.append', r'\[.*for.*in.*\]'),
            # Generator expressions
            (r'for\s+\w+\s+in.*:\s*\n\s*yield', r'\(.*for.*in.*\)'),
            # Caching
            (r'def\s+\w+\(', r'@lru_cache.*\ndef\s+\w+\('),
            # Algorithm improvements
            (r'for.*for.*in', r'for.*in.*if'),
        ]
        
        # Check for performance-related keywords
        perf_keywords = ['cache', 'optimize', 'efficient', 'faster', 'performance']
        modified_lower = modified.lower()
        
        return any(keyword in modified_lower for keyword in perf_keywords)
    
    def _explain_change(self, 
                       change_type: ChangeType, 
                       original: str, 
                       modified: str, 
                       file_path: str) -> str:
        """Generate human-readable explanation for a code change.
        
        Args:
            change_type: Type of change
            original: Original code
            modified: Modified code
            file_path: File path for context
            
        Returns:
            Human-readable explanation string
        """
        language = self._detect_language(file_path)
        
        if change_type == ChangeType.ADD:
            return self._explain_addition(modified, language)
        elif change_type == ChangeType.DELETE:
            return self._explain_deletion(original, language)
        elif change_type == ChangeType.MODIFY:
            return self._explain_modification(original, modified, language)
        elif change_type == ChangeType.REFACTOR:
            return self._explain_refactor(original, modified, language)
        elif change_type == ChangeType.FIX:
            return self._explain_fix(original, modified, language)
        elif change_type == ChangeType.OPTIMIZE:
            return self._explain_optimization(original, modified, language)
        
        return "Code change detected"
    
    def _explain_addition(self, code: str, language: str) -> str:
        """Explain code addition."""
        if language == 'python':
            if 'def ' in code:
                func_name = re.search(r'def\s+(\w+)', code)
                if func_name:
                    return f"Added new function '{func_name.group(1)}'"
            elif 'class ' in code:
                class_name = re.search(r'class\s+(\w+)', code)
                if class_name:
                    return f"Added new class '{class_name.group(1)}'"
            elif 'import ' in code:
                return "Added new import statement"
            elif 'if ' in code:
                return "Added conditional logic"
            elif 'try:' in code:
                return "Added error handling"
        
        return "Added new code block"
    
    def _explain_deletion(self, code: str, language: str) -> str:
        """Explain code deletion."""
        if language == 'python':
            if 'def ' in code:
                func_name = re.search(r'def\s+(\w+)', code)
                if func_name:
                    return f"Removed function '{func_name.group(1)}'"
            elif 'class ' in code:
                class_name = re.search(r'class\s+(\w+)', code)
                if class_name:
                    return f"Removed class '{class_name.group(1)}'"
            elif 'import ' in code:
                return "Removed import statement"
        
        return "Removed code block"
    
    def _explain_modification(self, original: str, modified: str, language: str) -> str:
        """Explain code modification."""
        if language == 'python':
            # Check for function signature changes
            orig_func = re.search(r'def\s+(\w+)\((.*?)\)', original)
            mod_func = re.search(r'def\s+(\w+)\((.*?)\)', modified)
            
            if orig_func and mod_func:
                if orig_func.group(1) == mod_func.group(1):
                    if orig_func.group(2) != mod_func.group(2):
                        return f"Modified parameters for function '{orig_func.group(1)}'"
                    else:
                        return f"Modified implementation of function '{orig_func.group(1)}'"
            
            # Check for variable changes
            orig_vars = set(re.findall(r'\b[a-zA-Z_]\w*\s*=', original))
            mod_vars = set(re.findall(r'\b[a-zA-Z_]\w*\s*=', modified))
            
            if orig_vars != mod_vars:
                return "Modified variable assignments"
        
        return "Modified code logic"
    
    def _explain_refactor(self, original: str, modified: str, language: str) -> str:
        """Explain refactoring changes."""
        return "Refactored code structure for better maintainability"
    
    def _explain_fix(self, original: str, modified: str, language: str) -> str:
        """Explain bug fix changes."""
        if 'try:' in modified and 'try:' not in original:
            return "Added error handling to prevent potential crashes"
        elif 'if' in modified and 'None' in modified:
            return "Added null/None check to prevent errors"
        elif '==' in original and 'is' in modified:
            return "Fixed comparison operator for better type safety"
        
        return "Fixed potential bug or error condition"
    
    def _explain_optimization(self, original: str, modified: str, language: str) -> str:
        """Explain optimization changes."""
        if '[' in modified and 'for' in modified and 'append' in original:
            return "Optimized loop with list comprehension for better performance"
        elif 'cache' in modified.lower():
            return "Added caching to improve performance"
        
        return "Optimized code for better performance"
    
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension."""
        suffix = Path(file_path).suffix.lower()
        return self.supported_languages.get(suffix, 'unknown')
    
    def _calculate_confidence(self, change_type: ChangeType, original: str, modified: str) -> float:
        """Calculate confidence score for the change analysis.
        
        Args:
            change_type: Type of change
            original: Original code
            modified: Modified code
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        base_confidence = 0.7
        
        # Adjust based on change type
        if change_type in [ChangeType.ADD, ChangeType.DELETE]:
            base_confidence = 0.9  # High confidence for clear additions/deletions
        elif change_type == ChangeType.FIX:
            base_confidence = 0.8  # High confidence for bug fixes
        elif change_type == ChangeType.REFACTOR:
            base_confidence = 0.6  # Lower confidence for refactoring detection
        
        # Adjust based on code complexity
        complexity_factor = min(len(original.split('\n')) + len(modified.split('\n')), 20) / 20
        confidence = base_confidence * (1 - complexity_factor * 0.2)
        
        return max(0.1, min(1.0, confidence))
    
    def _calculate_impact(self, change_type: ChangeType, original: str, modified: str) -> float:
        """Calculate impact score for the change.
        
        Args:
            change_type: Type of change
            original: Original code
            modified: Modified code
            
        Returns:
            Impact score between 0.0 and 1.0
        """
        base_impact = 0.5
        
        # Adjust based on change type
        if change_type == ChangeType.DELETE:
            base_impact = 0.8  # High impact for deletions
        elif change_type == ChangeType.REFACTOR:
            base_impact = 0.7  # High impact for refactoring
        elif change_type == ChangeType.ADD:
            base_impact = 0.6  # Medium-high impact for additions
        elif change_type == ChangeType.FIX:
            base_impact = 0.4  # Medium impact for fixes
        
        # Adjust based on code size
        size_factor = (len(original) + len(modified)) / 1000  # Normalize by 1000 chars
        impact = base_impact + min(size_factor * 0.3, 0.4)
        
        return max(0.1, min(1.0, impact))
    
    def _suggest_tests(self, changes: List[CodeChange], file_path: str) -> List[TestSuggestion]:
        """Suggest test cases based on code changes.
        
        Args:
            changes: List of code changes
            file_path: Path to the file being modified
            
        Returns:
            List of TestSuggestion objects
        """
        suggestions = []
        language = self._detect_language(file_path)
        
        for change in changes:
            if change.change_type == ChangeType.ADD:
                suggestions.extend(self._suggest_tests_for_addition(change, language))
            elif change.change_type == ChangeType.MODIFY:
                suggestions.extend(self._suggest_tests_for_modification(change, language))
            elif change.change_type == ChangeType.FIX:
                suggestions.extend(self._suggest_tests_for_fix(change, language))
        
        # Remove duplicates and sort by priority
        unique_suggestions = []
        seen_names = set()
        
        for suggestion in suggestions:
            if suggestion.test_name not in seen_names:
                unique_suggestions.append(suggestion)
                seen_names.add(suggestion.test_name)
        
        return sorted(unique_suggestions, key=lambda x: x.priority, reverse=True)
    
    def _suggest_tests_for_addition(self, change: CodeChange, language: str) -> List[TestSuggestion]:
        """Suggest tests for code additions."""
        suggestions = []
        
        if language == 'python':
            # Check for function additions
            func_match = re.search(r'def\s+(\w+)\((.*?)\)', change.proposed_code)
            if func_match:
                func_name = func_match.group(1)
                params = func_match.group(2)
                
                # Basic functionality test
                suggestions.append(TestSuggestion(
                    test_name=f"test_{func_name}_basic_functionality",
                    test_code=f"def test_{func_name}_basic_functionality():\n    # Test basic functionality of {func_name}\n    result = {func_name}()\n    assert result is not None",
                    test_type="unit",
                    description=f"Test basic functionality of {func_name}",
                    priority=4
                ))
                
                # Edge case test if parameters exist
                if params.strip():
                    suggestions.append(TestSuggestion(
                        test_name=f"test_{func_name}_edge_cases",
                        test_code=f"def test_{func_name}_edge_cases():\n    # Test edge cases for {func_name}\n    # TODO: Add specific edge case tests",
                        test_type="edge_case",
                        description=f"Test edge cases for {func_name}",
                        priority=3
                    ))
            
            # Check for class additions
            class_match = re.search(r'class\s+(\w+)', change.proposed_code)
            if class_match:
                class_name = class_match.group(1)
                
                suggestions.append(TestSuggestion(
                    test_name=f"test_{class_name.lower()}_initialization",
                    test_code=f"def test_{class_name.lower()}_initialization():\n    # Test {class_name} initialization\n    instance = {class_name}()\n    assert instance is not None",
                    test_type="unit",
                    description=f"Test {class_name} initialization",
                    priority=4
                ))
        
        return suggestions
    
    def _suggest_tests_for_modification(self, change: CodeChange, language: str) -> List[TestSuggestion]:
        """Suggest tests for code modifications."""
        suggestions = []
        
        if language == 'python':
            # Check for function modifications
            func_match = re.search(r'def\s+(\w+)', change.proposed_code)
            if func_match:
                func_name = func_match.group(1)
                
                suggestions.append(TestSuggestion(
                    test_name=f"test_{func_name}_after_modification",
                    test_code=f"def test_{func_name}_after_modification():\n    # Test {func_name} after recent modifications\n    # TODO: Add specific tests for modified behavior",
                    test_type="unit",
                    description=f"Test {func_name} after modifications",
                    priority=5
                ))
        
        return suggestions
    
    def _suggest_tests_for_fix(self, change: CodeChange, language: str) -> List[TestSuggestion]:
        """Suggest tests for bug fixes."""
        suggestions = []
        
        if 'try:' in change.proposed_code and 'try:' not in change.original_code:
            suggestions.append(TestSuggestion(
                test_name="test_error_handling",
                test_code="def test_error_handling():\n    # Test error handling for the fixed bug\n    # TODO: Add specific error condition tests",
                test_type="edge_case",
                description="Test error handling for the bug fix",
                priority=5
            ))
        
        if 'None' in change.proposed_code and 'if' in change.proposed_code:
            suggestions.append(TestSuggestion(
                test_name="test_null_input_handling",
                test_code="def test_null_input_handling():\n    # Test handling of null/None inputs\n    # TODO: Add specific null input tests",
                test_type="edge_case",
                description="Test handling of null/None inputs",
                priority=4
            ))
        
        return suggestions
    
    def _assess_impact(self, changes: List[CodeChange]) -> str:
        """Assess overall impact of changes."""
        if not changes:
            return "No changes detected"
        
        total_impact = sum(change.impact_score for change in changes)
        avg_impact = total_impact / len(changes)
        
        if avg_impact >= 0.8:
            return "High impact - significant changes that may affect system behavior"
        elif avg_impact >= 0.6:
            return "Medium-high impact - notable changes requiring careful review"
        elif avg_impact >= 0.4:
            return "Medium impact - moderate changes with some risk"
        elif avg_impact >= 0.2:
            return "Low-medium impact - minor changes with minimal risk"
        else:
            return "Low impact - small changes with negligible risk"
    
    def _assess_risk(self, changes: List[CodeChange]) -> str:
        """Assess risk level of changes."""
        high_risk_types = {ChangeType.DELETE, ChangeType.REFACTOR}
        medium_risk_types = {ChangeType.MODIFY, ChangeType.FIX}
        
        high_risk_count = sum(1 for change in changes if change.change_type in high_risk_types)
        medium_risk_count = sum(1 for change in changes if change.change_type in medium_risk_types)
        
        if high_risk_count > 0:
            return f"High risk - {high_risk_count} high-risk changes detected. Thorough testing recommended."
        elif medium_risk_count > 2:
            return f"Medium risk - {medium_risk_count} medium-risk changes. Review and testing advised."
        else:
            return "Low risk - changes appear safe with minimal testing required."
    
    def _generate_recommendations(self, changes: List[CodeChange]) -> List[str]:
        """Generate recommendations based on changes."""
        recommendations = []
        
        change_types = {change.change_type for change in changes}
        
        if ChangeType.DELETE in change_types:
            recommendations.append("Review deleted code to ensure no dependencies are broken")
            recommendations.append("Update documentation to reflect removed functionality")
        
        if ChangeType.REFACTOR in change_types:
            recommendations.append("Run comprehensive test suite to verify refactoring didn't break functionality")
            recommendations.append("Update any related documentation or comments")
        
        if ChangeType.FIX in change_types:
            recommendations.append("Add regression tests to prevent the bug from reoccurring")
            recommendations.append("Consider if similar bugs exist elsewhere in the codebase")
        
        if ChangeType.ADD in change_types:
            recommendations.append("Ensure new code follows project coding standards")
            recommendations.append("Add appropriate unit tests for new functionality")
        
        if len(changes) > 5:
            recommendations.append("Consider breaking large changes into smaller, reviewable chunks")
        
        # Add general recommendations
        recommendations.append("Review code changes with a colleague before merging")
        recommendations.append("Update version control commit message with clear description")
        
        return recommendations
    
    def generate_explanation_report(self, analysis: DiffAnalysis) -> str:
        """Generate a comprehensive explanation report.
        
        Args:
            analysis: DiffAnalysis object
            
        Returns:
            Formatted explanation report
        """
        report = []
        report.append("# Code Change Analysis Report\n")
        
        # Summary
        report.append(f"## Summary")
        report.append(f"- **Total Changes**: {len(analysis.changes)}")
        report.append(f"- **Overall Impact**: {analysis.overall_impact}")
        report.append(f"- **Risk Assessment**: {analysis.risk_assessment}")
        report.append("")
        
        # Detailed Changes
        report.append("## Detailed Changes\n")
        for i, change in enumerate(analysis.changes, 1):
            report.append(f"### Change {i}: {change.change_type.value.title()}")
            report.append(f"- **File**: {change.file_path}")
            report.append(f"- **Lines**: {change.line_start}-{change.line_end}")
            report.append(f"- **Explanation**: {change.explanation}")
            report.append(f"- **Confidence**: {change.confidence:.2f}")
            report.append(f"- **Impact Score**: {change.impact_score:.2f}")
            report.append("")
        
        # Test Suggestions
        if analysis.test_suggestions:
            report.append("## Suggested Tests\n")
            for suggestion in analysis.test_suggestions:
                report.append(f"### {suggestion.test_name}")
                report.append(f"- **Type**: {suggestion.test_type}")
                report.append(f"- **Priority**: {suggestion.priority}/5")
                report.append(f"- **Description**: {suggestion.description}")
                report.append("```python")
                report.append(suggestion.test_code)
                report.append("```")
                report.append("")
        
        # Recommendations
        if analysis.recommendations:
            report.append("## Recommendations\n")
            for rec in analysis.recommendations:
                report.append(f"- {rec}")
            report.append("")
        
        return '\n'.join(report)