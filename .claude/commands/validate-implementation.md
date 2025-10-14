---
description: Perform comprehensive validation using user-story-finalizer agent
allowed-tools: Task, TodoWrite
---

# Comprehensive Implementation Validation

## 🔥 CRITICAL: MANDATORY DELEGATION

**ALL validation work MUST be delegated to the user-story-finalizer agent.**
- The main conversation is for coordination ONLY
- NO direct validation, testing, or linting in main conversation
- The user-story-finalizer ensures all quality gates are met

## 🎯 Delegation to User Story Finalizer

I will now delegate comprehensive validation to the user-story-finalizer agent who will:
1. Run all quality checks
2. Fix any issues found automatically
3. Ensure production readiness
4. Report validation status

```python
# Delegating to user-story-finalizer for comprehensive validation
Task.invoke(
    subagent_type="user-story-finalizer",
    description="Validate implementation comprehensively",
    prompt="""Perform comprehensive validation of the implementation.

    VALIDATION CHECKLIST:

    1. CODE QUALITY VALIDATION:
       ✓ Type checking with mypy (uv run mypy src/ --ignore-missing-imports)
       ✓ Code formatting check (uv run black --check src/ tests/)
       ✓ Import sorting (uv run isort --check-only src/ tests/)
       ✓ Linting with ruff (uv run ruff check src/ tests/)

       If any issues found:
       - Apply black formatting automatically
       - Fix import sorting with isort
       - Address ruff violations
       - Fix type hints where possible

    2. TEST SUITE EXECUTION:
       ✓ Run complete test suite (uv run pytest tests/ -v --tb=short)
       ✓ Generate coverage report (uv run pytest tests/ --cov=src/ --cov-report=term-missing)
       ✓ Ensure coverage >85% threshold
       ✓ Check for slow tests (>1s execution)

       If tests fail:
       - Debug the failures
       - Fix the issues
       - Re-run to confirm resolution

    3. IMPORT AND INTEGRATION:
       ✓ Verify package imports work correctly
       ✓ Test all public API exports
       ✓ Validate configuration loading
       ✓ Check for circular imports

       Test with:
       ```python
       # Import main package and submodules
       import [package_name]
       from [package_name].core import *
       from [package_name].utils import *
       ```

    4. PERFORMANCE VALIDATION:
       ✓ Check for performance regressions
       ✓ Identify slow tests
       ✓ Memory usage analysis
       ✓ Optimization opportunities

    5. DOCUMENTATION CHECK:
       ✓ Ensure all public APIs have docstrings
       ✓ Check for missing type hints
       ✓ Validate README.md is current
       ✓ Verify CLAUDE.md reflects changes

    6. GIT STATUS REVIEW:
       ✓ Check for uncommitted changes
       ✓ Review modified files
       ✓ Ensure .gitignore is respected
       ✓ No sensitive data in commits

    AUTOMATIC FIXES:
    If issues are found, automatically:
    - Apply code formatting with black
    - Sort imports with isort
    - Fix simple ruff violations
    - Add missing type hints where obvious
    - Update docstrings for clarity

    VALIDATION REPORT:
    Provide a detailed report including:

    ✅ PASSED VALIDATIONS:
    - List all successful checks
    - Note coverage percentage
    - Highlight strengths

    ❌ FAILED VALIDATIONS:
    - List any failures that couldn't be auto-fixed
    - Provide specific remediation steps
    - Include error messages

    ⚠️ WARNINGS:
    - Note areas for improvement
    - Suggest optimizations
    - Highlight technical debt

    📊 METRICS:
    - Total tests: X
    - Coverage: X%
    - Execution time: Xs
    - Files modified: X

    COMMIT READINESS:
    Based on validation results, determine if code is ready to commit:
    - If YES: Generate commit message following conventional format
    - If NO: List specific blockers that must be resolved

    IMPORTANT:
    - Fix all auto-fixable issues immediately
    - Only report back issues that require manual intervention
    - Ensure zero tolerance for quality violations
    - Production readiness is the goal
    """
)
```

## Expected Outcomes

The user-story-finalizer will provide:

### Validation Results
- ✅ Complete validation status
- 🔧 Auto-fixed issues list
- ❌ Remaining issues (if any)
- 📊 Quality metrics

### Auto-Fix Actions
- 🎨 Code formatting applied
- 📦 Imports sorted
- 🔍 Type hints added
- 📝 Docstrings updated

### Production Readiness
- ✅ All quality gates passed
- 📋 Commit message generated
- 🚀 Ready for deployment
- 📊 Final metrics report

## Post-Validation Actions

Based on the finalizer's report:

1. **If All Validations Pass**:
   - Code is ready to commit
   - Use generated commit message
   - Proceed with git operations

2. **If Manual Fixes Needed**:
   - Address specific issues identified
   - Re-run validation after fixes
   - Iterate until all checks pass

3. **If Critical Issues Found**:
   - Stop and address blockers
   - Consult appropriate specialist agent
   - Ensure resolution before proceeding

## Quality Standards

Validation is successful when:
- ✅ All tests pass (100%)
- ✅ Coverage exceeds 85%
- ✅ Zero type checking errors
- ✅ Code is properly formatted
- ✅ Imports are organized
- ✅ No linting violations
- ✅ Documentation is complete

## Commit Message Format

If validation passes, the finalizer will generate:
```
type(scope): description

- Detailed change 1
- Detailed change 2
- Detailed change 3

Closes: [User Story or Issue]
```

---
**Remember**: Always delegate to user-story-finalizer. Never run validation commands directly in the main conversation.