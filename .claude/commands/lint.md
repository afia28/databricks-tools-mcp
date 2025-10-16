---
description: Run linting and formatting using python-architect agent
allowed-tools: Task, TodoWrite
---

# Python Code Linting and Formatting

## 🔥 CRITICAL: MANDATORY DELEGATION

**ALL linting and formatting work MUST be delegated to the python-architect agent.**
- The main conversation is for coordination ONLY
- NO direct linting or formatting commands in main conversation
- The python-architect has expertise in code quality and style enforcement

## 🎯 Delegation to Python Architect

I will now delegate linting and formatting to the python-architect agent who will:
1. Run comprehensive linting checks
2. Apply automatic formatting
3. Fix code style issues
4. Ensure type safety
5. Report code quality metrics

```python
# Delegating to python-architect for linting and formatting
Task.invoke(
    subagent_type="python-architect",
    description="Perform linting and code formatting",
    prompt="""Perform comprehensive linting and code formatting for the project.

    LINTING AND FORMATTING TASKS:

    1. CODE FORMATTING (Auto-fix):
       ✓ Apply Black formatting to all Python files
         Command: uv run black src/ tests/
       ✓ Sort and organize imports with isort
         Command: uv run isort src/ tests/
       ✓ Ensure consistent line length (88 chars for Black)
       ✓ Fix whitespace and indentation issues

    2. STYLE CHECKING:
       ✓ Run Ruff for fast, comprehensive linting
         Command: uv run ruff check src/ tests/
       ✓ Auto-fix simple violations where possible
         Command: uv run ruff check --fix src/ tests/
       ✓ Report remaining style issues that need manual attention

    3. TYPE CHECKING:
       ✓ Run mypy for static type analysis
         Command: uv run mypy src/ --ignore-missing-imports
       ✓ Identify missing type hints
       ✓ Add obvious type annotations where possible
       ✓ Report complex type issues for review

    4. CODE QUALITY ANALYSIS:
       ✓ Check for code complexity issues
       ✓ Identify duplicate code patterns
       ✓ Find unused imports and variables
       ✓ Detect potential bugs and anti-patterns

    5. IMPORT ORGANIZATION:
       ✓ Group imports correctly (stdlib, third-party, local)
       ✓ Remove unused imports
       ✓ Sort alphabetically within groups
       ✓ Ensure absolute imports where appropriate

    6. DOCSTRING VALIDATION:
       ✓ Check for missing docstrings on public APIs
       ✓ Validate docstring format (Google style)
       ✓ Ensure Args, Returns, Raises sections present
       ✓ Add missing docstrings for obvious cases

    AUTO-FIX PRIORITY:
       1. Apply Black formatting (always safe)
       2. Sort imports with isort (always safe)
       3. Fix simple Ruff violations (safe auto-fixes only)
       4. Add obvious type hints (e.g., -> None for procedures)
       5. Update simple docstrings

    MANUAL FIX IDENTIFICATION:
       For issues that can't be auto-fixed, provide:
       - File path and line number
       - Clear description of the issue
       - Suggested fix with code example
       - Priority level (critical/high/medium/low)

    REPORT FORMAT:

       📊 LINTING SUMMARY:
       - Files checked: X
       - Issues found: Y
       - Issues auto-fixed: Z
       - Manual fixes needed: W

       ✅ AUTO-FIXED:
       - Black formatting applied to X files
       - Imports sorted in Y files
       - Ruff auto-fixes applied: [list specific fixes]
       - Type hints added: [list locations]

       ⚠️ MANUAL FIXES NEEDED:
       [For each issue]
       - File: path/to/file.py:line_number
       - Issue: Description
       - Suggested fix: Code example
       - Priority: Critical/High/Medium/Low

       📈 CODE QUALITY METRICS:
       - Cyclomatic complexity: X
       - Type hint coverage: Y%
       - Docstring coverage: Z%
       - Code duplication: N instances

       🎯 RECOMMENDATIONS:
       - Top 3 quality improvements to prioritize
       - Architectural suggestions if patterns detected
       - Performance optimizations if found

    CONFIGURATION COMPLIANCE:
       Ensure all changes comply with project configuration:
       - pyproject.toml settings for Black/isort
       - .ruff.toml or ruff section in pyproject.toml
       - mypy configuration if present

    IMPORTANT:
       - Apply ALL safe auto-fixes immediately
       - Never break existing functionality
       - Preserve code semantics exactly
       - Report before/after metrics
       - Focus on actionable improvements
    """
)
```

## Expected Outcomes

The python-architect will provide:

### Automatic Fixes Applied
- 🎨 Black formatting completed
- 📦 Imports organized and sorted
- 🔧 Simple style violations fixed
- 📝 Basic type hints added
- ✏️ Obvious docstrings added

### Manual Fixes Required
- 📍 Exact locations of issues
- 🔍 Clear problem descriptions
- 💡 Suggested solutions
- 🎯 Priority rankings

### Quality Metrics
- 📊 Before/after comparison
- 📈 Coverage percentages
- 🏆 Quality score
- 📋 Detailed reports

## Post-Linting Actions

Based on the architect's report:

1. **If All Auto-Fixes Applied**:
   - Review the changes
   - Confirm code still works
   - Run tests to verify
   - Commit formatted code

2. **If Manual Fixes Needed**:
   - Review priority issues
   - Address critical problems first
   - Re-run linting after fixes
   - Iterate until clean

3. **If Architectural Issues Found**:
   - Consider refactoring suggestions
   - Plan improvements
   - Create tasks for major changes

## Quality Standards

Linting is successful when:
- ✅ Black formatting applied
- ✅ Imports properly sorted
- ✅ No critical Ruff violations
- ✅ Type hints on public APIs
- ✅ Docstrings on public functions
- ✅ Complexity within limits
- ✅ No unused code

## Configuration Files Used

The python-architect will respect:

### pyproject.toml
- Black line length settings
- isort profile configuration
- Ruff rule selections
- Package dependencies

### .ruff.toml (if present)
- Specific rule configurations
- Ignore patterns
- Line length settings

### mypy.ini or setup.cfg (if present)
- Type checking strictness
- Import ignore patterns
- Plugin configurations

---
**Remember**: Always delegate to python-architect. Never run linting commands directly in the main conversation.
