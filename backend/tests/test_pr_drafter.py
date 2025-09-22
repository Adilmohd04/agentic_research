"""
Unit tests for PR Drafter

Tests the pull request drafting functionality including PR description generation,
review checklist creation, and change impact analysis.
"""

import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import patch, MagicMock

from backend.src.copilot.pr_drafter import (
    PRDrafter,
    PRType,
    Priority,
    FileChange,
    IssueReference,
    ReviewChecklistItem,
    ChangeImpact,
    PRDraft
)


class TestPRDrafter:
    """Test cases for PRDrafter class."""
    
    @pytest.fixture
    def temp_repo(self):
        """Create a temporary repository for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            repo_path = Path(temp_dir)
            
            # Create sample config
            github_dir = repo_path / '.github'
            github_dir.mkdir()
            
            config = {
                'team_members': ['alice', 'bob', 'charlie'],
                'code_owners': {
                    '*.py': ['alice'],
                    'frontend/*': ['bob'],
                    'backend/*': ['charlie']
                },
                'labels': {
                    'feature': ['enhancement', 'feature'],
                    'bugfix': ['bug', 'fix']
                }
            }
            
            with open(github_dir / 'pr_drafter.json', 'w') as f:
                json.dump(config, f)
            
            yield repo_path
    
    @pytest.fixture
    def drafter(self, temp_repo):
        """Create a PRDrafter instance for testing."""
        with patch('backend.src.copilot.pr_drafter.RepositoryAnalyzer'):
            return PRDrafter(str(temp_repo))
    
    def test_init(self, temp_repo):
        """Test drafter initialization."""
        with patch('backend.src.copilot.pr_drafter.RepositoryAnalyzer'):
            drafter = PRDrafter(str(temp_repo))
            assert drafter.repo_path == temp_repo
            assert drafter.config is not None
            assert 'team_members' in drafter.config
    
    def test_detect_language(self, drafter):
        """Test language detection from file extensions."""
        assert drafter._detect_language("test.py") == "python"
        assert drafter._detect_language("test.js") == "javascript"
        assert drafter._detect_language("test.ts") == "typescript"
        assert drafter._detect_language("test.md") == "markdown"
        assert drafter._detect_language("test.unknown") == "text"    def 
test_analyze_file_changes_added(self, drafter):
        """Test file change analysis for added files."""
        changed_files = {
            "new_file.py": ("", "def hello():\n    print('Hello')")
        }
        
        file_changes = drafter._analyze_file_changes(changed_files)
        
        assert len(file_changes) == 1
        fc = file_changes[0]
        assert fc.path == "new_file.py"
        assert fc.change_type == "added"
        assert fc.additions == 2
        assert fc.deletions == 0
        assert fc.language == "python"
    
    def test_determine_pr_type_from_branch(self, drafter):
        """Test PR type determination from branch name."""
        file_changes = [FileChange("test.py", 10, 0, "added", "python")]
        
        # Feature branch
        pr_type = drafter._determine_pr_type(file_changes, [], "feature/new-login")
        assert pr_type == PRType.FEATURE
        
        # Bug fix branch
        pr_type = drafter._determine_pr_type(file_changes, [], "bugfix/fix-auth-issue")
        assert pr_type == PRType.BUGFIX
    
    def test_determine_priority(self, drafter):
        """Test priority determination."""
        file_changes = [FileChange("test.py", 10, 0, "added", "python")]
        
        # Critical for hotfix
        priority = drafter._determine_priority(PRType.HOTFIX, file_changes)
        assert priority == Priority.CRITICAL
        
        # High for bugfix
        priority = drafter._determine_priority(PRType.BUGFIX, file_changes)
        assert priority == Priority.HIGH
        
        # Medium for feature
        priority = drafter._determine_priority(PRType.FEATURE, file_changes)
        assert priority == Priority.MEDIUM
    
    def test_generate_title_from_branch(self, drafter):
        """Test title generation from branch name."""
        file_changes = [FileChange("test.py", 10, 0, "added", "python")]
        
        title = drafter._generate_title(
            PRType.FEATURE, file_changes, "feature/user-authentication", []
        )
        
        assert "feat:" in title
        assert "User Authentication" in title
    
    def test_draft_pr_complete(self, drafter):
        """Test complete PR drafting."""
        changed_files = {
            "auth.py": ("", "def login():\n    pass"),
            "test_auth.py": ("", "def test_login():\n    assert True")
        }
        
        pr_draft = drafter.draft_pr(
            changed_files=changed_files,
            branch_name="feature/user-auth",
            commit_messages=["Add user authentication"],
            issue_numbers=[123]
        )
        
        assert isinstance(pr_draft, PRDraft)
        assert pr_draft.pr_type == PRType.FEATURE
        assert pr_draft.priority in [Priority.LOW, Priority.MEDIUM, Priority.HIGH]
        assert len(pr_draft.file_changes) == 2
        assert len(pr_draft.issue_references) == 1
        assert pr_draft.issue_references[0].issue_number == 123
        assert len(pr_draft.review_checklist) > 0
        assert pr_draft.change_impact is not None
        assert len(pr_draft.labels) > 0
        assert "feat:" in pr_draft.title


if __name__ == "__main__":
    pytest.main([__file__])