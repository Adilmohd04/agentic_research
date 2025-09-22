"""
Repository Analysis Tools for Developer Copilot

This module provides comprehensive repository analysis capabilities including
file tree traversal, AST parsing, dependency analysis, and test coverage reporting.
"""

import ast
import os
import json
import subprocess
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, asdict
from collections import defaultdict
import logging

logger = logging.getLogger(__name__)

@dataclass
class FileInfo:
    """Information about a file in the repository."""
    path: str
    size: int
    lines: int
    language: str
    last_modified: float
    complexity: Optional[int] = None
    test_coverage: Optional[float] = None

@dataclass
class DependencyInfo:
    """Information about project dependencies."""
    name: str
    version: str
    type: str  # 'direct', 'dev', 'transitive'
    source: str  # 'requirements.txt', 'package.json', etc.

@dataclass
class CodeMetrics:
    """Code quality and complexity metrics."""
    cyclomatic_complexity: int
    cognitive_complexity: int
    lines_of_code: int
    comment_ratio: float
    function_count: int
    class_count: int

@dataclass
class TestInfo:
    """Test coverage and quality information."""
    total_tests: int
    passing_tests: int
    coverage_percentage: float
    test_files: List[str]
    uncovered_lines: List[int]

@dataclass
class RepositoryAnalysis:
    """Complete repository analysis results."""
    total_files: int
    total_lines: int
    languages: Dict[str, int]
    files: List[FileInfo]
    dependencies: List[DependencyInfo]
    metrics: CodeMetrics
    test_info: TestInfo
    structure: Dict[str, Any]

class RepositoryAnalyzer:
    """Analyzes repository structure, code quality, and dependencies."""
    
    SUPPORTED_LANGUAGES = {
        '.py': 'Python',
        '.js': 'JavaScript',
        '.ts': 'TypeScript',
        '.jsx': 'React',
        '.tsx': 'React TypeScript',
        '.java': 'Java',
        '.cpp': 'C++',
        '.c': 'C',
        '.cs': 'C#',
        '.go': 'Go',
        '.rs': 'Rust',
        '.php': 'PHP',
        '.rb': 'Ruby',
        '.swift': 'Swift',
        '.kt': 'Kotlin',
        '.scala': 'Scala',
        '.r': 'R',
        '.sql': 'SQL',
        '.html': 'HTML',
        '.css': 'CSS',
        '.scss': 'SCSS',
        '.less': 'LESS',
        '.vue': 'Vue',
        '.svelte': 'Svelte',
        '.md': 'Markdown',
        '.yml': 'YAML',
        '.yaml': 'YAML',
        '.json': 'JSON',
        '.xml': 'XML',
        '.sh': 'Shell',
        '.bash': 'Bash',
        '.zsh': 'Zsh',
        '.fish': 'Fish'
    }
    
    IGNORE_PATTERNS = {
        '.git', '.svn', '.hg',
        'node_modules', '__pycache__', '.pytest_cache',
        'venv', 'env', '.env',
        'dist', 'build', 'target',
        '.DS_Store', 'Thumbs.db',
        '*.pyc', '*.pyo', '*.pyd',
        '*.class', '*.jar', '*.war',
        '*.o', '*.so', '*.dll',
        '*.log', '*.tmp', '*.temp'
    }
    
    def __init__(self, repo_path: str):
        """Initialize repository analyzer.
        
        Args:
            repo_path: Path to the repository root
        """
        self.repo_path = Path(repo_path).resolve()
        if not self.repo_path.exists():
            raise ValueError(f"Repository path does not exist: {repo_path}")
    
    def analyze(self) -> RepositoryAnalysis:
        """Perform complete repository analysis.
        
        Returns:
            RepositoryAnalysis object with all analysis results
        """
        logger.info(f"Starting repository analysis for {self.repo_path}")
        
        # Traverse file tree and collect file information
        files = self._traverse_files()
        
        # Analyze dependencies
        dependencies = self._analyze_dependencies()
        
        # Calculate code metrics
        metrics = self._calculate_metrics(files)
        
        # Analyze test coverage
        test_info = self._analyze_tests()
        
        # Build repository structure
        structure = self._build_structure()
        
        # Aggregate language statistics
        languages = defaultdict(int)
        total_lines = 0
        
        for file_info in files:
            languages[file_info.language] += file_info.lines
            total_lines += file_info.lines
        
        return RepositoryAnalysis(
            total_files=len(files),
            total_lines=total_lines,
            languages=dict(languages),
            files=files,
            dependencies=dependencies,
            metrics=metrics,
            test_info=test_info,
            structure=structure
        )
    
    def _traverse_files(self) -> List[FileInfo]:
        """Traverse repository and collect file information.
        
        Returns:
            List of FileInfo objects for all relevant files
        """
        files = []
        
        for root, dirs, filenames in os.walk(self.repo_path):
            # Filter out ignored directories
            dirs[:] = [d for d in dirs if not self._should_ignore(d)]
            
            for filename in filenames:
                if self._should_ignore(filename):
                    continue
                
                file_path = Path(root) / filename
                relative_path = file_path.relative_to(self.repo_path)
                
                try:
                    file_info = self._analyze_file(file_path, str(relative_path))
                    if file_info:
                        files.append(file_info)
                except Exception as e:
                    logger.warning(f"Failed to analyze file {relative_path}: {e}")
        
        return files
    
    def _analyze_file(self, file_path: Path, relative_path: str) -> Optional[FileInfo]:
        """Analyze a single file.
        
        Args:
            file_path: Absolute path to the file
            relative_path: Relative path from repository root
            
        Returns:
            FileInfo object or None if file should be skipped
        """
        try:
            stat = file_path.stat()
            
            # Determine language
            language = self._detect_language(file_path)
            if not language:
                return None
            
            # Count lines
            lines = self._count_lines(file_path)
            
            # Calculate complexity for code files
            complexity = None
            if language in ['Python', 'JavaScript', 'TypeScript']:
                complexity = self._calculate_complexity(file_path, language)
            
            return FileInfo(
                path=relative_path,
                size=stat.st_size,
                lines=lines,
                language=language,
                last_modified=stat.st_mtime,
                complexity=complexity
            )
        
        except Exception as e:
            logger.warning(f"Error analyzing file {relative_path}: {e}")
            return None
    
    def _detect_language(self, file_path: Path) -> Optional[str]:
        """Detect programming language from file extension.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Language name or None if not supported
        """
        suffix = file_path.suffix.lower()
        return self.SUPPORTED_LANGUAGES.get(suffix)
    
    def _count_lines(self, file_path: Path) -> int:
        """Count lines in a file.
        
        Args:
            file_path: Path to the file
            
        Returns:
            Number of lines in the file
        """
        try:
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                return sum(1 for _ in f)
        except Exception:
            return 0
    
    def _calculate_complexity(self, file_path: Path, language: str) -> Optional[int]:
        """Calculate cyclomatic complexity for code files.
        
        Args:
            file_path: Path to the file
            language: Programming language
            
        Returns:
            Complexity score or None if calculation fails
        """
        if language == 'Python':
            return self._calculate_python_complexity(file_path)
        # Add support for other languages as needed
        return None
    
    def _calculate_python_complexity(self, file_path: Path) -> Optional[int]:
        """Calculate cyclomatic complexity for Python files.
        
        Args:
            file_path: Path to the Python file
            
        Returns:
            Complexity score or None if calculation fails
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content)
            complexity = 1  # Base complexity
            
            for node in ast.walk(tree):
                if isinstance(node, (ast.If, ast.While, ast.For, ast.AsyncFor)):
                    complexity += 1
                elif isinstance(node, ast.ExceptHandler):
                    complexity += 1
                elif isinstance(node, (ast.And, ast.Or)):
                    complexity += 1
                elif isinstance(node, ast.BoolOp):
                    complexity += len(node.values) - 1
            
            return complexity
        
        except Exception as e:
            logger.warning(f"Failed to calculate complexity for {file_path}: {e}")
            return None
    
    def _analyze_dependencies(self) -> List[DependencyInfo]:
        """Analyze project dependencies.
        
        Returns:
            List of DependencyInfo objects
        """
        dependencies = []
        
        # Python dependencies
        requirements_files = [
            'requirements.txt', 'requirements-dev.txt', 'requirements-test.txt',
            'pyproject.toml', 'setup.py', 'Pipfile'
        ]
        
        for req_file in requirements_files:
            req_path = self.repo_path / req_file
            if req_path.exists():
                deps = self._parse_python_dependencies(req_path, req_file)
                dependencies.extend(deps)
        
        # Node.js dependencies
        package_json = self.repo_path / 'package.json'
        if package_json.exists():
            deps = self._parse_nodejs_dependencies(package_json)
            dependencies.extend(deps)
        
        return dependencies
    
    def _parse_python_dependencies(self, file_path: Path, source: str) -> List[DependencyInfo]:
        """Parse Python dependencies from requirements files.
        
        Args:
            file_path: Path to the requirements file
            source: Source file name
            
        Returns:
            List of DependencyInfo objects
        """
        dependencies = []
        
        try:
            if source == 'pyproject.toml':
                # Parse TOML format
                import tomli
                with open(file_path, 'rb') as f:
                    data = tomli.load(f)
                
                # Extract dependencies from pyproject.toml
                deps = data.get('project', {}).get('dependencies', [])
                for dep in deps:
                    name, version = self._parse_dependency_spec(dep)
                    dependencies.append(DependencyInfo(
                        name=name,
                        version=version,
                        type='direct',
                        source=source
                    ))
            
            else:
                # Parse requirements.txt format
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#'):
                            name, version = self._parse_dependency_spec(line)
                            dep_type = 'dev' if 'dev' in source else 'direct'
                            dependencies.append(DependencyInfo(
                                name=name,
                                version=version,
                                type=dep_type,
                                source=source
                            ))
        
        except Exception as e:
            logger.warning(f"Failed to parse dependencies from {file_path}: {e}")
        
        return dependencies
    
    def _parse_nodejs_dependencies(self, file_path: Path) -> List[DependencyInfo]:
        """Parse Node.js dependencies from package.json.
        
        Args:
            file_path: Path to package.json
            
        Returns:
            List of DependencyInfo objects
        """
        dependencies = []
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Parse regular dependencies
            deps = data.get('dependencies', {})
            for name, version in deps.items():
                dependencies.append(DependencyInfo(
                    name=name,
                    version=version,
                    type='direct',
                    source='package.json'
                ))
            
            # Parse dev dependencies
            dev_deps = data.get('devDependencies', {})
            for name, version in dev_deps.items():
                dependencies.append(DependencyInfo(
                    name=name,
                    version=version,
                    type='dev',
                    source='package.json'
                ))
        
        except Exception as e:
            logger.warning(f"Failed to parse package.json: {e}")
        
        return dependencies
    
    def _parse_dependency_spec(self, spec: str) -> Tuple[str, str]:
        """Parse dependency specification string.
        
        Args:
            spec: Dependency specification (e.g., "requests>=2.25.0")
            
        Returns:
            Tuple of (name, version)
        """
        # Remove common operators and extract name/version
        for op in ['>=', '<=', '==', '!=', '>', '<', '~=']:
            if op in spec:
                name, version = spec.split(op, 1)
                return name.strip(), version.strip()
        
        # No version specified
        return spec.strip(), '*'
    
    def _calculate_metrics(self, files: List[FileInfo]) -> CodeMetrics:
        """Calculate overall code metrics.
        
        Args:
            files: List of analyzed files
            
        Returns:
            CodeMetrics object
        """
        total_complexity = 0
        total_lines = 0
        function_count = 0
        class_count = 0
        comment_lines = 0
        
        for file_info in files:
            if file_info.complexity:
                total_complexity += file_info.complexity
            total_lines += file_info.lines
            
            # Count functions and classes for Python files
            if file_info.language == 'Python':
                try:
                    file_path = self.repo_path / file_info.path
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    tree = ast.parse(content)
                    for node in ast.walk(tree):
                        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                            function_count += 1
                        elif isinstance(node, ast.ClassDef):
                            class_count += 1
                    
                    # Count comment lines
                    comment_lines += sum(1 for line in content.split('\n') 
                                       if line.strip().startswith('#'))
                
                except Exception:
                    pass
        
        comment_ratio = comment_lines / max(total_lines, 1)
        
        return CodeMetrics(
            cyclomatic_complexity=total_complexity,
            cognitive_complexity=total_complexity,  # Simplified
            lines_of_code=total_lines,
            comment_ratio=comment_ratio,
            function_count=function_count,
            class_count=class_count
        )
    
    def _analyze_tests(self) -> TestInfo:
        """Analyze test coverage and quality.
        
        Returns:
            TestInfo object with test analysis results
        """
        test_files = []
        total_tests = 0
        
        # Find test files
        for root, dirs, filenames in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if not self._should_ignore(d)]
            
            for filename in filenames:
                if (filename.startswith('test_') or filename.endswith('_test.py') or
                    'test' in filename.lower() and filename.endswith('.py')):
                    
                    file_path = Path(root) / filename
                    relative_path = str(file_path.relative_to(self.repo_path))
                    test_files.append(relative_path)
                    
                    # Count test functions
                    try:
                        with open(file_path, 'r', encoding='utf-8') as f:
                            content = f.read()
                        
                        tree = ast.parse(content)
                        for node in ast.walk(tree):
                            if (isinstance(node, ast.FunctionDef) and 
                                node.name.startswith('test_')):
                                total_tests += 1
                    
                    except Exception:
                        pass
        
        # Try to get coverage information
        coverage_percentage = 0.0
        try:
            # Run coverage if available
            result = subprocess.run(
                ['coverage', 'report', '--show-missing'],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0:
                # Parse coverage output
                lines = result.stdout.split('\n')
                for line in lines:
                    if 'TOTAL' in line:
                        parts = line.split()
                        if len(parts) >= 4 and parts[-1].endswith('%'):
                            coverage_percentage = float(parts[-1][:-1])
                            break
        
        except Exception:
            pass
        
        return TestInfo(
            total_tests=total_tests,
            passing_tests=total_tests,  # Assume all pass for now
            coverage_percentage=coverage_percentage,
            test_files=test_files,
            uncovered_lines=[]
        )
    
    def _build_structure(self) -> Dict[str, Any]:
        """Build repository structure tree.
        
        Returns:
            Nested dictionary representing repository structure
        """
        structure = {}
        
        for root, dirs, filenames in os.walk(self.repo_path):
            dirs[:] = [d for d in dirs if not self._should_ignore(d)]
            
            # Get relative path from repo root
            rel_root = Path(root).relative_to(self.repo_path)
            
            # Navigate to the correct position in structure
            current = structure
            if str(rel_root) != '.':
                for part in rel_root.parts:
                    if part not in current:
                        current[part] = {}
                    current = current[part]
            
            # Add directories
            for dirname in dirs:
                if dirname not in current:
                    current[dirname] = {}
            
            # Add files
            for filename in filenames:
                if not self._should_ignore(filename):
                    current[filename] = None  # Files are leaf nodes
        
        return structure
    
    def _should_ignore(self, name: str) -> bool:
        """Check if file or directory should be ignored.
        
        Args:
            name: File or directory name
            
        Returns:
            True if should be ignored
        """
        # Check exact matches
        if name in self.IGNORE_PATTERNS:
            return True
        
        # Check pattern matches
        for pattern in self.IGNORE_PATTERNS:
            if '*' in pattern:
                import fnmatch
                if fnmatch.fnmatch(name, pattern):
                    return True
        
        # Ignore hidden files/directories (starting with .)
        if name.startswith('.') and name not in ['.gitignore', '.env.example']:
            return True
        
        return False
    
    def get_file_analysis(self, file_path: str) -> Optional[FileInfo]:
        """Get detailed analysis for a specific file.
        
        Args:
            file_path: Relative path to the file
            
        Returns:
            FileInfo object or None if file not found
        """
        full_path = self.repo_path / file_path
        if not full_path.exists():
            return None
        
        return self._analyze_file(full_path, file_path)
    
    def get_dependency_tree(self) -> Dict[str, List[str]]:
        """Build dependency tree showing relationships.
        
        Returns:
            Dictionary mapping dependencies to their dependents
        """
        # This is a simplified implementation
        # In practice, you'd want to use tools like pipdeptree or npm ls
        dependencies = self._analyze_dependencies()
        
        tree = defaultdict(list)
        for dep in dependencies:
            tree[dep.type].append(dep.name)
        
        return dict(tree)
    
    def export_analysis(self, output_path: str, format: str = 'json') -> None:
        """Export analysis results to file.
        
        Args:
            output_path: Path to output file
            format: Output format ('json' or 'yaml')
        """
        analysis = self.analyze()
        
        if format == 'json':
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(asdict(analysis), f, indent=2, default=str)
        
        elif format == 'yaml':
            import yaml
            with open(output_path, 'w', encoding='utf-8') as f:
                yaml.dump(asdict(analysis), f, default_flow_style=False)
        
        else:
            raise ValueError(f"Unsupported format: {format}")