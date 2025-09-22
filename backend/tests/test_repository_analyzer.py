"""
Unit tests for Repository Analyzer

Tests the repository analysis functionality including file traversal,
AST parsing, dependency analysis, and test coverage reporting.
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, mock_open

from backend.src.copilot.repository_analyzer import (
    RepositoryAnalyzer,
    FileInfo,
    DependencyInfo,
    CodeMetrics,
    TestInfo,
    RepositoryAnalysis
)


class TestRepositoryAnalyzer:
    """Test cases for RepositoryAnalyzer class."""
    
    @pytest.fixture
    def temp_repo(self):
        """Create a temporary repository for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            
            # Create sample files
            (repo_path / 'main.py').write_text('''
def hello_world():
    """Say hello to the world."""
    if True:
        print("Hello, World!")
    return "Hello"

class TestClass:
    def method(self):
        pass
''')
            
            (repo_path / 'requirements.txt').write_text('''
requests>=2.25.0
flask==2.0.1
pytest>=6.0.0
''')
            
            (repo_path / 'package.json').write_text(json.dumps({
                "name": "test-project",
                "dependencies": {
                    "react": "^17.0.0",
                    "axios": "^0.24.0"
                },
                "devDependencies": {
                    "jest": "^27.0.0"
                }
            }))
            
            (repo_path / 'test_main.py').write_text('''
import pytest
from main import hello_world

def test_hello_world():
    assert hello_world() == "Hello"

def test_another_function():
    assert True
''')
            
            # Create subdirectory
            sub_dir = repo_path / 'src'
            sub_dir.mkdir()
            (sub_dir / 'utils.js').write_text('''
function add(a, b) {
    return a + b;
}

function multiply(a, b) {
    if (a === 0 || b === 0) {
        return 0;
    }
    return a * b;
}
''')
            
            yield repo_path
    
    def test_init_valid_path(self, temp_repo):
        """Test analyzer initialization with valid path."""
        analyzer = RepositoryAnalyzer(str(temp_repo))
        assert analyzer.repo_path == temp_repo
    
    def test_init_invalid_path(self):
        """Test analyzer initialization with invalid path."""
        with pytest.raises(ValueError, match="Repository path does not exist"):
            RepositoryAnalyzer("/nonexistent/path")
    
    def test_detect_language(self, temp_repo):
        """Test language detection from file extensions."""
        analyzer = RepositoryAnalyzer(str(temp_repo))
        
        assert analyzer._detect_language(Path("test.py")) == "Python"
        assert analyzer._detect_language(Path("test.js")) == "JavaScript"
        assert analyzer._detect_language(Path("test.ts")) == "TypeScript"
        assert analyzer._detect_language(Path("test.unknown")) is None
    
    def test_count_lines(self, temp_repo):
        """Test line counting functionality."""
        analyzer = RepositoryAnalyzer(str(temp_repo))
        
        test_file = temp_repo / "test_lines.py"
        test_file.write_text("line1\nline2\nline3\n")
        
        lines = analyzer._count_lines(test_file)
        assert lines == 3
    
    def test_should_ignore(self, temp_repo):
        """Test file/directory ignore patterns."""
        analyzer = RepositoryAnalyzer(str(temp_repo))
        
        # Should ignore
        assert analyzer._should_ignore(".git")
        assert analyzer._should_ignore("node_modules")
        assert analyzer._should_ignore("__pycache__")
        assert analyzer._should_ignore(".hidden_file")
        
        # Should not ignore
        assert not analyzer._should_ignore("main.py")
        assert not analyzer._should_ignore("src")
        assert not analyzer._should_ignore(".gitignore")
    
    def test_calculate_python_complexity(self, temp_repo):
        """Test Python complexity calculation."""
        analyzer = RepositoryAnalyzer(str(temp_repo))
        
        main_file = temp_repo / "main.py"
        complexity = analyzer._calculate_python_complexity(main_file)
        
        # Should have complexity > 1 due to if statement and class
        assert complexity is not None
        assert complexity > 1
    
    def test_parse_dependency_spec(self, temp_repo):
        """Test dependency specification parsing."""
        analyzer = RepositoryAnalyzer(str(temp_repo))
        
        name, version = analyzer._parse_dependency_spec("requests>=2.25.0")
        assert name == "requests"
        assert version == "2.25.0"
        
        name, version = analyzer._parse_dependency_spec("flask==2.0.1")
        assert name == "flask"
        assert version == "2.0.1"
        
        name, version = analyzer._parse_dependency_spec("pytest")
        assert name == "pytest"
        assert version == "*"
    
    def test_parse_python_dependencies(self, temp_repo):
        """Test Python dependency parsing."""
        analyzer = RepositoryAnalyzer(str(temp_repo))
        
        req_file = temp_repo / "requirements.txt"
        deps = analyzer._parse_python_dependencies(req_file, "requirements.txt")
        
        assert len(deps) == 3
        
        dep_names = [dep.name for dep in deps]
        assert "requests" in dep_names
        assert "flask" in dep_names
        assert "pytest" in dep_names
        
        # Check specific dependency
        requests_dep = next(dep for dep in deps if dep.name == "requests")
        assert requests_dep.version == "2.25.0"
        assert requests_dep.type == "direct"
        assert requests_dep.source == "requirements.txt"
    
    def test_parse_nodejs_dependencies(self, temp_repo):
        """Test Node.js dependency parsing."""
        analyzer = RepositoryAnalyzer(str(temp_repo))
        
        package_file = temp_repo / "package.json"
        deps = analyzer._parse_nodejs_dependencies(package_file)
        
        assert len(deps) == 3
        
        dep_names = [dep.name for dep in deps]
        assert "react" in dep_names
        assert "axios" in dep_names
        assert "jest" in dep_names
        
        # Check dev dependency
        jest_dep = next(dep for dep in deps if dep.name == "jest")
        assert jest_dep.type == "dev"
        assert jest_dep.source == "package.json"
    
    def test_traverse_files(self, temp_repo):
        """Test file traversal functionality."""
        analyzer = RepositoryAnalyzer(str(temp_repo))
        
        files = analyzer._traverse_files()
        
        # Should find Python and JavaScript files
        file_paths = [f.path for f in files]
        assert "main.py" in file_paths
        assert "test_main.py" in file_paths
        assert str(Path("src") / "utils.js") in file_paths
        
        # Should not include package.json or requirements.txt in code files
        code_files = [f for f in files if f.language in ["Python", "JavaScript"]]
        assert len(code_files) >= 3
    
    def test_analyze_tests(self, temp_repo):
        """Test test analysis functionality."""
        analyzer = RepositoryAnalyzer(str(temp_repo))
        
        test_info = analyzer._analyze_tests()
        
        assert test_info.total_tests >= 2  # Should find test functions
        assert "test_main.py" in test_info.test_files
        assert test_info.coverage_percentage >= 0.0
    
    def test_build_structure(self, temp_repo):
        """Test repository structure building."""
        analyzer = RepositoryAnalyzer(str(temp_repo))
        
        structure = analyzer._build_structure()
        
        # Should have main files
        assert "main.py" in structure
        assert "test_main.py" in structure
        assert "requirements.txt" in structure
        assert "package.json" in structure
        
        # Should have src directory
        assert "src" in structure
        assert isinstance(structure["src"], dict)
        assert "utils.js" in structure["src"]
    
    def test_full_analysis(self, temp_repo):
        """Test complete repository analysis."""
        analyzer = RepositoryAnalyzer(str(temp_repo))
        
        analysis = analyzer.analyze()
        
        # Check basic properties
        assert isinstance(analysis, RepositoryAnalysis)
        assert analysis.total_files > 0
        assert analysis.total_lines > 0
        
        # Check languages
        assert "Python" in analysis.languages
        assert "JavaScript" in analysis.languages
        
        # Check files
        assert len(analysis.files) > 0
        python_files = [f for f in analysis.files if f.language == "Python"]
        assert len(python_files) >= 2
        
        # Check dependencies
        assert len(analysis.dependencies) > 0
        
        # Check metrics
        assert isinstance(analysis.metrics, CodeMetrics)
        assert analysis.metrics.lines_of_code > 0
        
        # Check test info
        assert isinstance(analysis.test_info, TestInfo)
        assert analysis.test_info.total_tests >= 0
        
        # Check structure
        assert isinstance(analysis.structure, dict)
        assert len(analysis.structure) > 0
    
    def test_get_file_analysis(self, temp_repo):
        """Test individual file analysis."""
        analyzer = RepositoryAnalyzer(str(temp_repo))
        
        file_info = analyzer.get_file_analysis("main.py")
        
        assert file_info is not None
        assert file_info.path == "main.py"
        assert file_info.language == "Python"
        assert file_info.lines > 0
        assert file_info.complexity is not None
        assert file_info.complexity > 1
    
    def test_get_file_analysis_nonexistent(self, temp_repo):
        """Test file analysis for nonexistent file."""
        analyzer = RepositoryAnalyzer(str(temp_repo))
        
        file_info = analyzer.get_file_analysis("nonexistent.py")
        assert file_info is None
    
    def test_get_dependency_tree(self, temp_repo):
        """Test dependency tree generation."""
        analyzer = RepositoryAnalyzer(str(temp_repo))
        
        tree = analyzer.get_dependency_tree()
        
        assert isinstance(tree, dict)
        assert "direct" in tree or "dev" in tree
    
    def test_export_analysis_json(self, temp_repo):
        """Test analysis export to JSON."""
        analyzer = RepositoryAnalyzer(str(temp_repo))
        
        output_file = temp_repo / "analysis.json"
        analyzer.export_analysis(str(output_file), "json")
        
        assert output_file.exists()
        
        # Verify JSON content
        with open(output_file, 'r') as f:
            data = json.load(f)
        
        assert "total_files" in data
        assert "languages" in data
        assert "files" in data
        assert "dependencies" in data
    
    @patch('subprocess.run')
    def test_analyze_tests_with_coverage(self, mock_run, temp_repo):
        """Test test analysis with coverage information."""
        # Mock coverage command output
        mock_run.return_value.returncode = 0
        mock_run.return_value.stdout = """
Name                 Stmts   Miss  Cover   Missing
--------------------------------------------------
main.py                 10      2    80%   15-16
test_main.py             5      0   100%
--------------------------------------------------
TOTAL                   15      2    87%
"""
        
        analyzer = RepositoryAnalyzer(str(temp_repo))
        test_info = analyzer._analyze_tests()
        
        assert test_info.coverage_percentage == 87.0
    
    def test_complex_python_file_analysis(self, temp_repo):
        """Test analysis of complex Python file with various constructs."""
        complex_file = temp_repo / "complex.py"
        complex_file.write_text('''
import os
import sys

class ComplexClass:
    """A complex class for testing."""
    
    def __init__(self, value):
        self.value = value
    
    def process(self, data):
        """Process data with complex logic."""
        if not data:
            return None
        
        result = []
        for item in data:
            if item > 0:
                result.append(item * 2)
            elif item < 0:
                result.append(abs(item))
            else:
                continue
        
        return result
    
    async def async_method(self):
        """Async method for testing."""
        try:
            await some_async_operation()
        except Exception as e:
            print(f"Error: {e}")
            return False
        return True

def standalone_function(x, y):
    """Standalone function with conditions."""
    if x and y:
        return x + y
    elif x or y:
        return x or y
    else:
        return 0

# This is a comment
# Another comment
''')
        
        analyzer = RepositoryAnalyzer(str(temp_repo))
        file_info = analyzer.get_file_analysis("complex.py")
        
        assert file_info is not None
        assert file_info.language == "Python"
        assert file_info.complexity is not None
        assert file_info.complexity > 5  # Should have high complexity
    
    def test_javascript_file_detection(self, temp_repo):
        """Test JavaScript file detection and basic analysis."""
        js_file = temp_repo / "app.js"
        js_file.write_text('''
function calculateTotal(items) {
    let total = 0;
    for (let item of items) {
        if (item.price > 0) {
            total += item.price;
        }
    }
    return total;
}

const processOrder = (order) => {
    if (!order || !order.items) {
        return null;
    }
    
    return {
        total: calculateTotal(order.items),
        itemCount: order.items.length
    };
};
''')
        
        analyzer = RepositoryAnalyzer(str(temp_repo))
        file_info = analyzer.get_file_analysis("app.js")
        
        assert file_info is not None
        assert file_info.language == "JavaScript"
        assert file_info.lines > 0
        assert file_info.size > 0


class TestDataClasses:
    """Test data classes used in repository analysis."""
    
    def test_file_info_creation(self):
        """Test FileInfo dataclass creation."""
        file_info = FileInfo(
            path="test.py",
            size=1024,
            lines=50,
            language="Python",
            last_modified=1234567890.0,
            complexity=5
        )
        
        assert file_info.path == "test.py"
        assert file_info.size == 1024
        assert file_info.lines == 50
        assert file_info.language == "Python"
        assert file_info.complexity == 5
    
    def test_dependency_info_creation(self):
        """Test DependencyInfo dataclass creation."""
        dep_info = DependencyInfo(
            name="requests",
            version="2.25.0",
            type="direct",
            source="requirements.txt"
        )
        
        assert dep_info.name == "requests"
        assert dep_info.version == "2.25.0"
        assert dep_info.type == "direct"
        assert dep_info.source == "requirements.txt"
    
    def test_code_metrics_creation(self):
        """Test CodeMetrics dataclass creation."""
        metrics = CodeMetrics(
            cyclomatic_complexity=10,
            cognitive_complexity=8,
            lines_of_code=500,
            comment_ratio=0.15,
            function_count=25,
            class_count=5
        )
        
        assert metrics.cyclomatic_complexity == 10
        assert metrics.cognitive_complexity == 8
        assert metrics.lines_of_code == 500
        assert metrics.comment_ratio == 0.15
        assert metrics.function_count == 25
        assert metrics.class_count == 5
    
    def test_test_info_creation(self):
        """Test TestInfo dataclass creation."""
        test_info = TestInfo(
            total_tests=20,
            passing_tests=18,
            coverage_percentage=85.5,
            test_files=["test_main.py", "test_utils.py"],
            uncovered_lines=[15, 23, 45]
        )
        
        assert test_info.total_tests == 20
        assert test_info.passing_tests == 18
        assert test_info.coverage_percentage == 85.5
        assert len(test_info.test_files) == 2
        assert len(test_info.uncovered_lines) == 3


if __name__ == "__main__":
    pytest.main([__file__])