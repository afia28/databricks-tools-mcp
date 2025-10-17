# US-7.3: Version Management and Changelog Automation

## Metadata
- **Story ID**: US-7.3
- **Title**: Version Management and Changelog Automation
- **Phase**: Phase 7 - Distribution & Deployment
- **Estimated LOC**: ~1000 lines
- **Dependencies**: US-7.1 (CLI initialization framework)
- **Status**: ⬜ Not Started

## Overview
Implement automated version management and changelog generation that parses conventional commit messages to automatically bump semantic versions, update version strings across multiple files, generate categorized CHANGELOG entries, create git tags, and validate version consistency throughout the project.

## User Story
**As a** developer maintaining the databricks-tools package
**I want** automated version management based on conventional commits
**So that** I can release new versions consistently without manual version tracking and changelog maintenance

## Acceptance Criteria
1. ✅ CLI command `databricks-tools-version bump` automatically detects version bump type from commit history (BREAKING CHANGE → major, feat → minor, fix → patch)
2. ✅ Version strings updated atomically in pyproject.toml, src/databricks_tools/__init__.py, and any configured files
3. ✅ CHANGELOG.md automatically generated with categorized sections (Added, Changed, Fixed, Removed, Breaking Changes) from commit messages
4. ✅ Git tags created with annotated messages including changelog summary for the release
5. ✅ Pre-release versions supported (alpha, beta, rc) with proper version progression (0.3.0-alpha.1 → 0.3.0-beta.1)
6. ✅ Dry-run mode shows all changes without modifying files (`--dry-run` flag)
7. ✅ Validation ensures clean working directory and passing tests before version bumps
8. ✅ Manual override supported with `--major`, `--minor`, `--patch` flags
9. ✅ Version consistency validated across all configured files with clear error messages for mismatches
10. ✅ Integration with existing CLI framework using Click and Rich for beautiful terminal output

## Technical Requirements

### Version Management Core (src/databricks_tools/versioning/version_manager.py)
```python
from typing import Optional, Literal
from pathlib import Path
from dataclasses import dataclass
from databricks_tools.versioning.commit_parser import CommitParser
from databricks_tools.versioning.changelog_generator import ChangelogGenerator
from databricks_tools.versioning.git_operations import GitOperations
from databricks_tools.versioning.file_updater import FileUpdater

@dataclass
class VersionConfig:
    """Configuration for version management."""
    current_version: str
    commit_version: bool = True
    tag_version: bool = True
    sign_tags: bool = False
    tag_message: Optional[str] = None
    files: list[str] = field(default_factory=list)

class VersionManager:
    """Orchestrates version bumping and changelog generation."""

    def __init__(
        self,
        config: VersionConfig,
        commit_parser: CommitParser,
        changelog_gen: ChangelogGenerator,
        git_ops: GitOperations,
        file_updater: FileUpdater
    ):
        self.config = config
        self.commit_parser = commit_parser
        self.changelog_gen = changelog_gen
        self.git_ops = git_ops
        self.file_updater = file_updater

    def bump_version(
        self,
        bump_type: Optional[Literal["major", "minor", "patch", "auto"]] = "auto",
        pre_release: Optional[Literal["alpha", "beta", "rc"]] = None,
        dry_run: bool = False
    ) -> str:
        """Bump version based on commits or manual override."""
        # Validate clean working directory
        if not dry_run and self.git_ops.is_dirty():
            raise ValueError("Working directory is not clean. Commit or stash changes.")

        # Determine bump type from commits if auto
        if bump_type == "auto":
            bump_type = self._detect_bump_type()

        # Calculate new version
        new_version = self._calculate_new_version(
            self.config.current_version,
            bump_type,
            pre_release
        )

        # Update files atomically
        if not dry_run:
            self.file_updater.update_version(
                self.config.files,
                self.config.current_version,
                new_version
            )

        return new_version
```

### Commit Parser (src/databricks_tools/versioning/commit_parser.py)
```python
import re
from dataclasses import dataclass
from typing import Optional, Literal

@dataclass
class ConventionalCommit:
    """Represents a parsed conventional commit."""
    type: str  # feat, fix, docs, style, refactor, perf, test, chore
    scope: Optional[str]
    description: str
    breaking: bool
    body: Optional[str]
    footers: dict[str, str]

class CommitParser:
    """Parses conventional commit messages."""

    # Regex for conventional commit format
    PATTERN = re.compile(
        r"^(?P<type>\w+)"
        r"(?:\((?P<scope>[^\)]+)\))?"
        r"(?P<breaking>!)?"
        r":\s*(?P<description>.+)"
    )

    def parse(self, message: str) -> ConventionalCommit:
        """Parse a conventional commit message."""
        lines = message.strip().split('\n')
        header = lines[0]

        match = self.PATTERN.match(header)
        if not match:
            raise ValueError(f"Invalid conventional commit format: {header}")

        # Check for BREAKING CHANGE in body/footer
        breaking = match.group("breaking") == "!" or "BREAKING CHANGE" in message

        return ConventionalCommit(
            type=match.group("type"),
            scope=match.group("scope"),
            description=match.group("description"),
            breaking=breaking,
            body=self._extract_body(lines),
            footers=self._extract_footers(lines)
        )

    def detect_bump_type(
        self,
        commits: list[str]
    ) -> Literal["major", "minor", "patch"]:
        """Determine version bump type from commits."""
        parsed_commits = [self.parse(commit) for commit in commits]

        # Major version for breaking changes
        if any(c.breaking for c in parsed_commits):
            return "major"

        # Minor version for features
        if any(c.type == "feat" for c in parsed_commits):
            return "minor"

        # Patch version for fixes
        if any(c.type == "fix" for c in parsed_commits):
            return "patch"

        # Default to patch for other changes
        return "patch"
```

### Changelog Generator (src/databricks_tools/versioning/changelog_generator.py)
```python
from datetime import datetime
from typing import Optional
from pathlib import Path
from databricks_tools.versioning.commit_parser import ConventionalCommit

class ChangelogGenerator:
    """Generates changelog entries from conventional commits."""

    # Commit type to changelog section mapping
    TYPE_TO_SECTION = {
        "feat": "Added",
        "fix": "Fixed",
        "docs": "Documentation",
        "style": "Style",
        "refactor": "Changed",
        "perf": "Performance",
        "test": "Tests",
        "chore": "Maintenance",
    }

    def generate_entry(
        self,
        version: str,
        commits: list[ConventionalCommit],
        date: Optional[datetime] = None
    ) -> str:
        """Generate a changelog entry for a version."""
        date = date or datetime.now()

        # Group commits by section
        sections = self._group_by_section(commits)

        # Build changelog entry
        lines = [
            f"## [{version}] - {date.strftime('%Y-%m-%d')}",
            ""
        ]

        # Add breaking changes first
        breaking = [c for c in commits if c.breaking]
        if breaking:
            lines.extend([
                "### Breaking Changes",
                ""
            ])
            for commit in breaking:
                scope = f"**{commit.scope}**: " if commit.scope else ""
                lines.append(f"- {scope}{commit.description}")
            lines.append("")

        # Add other sections
        for section, section_commits in sections.items():
            if section == "Breaking Changes":
                continue  # Already handled

            lines.extend([
                f"### {section}",
                ""
            ])
            for commit in section_commits:
                scope = f"**{commit.scope}**: " if commit.scope else ""
                lines.append(f"- {scope}{commit.description}")
            lines.append("")

        return "\n".join(lines)

    def update_changelog(
        self,
        changelog_path: Path,
        new_entry: str,
        dry_run: bool = False
    ) -> None:
        """Insert new entry into existing CHANGELOG.md."""
        if not changelog_path.exists():
            # Create new changelog
            content = self._create_changelog_template() + "\n" + new_entry
        else:
            # Insert after header
            content = changelog_path.read_text()
            insertion_point = self._find_insertion_point(content)
            content = (
                content[:insertion_point] +
                new_entry + "\n" +
                content[insertion_point:]
            )

        if not dry_run:
            changelog_path.write_text(content)
```

### CLI Commands (src/databricks_tools/cli/version.py)
```python
import click
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from pathlib import Path
from databricks_tools.versioning.version_manager import VersionManager
from databricks_tools.versioning.config_loader import load_version_config

console = Console()

@click.group()
def version_cli():
    """Version management and changelog automation commands."""
    pass

@version_cli.command()
@click.option(
    '--bump-type',
    type=click.Choice(['major', 'minor', 'patch', 'auto']),
    default='auto',
    help='Version bump type (auto detects from commits)'
)
@click.option(
    '--pre-release',
    type=click.Choice(['alpha', 'beta', 'rc']),
    help='Create pre-release version'
)
@click.option(
    '--dry-run',
    is_flag=True,
    help='Show what would change without modifying files'
)
@click.option(
    '--no-commit',
    is_flag=True,
    help='Do not create a commit after bumping'
)
@click.option(
    '--no-tag',
    is_flag=True,
    help='Do not create a git tag'
)
def bump(
    bump_type: str,
    pre_release: Optional[str],
    dry_run: bool,
    no_commit: bool,
    no_tag: bool
):
    """Bump project version based on conventional commits."""
    console.print("[bold blue]🚀 Version Bump Wizard[/bold blue]\n")

    # Load configuration
    config = load_version_config()
    manager = VersionManager.from_config(config)

    # Validate working directory
    if not dry_run:
        console.print("🔍 Validating working directory...")
        if manager.is_dirty():
            console.print("[red]✗ Working directory has uncommitted changes[/red]")
            raise click.Abort()

        console.print("🧪 Running tests...")
        if not manager.run_tests():
            console.print("[red]✗ Tests failed. Fix tests before bumping version.[/red]")
            raise click.Abort()

    # Detect or use specified bump type
    if bump_type == 'auto':
        detected = manager.detect_bump_type()
        console.print(f"🔍 Detected bump type: [cyan]{detected}[/cyan]")
        bump_type = detected

    # Calculate new version
    old_version = config.current_version
    new_version = manager.bump_version(
        bump_type=bump_type,
        pre_release=pre_release,
        dry_run=dry_run
    )

    # Display changes
    table = Table(title="Version Changes", show_header=True)
    table.add_column("File", style="cyan")
    table.add_column("Old Version", style="red")
    table.add_column("New Version", style="green")

    for file in config.files:
        table.add_row(file, old_version, new_version)

    console.print(table)

    if dry_run:
        console.print("\n[yellow]🔍 DRY RUN - No files modified[/yellow]")
        return

    # Generate changelog
    console.print("\n📝 Generating changelog entry...")
    changelog_entry = manager.generate_changelog(old_version, new_version)
    console.print(Panel(changelog_entry, title="Changelog Entry"))

    # Create commit and tag
    if not no_commit:
        console.print("📦 Creating commit...")
        manager.create_commit(new_version)

    if not no_tag:
        console.print("🏷️  Creating tag...")
        manager.create_tag(new_version, changelog_entry)

    console.print(f"\n[bold green]✅ Successfully bumped version to {new_version}![/bold green]")
    console.print("\nNext steps:")
    console.print("1. Review the changes")
    console.print("2. Push to remote: [cyan]git push && git push --tags[/cyan]")
    console.print("3. Create a release on GitHub")

@version_cli.command()
@click.option('--from-tag', help='Starting tag for changelog generation')
@click.option('--to-tag', default='HEAD', help='Ending tag (default: HEAD)')
@click.option('--output', '-o', type=click.Path(), help='Output file (default: CHANGELOG.md)')
def changelog(from_tag: Optional[str], to_tag: str, output: Optional[str]):
    """Generate or update changelog from commit history."""
    console.print("[bold blue]📝 Changelog Generator[/bold blue]\n")

    manager = VersionManager.from_config(load_version_config())

    # Get commit range
    commits = manager.get_commits(from_tag, to_tag)
    console.print(f"Found {len(commits)} commits to process")

    # Generate changelog
    entry = manager.generate_changelog_entry(commits)

    # Update file or display
    if output:
        Path(output).write_text(entry)
        console.print(f"[green]✅ Changelog written to {output}[/green]")
    else:
        console.print(Panel(entry, title="Generated Changelog"))

@version_cli.command()
def validate():
    """Validate version consistency across all files."""
    console.print("[bold blue]🔍 Version Validator[/bold blue]\n")

    config = load_version_config()
    manager = VersionManager.from_config(config)

    # Check all configured files
    versions = {}
    for file_path in config.files:
        version = manager.extract_version(file_path)
        versions[file_path] = version

    # Display results
    table = Table(title="Version Check", show_header=True)
    table.add_column("File", style="cyan")
    table.add_column("Version", style="green")
    table.add_column("Status", style="yellow")

    all_same = len(set(versions.values())) == 1

    for file, version in versions.items():
        status = "✅" if version == config.current_version else "❌"
        table.add_row(file, version, status)

    console.print(table)

    if all_same:
        console.print(f"\n[green]✅ All files have consistent version: {config.current_version}[/green]")
    else:
        console.print("\n[red]❌ Version mismatch detected![/red]")
        raise click.Exit(1)

# Register with main CLI
def register_version_commands(cli_group):
    """Register version commands with main CLI."""
    cli_group.add_command(version_cli)
```

## Design Patterns Used

1. **Command Pattern**: Click commands encapsulate version management operations as discrete, testable, and composable units
2. **Strategy Pattern**: Different version bump strategies (major/minor/patch/auto) with pluggable bump detection algorithms
3. **Chain of Responsibility**: Commit messages processed through categorizers to determine changelog sections
4. **Template Method Pattern**: ChangelogGenerator defines structure with customizable section generation
5. **Repository Pattern**: GitOperations abstracts git commands behind a clean interface for testability

## Key Implementation Notes

### Conventional Commit Parsing
```python
# Standard format: type(scope): description
feat(api): add new endpoint for version info
fix: resolve connection timeout issue
docs(readme): update installation instructions

# Breaking changes indicated by ! or footer
feat!: new API requires authentication
feat(api): redesign response format

BREAKING CHANGE: API v1 endpoints removed
```

### Semantic Version Rules
- **MAJOR** (1.0.0 → 2.0.0): Breaking changes detected
- **MINOR** (1.0.0 → 1.1.0): New features added
- **PATCH** (1.0.0 → 1.0.1): Bug fixes only
- **Pre-release** (1.0.0 → 1.1.0-alpha.1): Testing versions

### File Update Strategy
- Parse files to find version patterns
- Create backup before modifications
- Update all files atomically (all succeed or all rollback)
- Support multiple version formats (Python, TOML, JSON)
- Validate updates before committing

### Changelog Categories
```markdown
### Breaking Changes  (breaking commits)
### Added            (feat)
### Changed          (refactor)
### Fixed            (fix)
### Removed          (removed features)
### Documentation    (docs)
### Performance      (perf)
### Tests            (test)
### Maintenance      (chore)
```

### Git Operations Safety
- Always validate clean working directory
- Create annotated tags with changelog summary
- Support signed tags with GPG
- Allow custom tag messages
- Handle edge cases (no commits, first release)

### Configuration Sources
```toml
# pyproject.toml
[tool.bumpversion]
current_version = "0.2.0"
commit = true
tag = true
sign_tags = false

[[tool.bumpversion.files]]
filename = "pyproject.toml"
search = 'version = "{current_version}"'
replace = 'version = "{new_version}"'

[[tool.bumpversion.files]]
filename = "src/databricks_tools/__init__.py"
search = '__version__ = "{current_version}"'
replace = '__version__ = "{new_version}"'
```

## Files to Create/Modify

**Files to Create:**
- `src/databricks_tools/versioning/__init__.py` - Package marker
- `src/databricks_tools/versioning/version_manager.py` - Main orchestrator (~200 lines)
- `src/databricks_tools/versioning/commit_parser.py` - Conventional commit parser (~150 lines)
- `src/databricks_tools/versioning/semantic_version.py` - Version bumping logic (~100 lines)
- `src/databricks_tools/versioning/changelog_generator.py` - Changelog generation (~250 lines)
- `src/databricks_tools/versioning/git_operations.py` - Git wrapper (~100 lines)
- `src/databricks_tools/versioning/file_updater.py` - File update logic (~100 lines)
- `src/databricks_tools/versioning/config_loader.py` - Configuration loading (~50 lines)
- `src/databricks_tools/cli/version.py` - CLI commands (~150 lines)
- `tests/test_versioning/__init__.py` - Test package marker
- `tests/test_versioning/test_version_manager.py` - Version manager tests (~150 lines)
- `tests/test_versioning/test_commit_parser.py` - Parser tests (~100 lines)
- `tests/test_versioning/test_changelog_generator.py` - Changelog tests (~100 lines)
- `tests/test_versioning/test_semantic_version.py` - Version logic tests (~50 lines)
- `tests/test_cli/test_version.py` - CLI command tests (~100 lines)

**Files to Modify:**
- `src/databricks_tools/__init__.py` - Add __version__ = "0.2.0" (~5 lines)
- `pyproject.toml` - Add [tool.bumpversion] configuration (~20 lines)
- `src/databricks_tools/cli/__init__.py` - Register version commands (~5 lines)

## Test Cases

### Commit Parsing Tests
1. `test_parse_conventional_commit_with_scope` - Parse "feat(core): add feature"
2. `test_parse_conventional_commit_without_scope` - Parse "fix: resolve bug"
3. `test_parse_breaking_change_with_exclamation` - Parse "feat!: breaking change"
4. `test_parse_breaking_change_in_footer` - Detect BREAKING CHANGE footer
5. `test_parse_commit_with_body_and_footers` - Parse multi-line commits

### Version Bump Tests
6. `test_bump_major_for_breaking_change` - 1.2.3 → 2.0.0 on breaking
7. `test_bump_minor_for_feature` - 1.2.3 → 1.3.0 on feat
8. `test_bump_patch_for_fix` - 1.2.3 → 1.2.4 on fix
9. `test_bump_pre_release_alpha` - 1.2.3 → 1.3.0-alpha.1
10. `test_bump_pre_release_progression` - alpha.1 → beta.1 → rc.1 → final

### Changelog Generation Tests
11. `test_generate_changelog_with_categories` - Proper section grouping
12. `test_changelog_breaking_changes_first` - Breaking changes at top
13. `test_changelog_markdown_formatting` - Valid markdown output
14. `test_update_existing_changelog` - Insert at correct position
15. `test_changelog_date_formatting` - ISO date format

### File Update Tests
16. `test_update_pyproject_toml` - Update version in pyproject.toml
17. `test_update_init_py` - Update __version__ in __init__.py
18. `test_atomic_multi_file_update` - All files or none
19. `test_rollback_on_update_failure` - Restore on error
20. `test_version_pattern_detection` - Find various version formats

### CLI Integration Tests
21. `test_bump_command_auto_detection` - Auto-detect bump type
22. `test_bump_command_manual_override` - Use --major/--minor/--patch
23. `test_bump_command_dry_run` - No changes in dry-run
24. `test_changelog_command_generation` - Generate changelog entry
25. `test_validate_command_consistency` - Check version consistency

## Definition of Done

- [ ] All version management classes implemented with full type hints
- [ ] Conventional commit parser handles all standard types and breaking changes
- [ ] Semantic version bumping follows proper MAJOR.MINOR.PATCH rules
- [ ] Changelog generator creates properly formatted markdown with categories
- [ ] Git operations wrapped with proper error handling and validation
- [ ] File updater supports atomic multi-file updates with rollback
- [ ] CLI commands integrated with Click and Rich for beautiful output
- [ ] Dry-run mode implemented for all destructive operations
- [ ] Pre-release version support (alpha, beta, rc) with progression
- [ ] All 25+ test cases passing with 90%+ coverage
- [ ] Configuration loaded from pyproject.toml [tool.bumpversion] section
- [ ] Integration with existing CLI wizard patterns from US-7.1
- [ ] Type hints pass mypy strict mode checking
- [ ] Pre-commit hooks pass (ruff, mypy, pytest)
- [ ] Documentation includes usage examples and configuration guide

## Expected Outcome

After implementing this story, developers will have powerful version management automation:

1. **Automatic version bumping** based on commit messages without manual intervention
2. **Professional changelog generation** with properly categorized entries
3. **Consistent version updates** across all project files
4. **Git tag creation** with release notes included
5. **Pre-release support** for testing versions before stable releases

Example workflow:
```bash
# After several commits following conventional format
$ databricks-tools-version bump

🚀 Version Bump Wizard

🔍 Validating working directory... ✓
🧪 Running tests... ✓ (414 tests passed)
🔍 Detected bump type: minor

┌─────────────────────────────────────────────────┐
│ Version Changes                                 │
├──────────────────────┬──────────┬──────────────┤
│ File                 │ Old      │ New          │
├──────────────────────┼──────────┼──────────────┤
│ pyproject.toml       │ 0.2.0    │ 0.3.0        │
│ src/__init__.py      │ 0.2.0    │ 0.3.0        │
└──────────────────────┴──────────┴──────────────┘

📝 Generating changelog entry...

╭─ Changelog Entry ─────────────────────────────────╮
│ ## [0.3.0] - 2025-01-17                          │
│                                                   │
│ ### Added                                         │
│ - **cli**: Version management automation         │
│ - **versioning**: Conventional commit parser     │
│                                                   │
│ ### Fixed                                         │
│ - **core**: Connection timeout handling          │
╰───────────────────────────────────────────────────╯

📦 Creating commit...
🏷️  Creating tag v0.3.0...

✅ Successfully bumped version to 0.3.0!

Next steps:
1. Review the changes
2. Push to remote: git push && git push --tags
3. Create a release on GitHub
```

## Related Stories
- **Depends on**: US-7.1 (CLI initialization framework with Click and Rich)
- **Blocks**: Future release automation stories (US-7.4+)
- **Related**: US-7.2 (PyPI publishing could trigger on version tags)
