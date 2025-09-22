"""
Pull Request Drafting Functionality for Developer Copilot

This module provides comprehensive pull request drafting capabilities including
generating PR descriptions, review checklists, and change impact analysis.
"""

import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Set, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging

from .code_diff_generator import CodeDiffGenerator, DiffAnalysis, ChangeType
from .repository_analyzer import RepositoryAnalyzer

logger = logging.getLogger(__name__)

class PRType(Enum):
    """Types of pull requests."""
    FEATURE = "feature"
    BUGFIX = "bugfix"
    HOTFIX = "hotfix"
    REFACTOR = "refactor"
    DOCS = "docs"
    CHORE = "chore"
    PERFORMANCE = "performance"
    SECURITY = "security"

class Priority(Enum):
    """Priority levels for pull requests."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"

@dataclass
class FileChange:
    """Information about a changed file."""
    path: str
    additions: int
    deletions: int
    change_type: str  # 'added', 'modified', 'deleted', 'renamed'
    language: str
    complexity_change: Optional[int] = None

@dataclass
class IssueReference:
    """Reference to related issues."""
    issue_number: int
    issue_title: str
    issue_type: str  # 'closes', 'fixes', 'relates', 'references'

@dataclass
class ReviewChecklistItem:
    """Item in the review checklist."""
    category: str
    description: str
    required: bool
    automated: bool

@dataclass
class ChangeImpact:
    """Analysis of change impact."""
    affected_components: List[str]
    breaking_changes: List[str]
    migration_notes: List[str]
    performance_impact: str
    security_impact: str
    testing_requirements: List[str]

@dataclass
class PRDraft:
    """Complete pull request draft."""
    title: str
    description: str
    pr_type: PRType
    priority: Priority
    file_changes: List[FileChange]
    issue_references: List[IssueReference]
    review_checklist: List[ReviewChecklistItem]
    change_impact: ChangeImpact
    labels: List[str]
    assignees: List[str]
    reviewers: List[str]
    milestone: Optional[str] = None
class 
PRDrafter:
    """Generates pull request descriptions and review checklists."""
    
    def __init__(self, repo_path: str):
        """Initialize PR drafter.
        
        Args:
            repo_path: Path to the repository root
        """
        self.repo_path = Path(repo_path)
        self.diff_generator = CodeDiffGenerator()
        self.repo_analyzer = RepositoryAnalyzer(repo_path)
        
        # Load configuration if available
        self.config = self._load_config()
    
    def draft_pr(self, 
                 changed_files: Dict[str, Tuple[str, str]], 
                 branch_name: str = "",
                 commit_messages: List[str] = None,
                 issue_numbers: List[int] = None) -> PRDraft:
        """Draft a complete pull request.
        
        Args:
            changed_files: Dict mapping file paths to (original, modified) content tuples
            branch_name: Name of the feature branch
            commit_messages: List of commit messages
            issue_numbers: List of related issue numbers
            
        Returns:
            PRDraft object with complete PR information
        """
        logger.info(f"Drafting PR for {len(changed_files)} changed files")
        
        # Analyze file changes
        file_changes = self._analyze_file_changes(changed_files)
        
        # Determine PR type and priority
        pr_type = self._determine_pr_type(file_changes, commit_messages, branch_name)
        priority = self._determine_priority(pr_type, file_changes)
        
        # Generate title and description
        title = self._generate_title(pr_type, file_changes, branch_name, commit_messages)
        description = self._generate_description(
            pr_type, file_changes, changed_files, commit_messages
        )
        
        # Process issue references
        issue_references = self._process_issue_references(
            issue_numbers, commit_messages, description
        )
        
        # Generate review checklist
        review_checklist = self._generate_review_checklist(pr_type, file_changes)
        
        # Analyze change impact
        change_impact = self._analyze_change_impact(file_changes, changed_files)
        
        # Generate labels, assignees, and reviewers
        labels = self._generate_labels(pr_type, file_changes, change_impact)
        assignees = self._suggest_assignees(file_changes)
        reviewers = self._suggest_reviewers(file_changes, change_impact)
        
        # Determine milestone
        milestone = self._determine_milestone(pr_type, priority, issue_references)
        
        return PRDraft(
            title=title,
            description=description,
            pr_type=pr_type,
            priority=priority,
            file_changes=file_changes,
            issue_references=issue_references,
            review_checklist=review_checklist,
            change_impact=change_impact,
            labels=labels,
            assignees=assignees,
            reviewers=reviewers,
            milestone=milestone
        )
    
    def _load_config(self) -> Dict[str, Any]:
        """Load PR drafter configuration."""
        config_path = self.repo_path / '.github' / 'pr_drafter.json'
        
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except Exception as e:
                logger.warning(f"Failed to load PR drafter config: {e}")
        
        # Default configuration
        return {
            'team_members': [],
            'code_owners': {},
            'review_requirements': {
                'min_reviewers': 1,
                'require_code_owner': False
            },
            'labels': {
                'feature': ['enhancement', 'feature'],
                'bugfix': ['bug', 'fix'],
                'hotfix': ['hotfix', 'urgent'],
                'refactor': ['refactor', 'cleanup'],
                'docs': ['documentation'],
                'chore': ['chore', 'maintenance'],
                'performance': ['performance', 'optimization'],
                'security': ['security']
            },
            'milestones': {
                'feature': 'next-release',
                'bugfix': 'current-sprint',
                'hotfix': 'current-sprint'
            }
        }   
 def _analyze_file_changes(self, changed_files: Dict[str, Tuple[str, str]]) -> List[FileChange]:
        """Analyze changes in each file.
        
        Args:
            changed_files: Dict mapping file paths to (original, modified) content tuples
            
        Returns:
            List of FileChange objects
        """
        file_changes = []
        
        for file_path, (original, modified) in changed_files.items():
            # Count additions and deletions
            original_lines = original.splitlines() if original else []
            modified_lines = modified.splitlines() if modified else []
            
            additions = len(modified_lines)
            deletions = len(original_lines)
            
            # Determine change type
            if not original and modified:
                change_type = 'added'
                deletions = 0
            elif original and not modified:
                change_type = 'deleted'
                additions = 0
            else:
                change_type = 'modified'
                # Calculate net additions/deletions
                import difflib
                matcher = difflib.SequenceMatcher(None, original_lines, modified_lines)
                additions = sum(j2 - j1 for tag, i1, i2, j1, j2 in matcher.get_opcodes() 
                              if tag in ['insert', 'replace'])
                deletions = sum(i2 - i1 for tag, i1, i2, j1, j2 in matcher.get_opcodes() 
                              if tag in ['delete', 'replace'])
            
            # Detect language
            language = self._detect_language(file_path)
            
            # Calculate complexity change for code files
            complexity_change = None
            if language in ['python', 'javascript', 'typescript'] and change_type == 'modified':
                complexity_change = self._calculate_complexity_change(
                    original, modified, file_path
                )
            
            file_changes.append(FileChange(
                path=file_path,
                additions=additions,
                deletions=deletions,
                change_type=change_type,
                language=language,
                complexity_change=complexity_change
            ))
        
        return file_changes
    
    def _detect_language(self, file_path: str) -> str:
        """Detect programming language from file extension."""
        suffix = Path(file_path).suffix.lower()
        language_map = {
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
            '.rb': 'ruby',
            '.html': 'html',
            '.css': 'css',
            '.scss': 'scss',
            '.md': 'markdown',
            '.yml': 'yaml',
            '.yaml': 'yaml',
            '.json': 'json',
            '.xml': 'xml',
            '.sql': 'sql'
        }
        return language_map.get(suffix, 'text')
    
    def _calculate_complexity_change(self, original: str, modified: str, file_path: str) -> Optional[int]:
        """Calculate change in code complexity."""
        try:
            # Use the diff generator to analyze complexity
            analysis = self.diff_generator.analyze_changes(original, modified, file_path)
            
            # Sum up complexity changes
            complexity_change = 0
            for change in analysis.changes:
                if change.change_type == ChangeType.ADD:
                    complexity_change += 1
                elif change.change_type == ChangeType.DELETE:
                    complexity_change -= 1
                elif change.change_type in [ChangeType.REFACTOR, ChangeType.OPTIMIZE]:
                    complexity_change -= 1  # Assume refactoring reduces complexity
            
            return complexity_change
        
        except Exception as e:
            logger.warning(f"Failed to calculate complexity change for {file_path}: {e}")
            return None    def 
_determine_pr_type(self, 
                          file_changes: List[FileChange], 
                          commit_messages: List[str] = None,
                          branch_name: str = "") -> PRType:
        """Determine the type of pull request."""
        # Check branch name patterns
        branch_patterns = {
            PRType.FEATURE: [r'feature/', r'feat/', r'add-', r'implement-'],
            PRType.BUGFIX: [r'bugfix/', r'fix/', r'bug-', r'issue-'],
            PRType.HOTFIX: [r'hotfix/', r'urgent-', r'critical-'],
            PRType.REFACTOR: [r'refactor/', r'cleanup/', r'improve-'],
            PRType.DOCS: [r'docs/', r'doc-', r'documentation-'],
            PRType.CHORE: [r'chore/', r'maintenance/', r'update-'],
            PRType.PERFORMANCE: [r'perf/', r'performance/', r'optimize-'],
            PRType.SECURITY: [r'security/', r'sec-', r'vulnerability-']
        }
        
        for pr_type, patterns in branch_patterns.items():
            if any(re.search(pattern, branch_name, re.IGNORECASE) for pattern in patterns):
                return pr_type
        
        # Check commit message patterns
        if commit_messages:
            all_messages = ' '.join(commit_messages).lower()
            
            if any(word in all_messages for word in ['fix', 'bug', 'issue', 'error']):
                return PRType.BUGFIX
            elif any(word in all_messages for word in ['add', 'implement', 'feature', 'new']):
                return PRType.FEATURE
            elif any(word in all_messages for word in ['refactor', 'cleanup', 'improve']):
                return PRType.REFACTOR
            elif any(word in all_messages for word in ['docs', 'documentation', 'readme']):
                return PRType.DOCS
            elif any(word in all_messages for word in ['performance', 'optimize', 'speed']):
                return PRType.PERFORMANCE
            elif any(word in all_messages for word in ['security', 'vulnerability', 'auth']):
                return PRType.SECURITY
        
        # Check file types
        doc_files = sum(1 for fc in file_changes if fc.language in ['markdown', 'text'])
        code_files = sum(1 for fc in file_changes if fc.language not in ['markdown', 'text', 'json', 'yaml'])
        
        if doc_files > 0 and code_files == 0:
            return PRType.DOCS
        
        # Default to feature for code changes
        if code_files > 0:
            return PRType.FEATURE
        
        return PRType.CHORE
    
    def _determine_priority(self, pr_type: PRType, file_changes: List[FileChange]) -> Priority:
        """Determine the priority of the pull request."""
        # High priority types
        if pr_type in [PRType.HOTFIX, PRType.SECURITY]:
            return Priority.CRITICAL
        
        if pr_type == PRType.BUGFIX:
            return Priority.HIGH
        
        # Check for large changes
        total_changes = sum(fc.additions + fc.deletions for fc in file_changes)
        if total_changes > 500:
            return Priority.HIGH
        elif total_changes > 100:
            return Priority.MEDIUM
        
        # Default priorities by type
        priority_map = {
            PRType.FEATURE: Priority.MEDIUM,
            PRType.PERFORMANCE: Priority.MEDIUM,
            PRType.REFACTOR: Priority.LOW,
            PRType.DOCS: Priority.LOW,
            PRType.CHORE: Priority.LOW
        }
        
        return priority_map.get(pr_type, Priority.MEDIUM)    
def _generate_title(self, 
                       pr_type: PRType, 
                       file_changes: List[FileChange],
                       branch_name: str = "",
                       commit_messages: List[str] = None) -> str:
        """Generate a descriptive PR title."""
        # Extract meaningful parts from branch name
        branch_title = ""
        if branch_name:
            # Remove common prefixes and clean up
            clean_branch = re.sub(r'^(feature|feat|bugfix|fix|hotfix|refactor|docs|chore)/', '', branch_name)
            clean_branch = re.sub(r'[-_]', ' ', clean_branch)
            branch_title = clean_branch.title()
        
        # Use first commit message if available and meaningful
        commit_title = ""
        if commit_messages:
            first_commit = commit_messages[0].strip()
            # Skip generic commit messages
            if not any(generic in first_commit.lower() for generic in ['wip', 'temp', 'fix', 'update']):
                commit_title = first_commit
        
        # Generate title based on changes
        if branch_title:
            title = branch_title
        elif commit_title:
            title = commit_title
        else:
            # Generate from file changes
            if len(file_changes) == 1:
                fc = file_changes[0]
                if fc.change_type == 'added':
                    title = f"Add {Path(fc.path).name}"
                elif fc.change_type == 'deleted':
                    title = f"Remove {Path(fc.path).name}"
                else:
                    title = f"Update {Path(fc.path).name}"
            else:
                # Multiple files
                languages = set(fc.language for fc in file_changes if fc.language != 'text')
                if len(languages) == 1:
                    lang = list(languages)[0]
                    title = f"Update {lang.title()} files"
                else:
                    title = f"Update {len(file_changes)} files"
        
        # Add type prefix
        type_prefixes = {
            PRType.FEATURE: "feat:",
            PRType.BUGFIX: "fix:",
            PRType.HOTFIX: "hotfix:",
            PRType.REFACTOR: "refactor:",
            PRType.DOCS: "docs:",
            PRType.CHORE: "chore:",
            PRType.PERFORMANCE: "perf:",
            PRType.SECURITY: "security:"
        }
        
        prefix = type_prefixes.get(pr_type, "")
        if prefix and not title.lower().startswith(prefix.split(':')[0]):
            title = f"{prefix} {title}"
        
        # Ensure title is not too long
        if len(title) > 72:
            title = title[:69] + "..."
        
        return title
    
    def _generate_description(self, 
                             pr_type: PRType,
                             file_changes: List[FileChange],
                             changed_files: Dict[str, Tuple[str, str]],
                             commit_messages: List[str] = None) -> str:
        """Generate a comprehensive PR description."""
        sections = []
        
        # Summary section
        sections.append("## Summary")
        summary = self._generate_summary(pr_type, file_changes, commit_messages)
        sections.append(summary)
        sections.append("")
        
        # Changes section
        sections.append("## Changes")
        changes_desc = self._generate_changes_description(file_changes, changed_files)
        sections.append(changes_desc)
        sections.append("")
        
        # Testing section
        if pr_type in [PRType.FEATURE, PRType.BUGFIX, PRType.REFACTOR]:
            sections.append("## Testing")
            testing_desc = self._generate_testing_description(pr_type, file_changes)
            sections.append(testing_desc)
            sections.append("")
        
        return '\n'.join(sections) 
   def _generate_summary(self, 
                         pr_type: PRType, 
                         file_changes: List[FileChange],
                         commit_messages: List[str] = None) -> str:
        """Generate a summary of the changes."""
        if commit_messages and len(commit_messages) == 1:
            # Single commit - use commit message as summary
            return commit_messages[0]
        
        # Generate summary based on changes
        total_additions = sum(fc.additions for fc in file_changes)
        total_deletions = sum(fc.deletions for fc in file_changes)
        
        summary_parts = []
        
        # Describe the type of change
        type_descriptions = {
            PRType.FEATURE: "This PR introduces new functionality",
            PRType.BUGFIX: "This PR fixes a bug",
            PRType.HOTFIX: "This PR provides an urgent fix",
            PRType.REFACTOR: "This PR refactors existing code",
            PRType.DOCS: "This PR updates documentation",
            PRType.CHORE: "This PR performs maintenance tasks",
            PRType.PERFORMANCE: "This PR improves performance",
            PRType.SECURITY: "This PR addresses security issues"
        }
        
        summary_parts.append(type_descriptions.get(pr_type, "This PR makes changes"))
        
        # Add file statistics
        if len(file_changes) == 1:
            fc = file_changes[0]
            summary_parts.append(f"to `{fc.path}`")
        else:
            summary_parts.append(f"across {len(file_changes)} files")
        
        # Add change statistics
        if total_additions > 0 and total_deletions > 0:
            summary_parts.append(f"({total_additions} additions, {total_deletions} deletions)")
        elif total_additions > 0:
            summary_parts.append(f"({total_additions} additions)")
        elif total_deletions > 0:
            summary_parts.append(f"({total_deletions} deletions)")
        
        return ' '.join(summary_parts) + '.'
    
    def _generate_changes_description(self, 
                                    file_changes: List[FileChange],
                                    changed_files: Dict[str, Tuple[str, str]]) -> str:
        """Generate detailed description of changes."""
        changes = []
        
        # Group changes by type
        added_files = [fc for fc in file_changes if fc.change_type == 'added']
        modified_files = [fc for fc in file_changes if fc.change_type == 'modified']
        deleted_files = [fc for fc in file_changes if fc.change_type == 'deleted']
        
        if added_files:
            changes.append("### Added")
            for fc in added_files:
                changes.append(f"- `{fc.path}` ({fc.additions} lines)")
        
        if modified_files:
            changes.append("### Modified")
            for fc in modified_files:
                complexity_note = ""
                if fc.complexity_change is not None:
                    if fc.complexity_change > 0:
                        complexity_note = " (increased complexity)"
                    elif fc.complexity_change < 0:
                        complexity_note = " (reduced complexity)"
                
                changes.append(f"- `{fc.path}` (+{fc.additions}/-{fc.deletions}){complexity_note}")
        
        if deleted_files:
            changes.append("### Deleted")
            for fc in deleted_files:
                changes.append(f"- `{fc.path}` ({fc.deletions} lines)")
        
        return '\n'.join(changes) if changes else "No significant changes detected."
    
    def _generate_testing_description(self, pr_type: PRType, file_changes: List[FileChange]) -> str:
        """Generate testing description."""
        test_files = [fc for fc in file_changes if 'test' in fc.path.lower()]
        
        if test_files:
            testing_desc = ["Tests have been updated/added:"]
            for fc in test_files:
                testing_desc.append(f"- `{fc.path}`")
        else:
            testing_desc = ["Please ensure the following testing is completed:"]
            
            if pr_type == PRType.FEATURE:
                testing_desc.extend([
                    "- [ ] Unit tests for new functionality",
                    "- [ ] Integration tests if applicable",
                    "- [ ] Manual testing of new features"
                ])
            elif pr_type == PRType.BUGFIX:
                testing_desc.extend([
                    "- [ ] Regression test for the fixed bug",
                    "- [ ] Verification that the bug is resolved",
                    "- [ ] No new issues introduced"
                ])
            elif pr_type == PRType.REFACTOR:
                testing_desc.extend([
                    "- [ ] All existing tests pass",
                    "- [ ] No functional changes verified",
                    "- [ ] Performance impact assessed"
                ])
        
        return '\n'.join(testing_desc) 
   def _process_issue_references(self, 
                                 issue_numbers: List[int] = None,
                                 commit_messages: List[str] = None,
                                 description: str = "") -> List[IssueReference]:
        """Process and extract issue references."""
        references = []
        
        # Add explicitly provided issue numbers
        if issue_numbers:
            for issue_num in issue_numbers:
                references.append(IssueReference(
                    issue_number=issue_num,
                    issue_title=f"Issue #{issue_num}",
                    issue_type="relates"
                ))
        
        # Extract from commit messages
        if commit_messages:
            for message in commit_messages:
                # Look for issue references
                issue_matches = re.findall(r'#(\d+)', message)
                for match in issue_matches:
                    issue_num = int(match)
                    
                    # Determine relationship type
                    issue_type = "relates"
                    if any(keyword in message.lower() for keyword in ['fix', 'fixes', 'fixed']):
                        issue_type = "fixes"
                    elif any(keyword in message.lower() for keyword in ['close', 'closes', 'closed']):
                        issue_type = "closes"
                    
                    references.append(IssueReference(
                        issue_number=issue_num,
                        issue_title=f"Issue #{issue_num}",
                        issue_type=issue_type
                    ))
        
        # Remove duplicates
        unique_refs = []
        seen_issues = set()
        for ref in references:
            if ref.issue_number not in seen_issues:
                unique_refs.append(ref)
                seen_issues.add(ref.issue_number)
        
        return unique_refs
    
    def _generate_review_checklist(self, pr_type: PRType, file_changes: List[FileChange]) -> List[ReviewChecklistItem]:
        """Generate review checklist based on PR type and changes."""
        checklist = []
        
        # Common items for all PRs
        checklist.extend([
            ReviewChecklistItem("General", "Code follows project style guidelines", True, False),
            ReviewChecklistItem("General", "No obvious bugs or issues", True, False),
            ReviewChecklistItem("General", "Commit messages are clear and descriptive", False, False)
        ])
        
        # Type-specific items
        if pr_type == PRType.FEATURE:
            checklist.extend([
                ReviewChecklistItem("Feature", "New functionality is properly tested", True, False),
                ReviewChecklistItem("Feature", "Documentation updated if needed", False, False),
                ReviewChecklistItem("Feature", "No breaking changes without justification", True, False)
            ])
        
        elif pr_type == PRType.BUGFIX:
            checklist.extend([
                ReviewChecklistItem("Bug Fix", "Root cause of bug identified", True, False),
                ReviewChecklistItem("Bug Fix", "Fix addresses the root cause", True, False),
                ReviewChecklistItem("Bug Fix", "Regression test added", True, False)
            ])
        
        elif pr_type == PRType.REFACTOR:
            checklist.extend([
                ReviewChecklistItem("Refactor", "No functional changes", True, False),
                ReviewChecklistItem("Refactor", "Code complexity reduced", False, False),
                ReviewChecklistItem("Refactor", "All tests still pass", True, True)
            ])
        
        elif pr_type == PRType.SECURITY:
            checklist.extend([
                ReviewChecklistItem("Security", "Security implications reviewed", True, False),
                ReviewChecklistItem("Security", "No sensitive data exposed", True, False),
                ReviewChecklistItem("Security", "Security team approval obtained", True, False)
            ])
        
        return checklist    de
f _analyze_change_impact(self, 
                              file_changes: List[FileChange],
                              changed_files: Dict[str, Tuple[str, str]]) -> ChangeImpact:
        """Analyze the impact of changes."""
        # Identify affected components
        affected_components = self._identify_affected_components(file_changes)
        
        # Identify breaking changes
        breaking_changes = self._identify_breaking_changes(file_changes, changed_files)
        
        # Generate migration notes
        migration_notes = []
        if breaking_changes:
            migration_notes.append("Review breaking changes and update dependent code")
        
        # Assess performance impact
        performance_impact = "Minimal"
        perf_files = [fc for fc in file_changes if any(indicator in fc.path.lower() 
                     for indicator in ['performance', 'optimization', 'cache', 'index'])]
        if perf_files:
            performance_impact = "Potential impact - review performance changes"
        
        # Assess security impact
        security_impact = "None identified"
        security_files = [fc for fc in file_changes if any(indicator in fc.path.lower() 
                         for indicator in ['auth', 'security', 'permission', 'token', 'password'])]
        if security_files:
            security_impact = "Security-related changes - requires security review"
        
        # Generate testing requirements
        testing_requirements = []
        if any(fc.language in ['python', 'javascript', 'typescript'] for fc in file_changes):
            testing_requirements.append("Unit tests required")
        
        if len(file_changes) > 3:
            testing_requirements.append("Integration tests recommended")
        
        return ChangeImpact(
            affected_components=affected_components,
            breaking_changes=breaking_changes,
            migration_notes=migration_notes,
            performance_impact=performance_impact,
            security_impact=security_impact,
            testing_requirements=testing_requirements
        )
    
    def _identify_affected_components(self, file_changes: List[FileChange]) -> List[str]:
        """Identify components affected by changes."""
        components = set()
        
        for fc in file_changes:
            path_parts = Path(fc.path).parts
            
            # Extract component from path structure
            if len(path_parts) > 1:
                # Use first directory as component
                components.add(path_parts[0])
            
            # Check for specific component indicators
            if 'api' in fc.path.lower():
                components.add('API')
            elif 'ui' in fc.path.lower() or 'frontend' in fc.path.lower():
                components.add('Frontend')
            elif 'backend' in fc.path.lower():
                components.add('Backend')
            elif 'database' in fc.path.lower() or 'db' in fc.path.lower():
                components.add('Database')
            elif 'test' in fc.path.lower():
                components.add('Tests')
            elif fc.language == 'markdown':
                components.add('Documentation')
        
        return sorted(list(components))
    
    def _identify_breaking_changes(self, 
                                  file_changes: List[FileChange],
                                  changed_files: Dict[str, Tuple[str, str]]) -> List[str]:
        """Identify potential breaking changes."""
        breaking_changes = []
        
        # Check for API/interface changes
        api_files = [fc for fc in file_changes if any(indicator in fc.path.lower() 
                    for indicator in ['api', 'interface', 'contract', 'schema'])]
        
        for fc in api_files:
            if fc.change_type == 'modified' and fc.path in changed_files:
                original, modified = changed_files[fc.path]
                
                # Simple heuristic: look for removed functions/methods
                if fc.language == 'python':
                    orig_functions = set(re.findall(r'def\s+(\w+)', original))
                    mod_functions = set(re.findall(r'def\s+(\w+)', modified))
                    removed_functions = orig_functions - mod_functions
                    
                    for func in removed_functions:
                        breaking_changes.append(f"Removed function `{func}` from `{fc.path}`")
        
        return breaking_changes 
   def _generate_labels(self, 
                        pr_type: PRType, 
                        file_changes: List[FileChange],
                        change_impact: ChangeImpact) -> List[str]:
        """Generate appropriate labels for the PR."""
        labels = []
        
        # Add type-based labels
        type_labels = self.config.get('labels', {}).get(pr_type.value, [])
        labels.extend(type_labels)
        
        # Add size labels
        total_changes = sum(fc.additions + fc.deletions for fc in file_changes)
        if total_changes > 500:
            labels.append('size/XL')
        elif total_changes > 200:
            labels.append('size/L')
        elif total_changes > 50:
            labels.append('size/M')
        else:
            labels.append('size/S')
        
        # Add component labels
        for component in change_impact.affected_components:
            labels.append(f'component/{component.lower()}')
        
        # Add special labels
        if change_impact.breaking_changes:
            labels.append('breaking-change')
        
        if change_impact.security_impact != "None identified":
            labels.append('security')
        
        return labels
    
    def _suggest_assignees(self, file_changes: List[FileChange]) -> List[str]:
        """Suggest assignees based on code ownership."""
        assignees = []
        
        # Check code owners configuration
        code_owners = self.config.get('code_owners', {})
        
        for fc in file_changes:
            for pattern, owners in code_owners.items():
                if re.match(pattern.replace('*', '.*'), fc.path):
                    assignees.extend(owners)
        
        # Remove duplicates and return
        return list(set(assignees))
    
    def _suggest_reviewers(self, 
                          file_changes: List[FileChange],
                          change_impact: ChangeImpact) -> List[str]:
        """Suggest reviewers based on changes and impact."""
        reviewers = []
        
        # Get team members from config
        team_members = self.config.get('team_members', [])
        
        # Add code owners as reviewers
        reviewers.extend(self._suggest_assignees(file_changes))
        
        # Add security team for security changes
        if change_impact.security_impact != "None identified":
            security_team = self.config.get('security_team', [])
            reviewers.extend(security_team)
        
        # Add random team members if no specific reviewers
        if not reviewers and team_members:
            import random
            min_reviewers = self.config.get('review_requirements', {}).get('min_reviewers', 1)
            reviewers = random.sample(team_members, min(min_reviewers, len(team_members)))
        
        return list(set(reviewers))
    
    def _determine_milestone(self, 
                           pr_type: PRType, 
                           priority: Priority,
                           issue_references: List[IssueReference]) -> Optional[str]:
        """Determine appropriate milestone for the PR."""
        milestones = self.config.get('milestones', {})
        
        # High priority items go to current sprint
        if priority in [Priority.CRITICAL, Priority.HIGH]:
            return milestones.get('urgent', 'current-sprint')
        
        # Type-based milestones
        return milestones.get(pr_type.value, None)
    
    def format_pr_description(self, pr_draft: PRDraft) -> str:
        """Format the complete PR description for GitHub/GitLab."""
        sections = []
        
        # Add the main description
        sections.append(pr_draft.description)
        
        # Add issue references
        if pr_draft.issue_references:
            sections.append("## Related Issues")
            for ref in pr_draft.issue_references:
                action = ref.issue_type.title()
                sections.append(f"- {action} #{ref.issue_number}")
            sections.append("")
        
        # Add review checklist
        if pr_draft.review_checklist:
            sections.append("## Review Checklist")
            for item in pr_draft.review_checklist:
                required_marker = " (Required)" if item.required else ""
                auto_marker = " (Automated)" if item.automated else ""
                sections.append(f"- [ ] {item.description}{required_marker}{auto_marker}")
            sections.append("")
        
        return '\n'.join(sections)
    
    def export_pr_draft(self, pr_draft: PRDraft, format: str = 'json') -> str:
        """Export PR draft in specified format."""
        if format == 'json':
            return json.dumps(asdict(pr_draft), indent=2, default=str)
        elif format == 'markdown':
            return self.format_pr_description(pr_draft)
        else:
            raise ValueError(f"Unsupported format: {format}")